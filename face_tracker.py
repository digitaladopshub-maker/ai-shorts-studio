"""Lightweight, free CPU face tracking helpers for Streamlit Community Cloud.

Uses OpenCV's bundled Haar cascade at sampled timestamps, associates detections
between samples, smooths the centre path and builds an FFmpeg time expression.
This is single-subject framing, not active-speaker recognition.
"""
from __future__ import annotations

import os
import cv2


def _load_cascade():
    path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    cascade = cv2.CascadeClassifier(path)
    return None if cascade.empty() else cascade


def sample_face_track(video_path: str, start_sec: float, duration_sec: float,
                      sample_interval: float = 0.75, max_width: int = 480):
    """Return smoothed (time, cx, cy) samples in source-video pixels."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if width <= 0 or height <= 0:
        cap.release()
        return []
    cascade = _load_cascade()
    if cascade is None:
        cap.release()
        return []

    scale = min(1.0, float(max_width) / float(width))
    samples = []
    previous = None
    t = 0.0
    while t <= max(0.0, duration_sec):
        cap.set(cv2.CAP_PROP_POS_MSEC, (start_sec + t) * 1000.0)
        ok, frame = cap.read()
        if not ok or frame is None:
            t += sample_interval
            continue
        if scale < 1.0:
            frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=5,
                                         minSize=(max(24, int(28 * scale)), max(24, int(28 * scale))))
        chosen = None
        if len(faces):
            candidates = []
            for x, y, w, h in faces:
                cx = (x + w / 2.0) / scale
                cy = (y + h / 2.0) / scale
                area = float(w * h)
                # Prefer the previous subject while still preferring a reasonably large face.
                distance = 0.0 if previous is None else ((cx - previous[0]) ** 2 + (cy - previous[1]) ** 2) ** 0.5
                candidates.append((area / (1.0 + distance / max(width, height)), cx, cy))
            _, cx, cy = max(candidates, key=lambda item: item[0])
            chosen = (cx, cy)
        if chosen is not None:
            if previous is not None:
                # Exponential smoothing reduces crop jitter between detections.
                chosen = (0.68 * previous[0] + 0.32 * chosen[0],
                          0.68 * previous[1] + 0.32 * chosen[1])
            previous = chosen
            samples.append((round(t, 3), float(chosen[0]), float(chosen[1])))
        elif previous is not None:
            # Hold last reliable location briefly across missed detections.
            samples.append((round(t, 3), float(previous[0]), float(previous[1])))
        t += sample_interval
    cap.release()
    if samples and samples[0][0] > 0:
        first = samples[0]
        samples.insert(0, (0.0, first[1], first[2]))
    return _smooth_samples(samples)


def _smooth_samples(samples):
    if len(samples) < 3:
        return samples
    result = []
    for i, (t, x, y) in enumerate(samples):
        window = samples[max(0, i - 1):min(len(samples), i + 2)]
        result.append((t, sum(p[1] for p in window) / len(window),
                       sum(p[2] for p in window) / len(window)))
    return result


def _piecewise_expression(samples, value_index: int, fallback: str):
    if not samples:
        return fallback
    if len(samples) == 1:
        return f"{samples[0][value_index]:.2f}"
    expr = f"{samples[-1][value_index]:.2f}"
    for i in range(len(samples) - 2, -1, -1):
        t0, v0 = samples[i][0], samples[i][value_index]
        t1, v1 = samples[i + 1][0], samples[i + 1][value_index]
        if t1 <= t0:
            continue
        interpolated = f"({v0:.2f}+({v1-v0:.2f})*(t-{t0:.3f})/{(t1-t0):.3f})"
        expr = f"if(lt(t\\,{t1:.3f})\\,{interpolated}\\,{expr})"
    return expr


def build_crop_expressions(samples, crop_width: str, crop_height: str,
                           frame_width: int, frame_height: int,
                           fallback_x: str = "(iw-ow)/2",
                           fallback_y: str = "(ih-oh)/2"):
    """Build smooth, clamped crop x/y expressions using FFmpeg's local clip time."""
    if not samples:
        return fallback_x, fallback_y
    # Keep the face slightly above the vertical centre to leave room for captions.
    cx_expr = _piecewise_expression(samples, 1, str(frame_width / 2.0))
    cy_expr = _piecewise_expression(samples, 2, str(frame_height * 0.42))
    x = f"clip(({cx_expr})-({crop_width})/2\\,0\\,iw-({crop_width}))"
    y = f"clip(({cy_expr})-({crop_height})*0.42\\,0\\,ih-({crop_height}))"
    return x, y
