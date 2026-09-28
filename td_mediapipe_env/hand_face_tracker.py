"""
Standalone hand + face tracker for the TouchDesigner face-filter project.

Runs outside TouchDesigner (TD's embedded Python can't import mediapipe cleanly).
Opens the webcam, runs MediaPipe Hands (to count extended fingers 0-5) and
MediaPipe FaceMesh w/ iris refinement (for a curated set of key landmarks),
and streams the results as JSON over UDP to TouchDesigner's UDP In DAT.

Run with: td_mediapipe_env/bin/python3 hand_face_tracker.py
"""
import cv2
import mediapipe as mp
import json
import os
import time

TRACKING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracking_data.json")
CAM_INDEX = 0

# Curated MediaPipe FaceMesh landmark indices we actually need for the 5 filters.
# (Face oval / silhouette, eyes + iris, eyebrows, nose, lips inner+outer.)
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397,
             365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58,
             132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
LEFT_EYE = [33, 133, 159, 145, 160, 144, 158, 153]
RIGHT_EYE = [362, 263, 386, 374, 387, 373, 385, 380]
LEFT_IRIS_CENTER = 468
RIGHT_IRIS_CENTER = 473
LEFT_EYEBROW = [70, 63, 105, 66, 107]
RIGHT_EYEBROW = [300, 293, 334, 296, 336]
NOSE = [1, 4, 168, 98, 327]
LIPS_OUTER = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 146, 91, 181, 84, 17, 314, 405, 321, 375]
LIPS_INNER = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 95, 88, 178, 87, 14, 317, 402, 318, 324]
CHEEKS = [50, 280]
TEMPLES = [127, 356]

KEY_INDICES = sorted(set(
    FACE_OVAL + LEFT_EYE + RIGHT_EYE + [LEFT_IRIS_CENTER, RIGHT_IRIS_CENTER] +
    LEFT_EYEBROW + RIGHT_EYEBROW + NOSE + LIPS_OUTER + LIPS_INNER + CHEEKS + TEMPLES
))

mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_mesh

FINGER_TIPS = [8, 12, 16, 20]
FINGER_PIPS = [6, 10, 14, 18]


def count_fingers(hand_landmarks):
    lm = hand_landmarks.landmark
    count = 0
    # thumb: extended if tip is farther from pinky-MCP than the thumb IP joint is
    # (orientation independent, works regardless of hand rotation)
    def dist(a, b):
        return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
    pinky_mcp = lm[17]
    if dist(lm[4], pinky_mcp) > dist(lm[3], pinky_mcp):
        count += 1
    for tip, pip in zip(FINGER_TIPS, FINGER_PIPS):
        if lm[tip].y < lm[pip].y:
            count += 1
    return count


def write_tracking(payload):
    tmp_path = TRACKING_FILE + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(payload, f)
    os.replace(tmp_path, TRACKING_FILE)


def main():
    cv2.setNumThreads(1)
    cap = cv2.VideoCapture(CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("ERROR: could not open webcam at index", CAM_INDEX)
        return

    print("Webcam opened. Writing tracking data to", TRACKING_FILE, flush=True)

    with mp_hands.Hands(static_image_mode=False, max_num_hands=1, model_complexity=0,
                         min_detection_confidence=0.6, min_tracking_confidence=0.5) as hands, \
         mp_face.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True,
                           min_detection_confidence=0.6, min_tracking_confidence=0.5) as face_mesh:

        frame_count = 0
        last_print = time.time()
        target_interval = 1.0 / 15.0  # cap at ~15fps to leave CPU headroom for TD

        while True:
            loop_start = time.time()
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.01)
                continue

            frame = cv2.flip(frame, 1)  # mirror, so it matches a flipped video feed in TD
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False

            hand_results = hands.process(rgb)
            face_results = face_mesh.process(rgb)

            payload = {
                "hand_detected": False,
                "finger_count": 0,
                "face_detected": False,
                "face": {}
            }

            if hand_results.multi_hand_landmarks:
                payload["hand_detected"] = True
                payload["finger_count"] = count_fingers(hand_results.multi_hand_landmarks[0])

            if face_results.multi_face_landmarks:
                payload["face_detected"] = True
                lm = face_results.multi_face_landmarks[0].landmark
                face_pts = {}
                for idx in KEY_INDICES:
                    p = lm[idx]
                    face_pts[f"p{idx}"] = [round(p.x, 5), round(p.y, 5)]
                payload["face"] = face_pts

            try:
                write_tracking(payload)
            except OSError:
                pass

            frame_count += 1
            if time.time() - last_print > 5:
                print(f"streaming... fingers={payload['finger_count']} "
                      f"hand={payload['hand_detected']} face={payload['face_detected']}", flush=True)
                last_print = time.time()

            elapsed = time.time() - loop_start
            if elapsed < target_interval:
                time.sleep(target_interval - elapsed)

    cap.release()


if __name__ == "__main__":
    main()
