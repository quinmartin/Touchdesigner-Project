"""
Standalone arm/pose tracker for the "Wave the Wheat" TouchDesigner project.

Runs outside TouchDesigner (TD's embedded Python can't import mediapipe cleanly).
Reads the (already mirrored) camera frame that TD saves to td_frame.jpg, runs
MediaPipe Pose, and writes the user's arm angles to pose_data.json, which TD
reads every frame to drive the stick figures. Getting frames from TD means this
script never opens the camera itself, so it needs no macOS camera permission.
Pass --camera to open the webcam directly instead.

Arms are reported per *screen side* (after mirroring), so "left" means the arm
the user sees on the left of the screen. Angles are in degrees measured from
straight up, positive = rotated toward screen-left. An arm is only "up" when its
wrist is above its shoulder.

It also writes td_mask.png, a grayscale person mask (white = user) the same size
as the frame, so TD can cut the user out of their background. The mask is all
black when nobody is detected.

Run with: td_mediapipe_env/bin/python3 pose_tracker.py [--camera]
"""
import cv2
import mediapipe as mp
import numpy as np
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TRACKING_FILE = os.path.join(HERE, "pose_data.json")
FRAME_FILE = os.path.join(HERE, "td_frame.jpg")
MASK_FILE = os.path.join(HERE, "td_mask.png")
FRAME_STALE_SECONDS = 1.0
CAM_INDEX = 0
MIN_VISIBILITY = 0.5

# MediaPipe Pose landmark indices: (shoulder, elbow, wrist)
ARM_A = (11, 13, 15)
ARM_B = (12, 14, 16)

mp_pose = mp.solutions.pose


def angle_from_up(a, b):
    """Angle of the vector a->b in degrees from straight up (image y points down).
    Positive rotates toward screen-left."""
    dx = b.x - a.x
    dy = b.y - a.y
    return math.degrees(math.atan2(-dx, -dy))


def arm_data(lm, idx):
    s, e, w = (lm[i] for i in idx)
    visible = min(s.visibility, e.visibility, w.visibility) >= MIN_VISIBILITY
    return {
        "shoulder_x": s.x,
        "visible": visible,
        "up": visible and w.y < s.y,
        "upper": round(angle_from_up(s, e), 2),
        "fore": round(angle_from_up(e, w), 2),
    }


def write_tracking(payload):
    tmp_path = TRACKING_FILE + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(payload, f)
    os.replace(tmp_path, TRACKING_FILE)


def write_mask(mask):
    tmp_path = MASK_FILE + ".tmp.png"
    cv2.imwrite(tmp_path, mask)
    os.replace(tmp_path, MASK_FILE)


class CameraSource:
    def __init__(self):
        self.cap = cv2.VideoCapture(CAM_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.ok = self.cap.isOpened()

    def read(self):
        ok, frame = self.cap.read()
        return cv2.flip(frame, 1) if ok else None  # mirror to match TD's flipped feed

    def release(self):
        self.cap.release()


class TDFrameSource:
    """Reads the mirrored frame TD saves each frame; returns None if it's stale."""
    ok = True

    def __init__(self):
        self.last_mtime = 0

    def read(self):
        try:
            mtime = os.path.getmtime(FRAME_FILE)
        except OSError:
            return None
        if mtime == self.last_mtime or time.time() - mtime > FRAME_STALE_SECONDS:
            return None
        self.last_mtime = mtime
        return cv2.imread(FRAME_FILE)  # None if caught mid-write

    def release(self):
        pass


def main():
    cv2.setNumThreads(1)
    use_camera = "--camera" in sys.argv
    source = CameraSource() if use_camera else TDFrameSource()

    if not source.ok:
        print("ERROR: could not open webcam at index", CAM_INDEX)
        return

    print("Reading frames from", "webcam" if use_camera else FRAME_FILE,
          "- writing pose data to", TRACKING_FILE, flush=True)

    with mp_pose.Pose(static_image_mode=False, model_complexity=0, smooth_landmarks=True,
                      enable_segmentation=True, smooth_segmentation=True,
                      min_detection_confidence=0.6, min_tracking_confidence=0.5) as pose:

        last_print = time.time()
        target_interval = 1.0 / 20.0  # cap at ~20fps to leave CPU headroom for TD

        while True:
            loop_start = time.time()
            frame = source.read()
            if frame is None:
                time.sleep(0.01)
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = pose.process(rgb)

            payload = {"detected": False, "left": None, "right": None}

            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                arms = sorted([arm_data(lm, ARM_A), arm_data(lm, ARM_B)],
                              key=lambda a: a["shoulder_x"])
                payload = {"detected": True, "left": arms[0], "right": arms[1]}

            if results.pose_landmarks and results.segmentation_mask is not None:
                mask = (np.clip(results.segmentation_mask, 0.0, 1.0) * 255).astype(np.uint8)
            else:
                mask = np.zeros(frame.shape[:2], np.uint8)

            try:
                write_tracking(payload)
                write_mask(mask)
            except OSError:
                pass

            if time.time() - last_print > 5:
                if payload["detected"]:
                    l, r = payload["left"], payload["right"]
                    print(f"streaming... L up={l['up']} upper={l['upper']:.0f} | "
                          f"R up={r['up']} upper={r['upper']:.0f}", flush=True)
                else:
                    print("streaming... no person", flush=True)
                last_print = time.time()

            elapsed = time.time() - loop_start
            if elapsed < target_interval:
                time.sleep(target_interval - elapsed)

    source.release()


if __name__ == "__main__":
    main()
