import cv2
import numpy as np
import math
import random

FACE_CASCADE_PATH = '/Users/quinmartin/Desktop/Touchdesigner-Project/cascades/haarcascade_frontalface_default.xml'
EYE_CASCADE_PATH = '/Users/quinmartin/Desktop/Touchdesigner-Project/cascades/haarcascade_eye.xml'

face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
eye_cascade = cv2.CascadeClassifier(EYE_CASCADE_PATH)

DETECT_SCALE = 0.5
# Eyes only ever sit in the upper part of the face box; nostrils/mouth live below this,
# so capping the search here is what keeps the eye cascade off the nose.
EYE_REGION_HEIGHT_FRAC = 0.55


def onSetupParameters(scriptOp):
	return


def onPulse(par):
	return


def onCook(scriptOp):
	inp = scriptOp.inputs[0]
	if inp is None:
		scriptOp.copyNumpyArray(np.zeros((4, 4, 4), dtype='float32'))
		return

	arr = inp.numpyArray(delayed=False)
	if arr is None:
		return

	h, w = arr.shape[0], arr.shape[1]

	# TD gives float32 0-1 RGBA with row 0 at the bottom; flip + convert for cv2 (top-down, BGR uint8)
	img = (arr[..., :3] * 255).astype(np.uint8)
	img = np.flipud(img)
	bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
	gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

	small = cv2.resize(gray, (0, 0), fx=DETECT_SCALE, fy=DETECT_SCALE)
	faces = face_cascade.detectMultiScale(small, scaleFactor=1.2, minNeighbors=6, minSize=(40, 40))
	faces = [(int(fx / DETECT_SCALE), int(fy / DETECT_SCALE),
			  int(fw / DETECT_SCALE), int(fh / DETECT_SCALE)) for (fx, fy, fw, fh) in faces]

	beams = np.zeros_like(bgr)
	cx, cy = w / 2.0, h / 2.0
	t_now = absTime.seconds

	for (fx, fy, fw, fh) in faces:
		# Restrict the eye search to the upper part of the face box only.
		eye_region_h = max(1, int(fh * EYE_REGION_HEIGHT_FRAC))
		roi_gray = gray[fy:fy + eye_region_h, fx:fx + fw]
		if roi_gray.size == 0:
			continue
		# Haar cascade eye detector reliably fires on open eyes and drops out on closed ones,
		# so the beams naturally disappear on a blink instead of needing separate blink logic.
		eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.05, minNeighbors=10,
											 minSize=(max(1, int(fw * 0.14)), max(1, int(fh * 0.10))),
											 maxSize=(int(fw * 0.5), int(fh * 0.4)))

		# Keep at most one detection per face-half (left/right), the largest one, so a
		# stray nostril/nose-bridge hit can't sneak in alongside the real eyes.
		left_candidates = [e for e in eyes if (e[0] + e[2] / 2.0) < fw * 0.5]
		right_candidates = [e for e in eyes if (e[0] + e[2] / 2.0) >= fw * 0.5]
		chosen = []
		if left_candidates:
			chosen.append(max(left_candidates, key=lambda e: e[2] * e[3]))
		if right_candidates:
			chosen.append(max(right_candidates, key=lambda e: e[2] * e[3]))

		for eye_idx, (ex, ey, ew, eh) in enumerate(chosen):
			eye_cx = fx + ex + ew / 2.0
			eye_cy = fy + ey + eh / 2.0

			dx, dy = eye_cx - cx, eye_cy - cy
			dist = (dx ** 2 + dy ** 2) ** 0.5
			if dist < 1e-3:
				dx, dy = 0.0, -1.0
				dist = 1.0
			dx, dy = dx / dist, dy / dist
			base_angle = math.atan2(dy, dx)

			# Powerful-beam energy: a slow wobble + a faster crackle, unique per eye so
			# the two beams don't shake in lockstep, plus a flicker on brightness/width.
			seed = eye_idx * 97 + int(fx) + int(fy)
			wobble = (math.sin(t_now * 9.0 + seed) * 0.045
					  + math.sin(t_now * 23.0 + seed * 1.7) * 0.02)
			jitter = (random.random() - 0.5) * 0.03
			angle = base_angle + wobble + jitter
			dx, dy = math.cos(angle), math.sin(angle)

			t_candidates = []
			if dx > 0:
				t_candidates.append((w - eye_cx) / dx)
			if dx < 0:
				t_candidates.append((0 - eye_cx) / dx)
			if dy > 0:
				t_candidates.append((h - eye_cy) / dy)
			if dy < 0:
				t_candidates.append((0 - eye_cy) / dy)
			t = min([tc for tc in t_candidates if tc > 0], default=w)

			pulse = 0.5 + 0.5 * math.sin(t_now * 6.0 + seed)
			flicker = 0.85 + 0.15 * random.random()
			energy = pulse * flicker

			core_w = max(1, int(2 + 3 * energy))
			mid_w = max(2, int(5 + 6 * energy))
			outer_w = max(4, int(9 + 9 * energy))

			# small perpendicular shake at the origin for a crackling feel
			perp_x, perp_y = -dy, dx
			shake = (random.random() - 0.5) * 6.0
			start_x = int(eye_cx + perp_x * shake)
			start_y = int(eye_cy + perp_y * shake)

			pt1 = (start_x, start_y)
			pt2 = (int(eye_cx + dx * t), int(eye_cy + dy * t))

			outer_color = tuple(int(c * energy) for c in (0, 0, 255))
			mid_color = tuple(int(c * energy) for c in (40, 40, 255))
			core_color = tuple(int(c * (0.7 + 0.3 * energy)) for c in (255, 255, 255))

			cv2.line(beams, pt1, pt2, outer_color, outer_w, cv2.LINE_AA)
			cv2.line(beams, pt1, pt2, mid_color, mid_w, cv2.LINE_AA)
			cv2.line(beams, pt1, pt2, core_color, core_w, cv2.LINE_AA)
			cv2.circle(beams, (int(eye_cx), int(eye_cy)), int(5 + 4 * energy), core_color, -1, cv2.LINE_AA)

	glow = cv2.GaussianBlur(beams, (0, 0), sigmaX=10)
	composite = cv2.add(bgr, glow)
	composite = cv2.add(composite, beams)

	rgb = cv2.cvtColor(composite, cv2.COLOR_BGR2RGB)
	rgb = np.flipud(rgb)
	alpha = np.full((h, w, 1), 255, dtype=np.uint8)
	rgba = np.concatenate([rgb, alpha], axis=2).astype(np.float32) / 255.0

	scriptOp.copyNumpyArray(rgba)
