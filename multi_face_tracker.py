"""Lightweight multi-face tracking and visible speaking-activity estimation.

Uses OpenCV Haar cascades and mouth-region frame-difference activity. This is a visual
activity heuristic, not audio/lip-sync speaker identification. When confidence
is weak, callers should fall back to the continuity-based face tracker.
"""
from __future__ import annotations

import math
import cv2
import numpy as np


def _cascade():
    path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(path)
    return None if detector.empty() else detector


def _mouth_patch(gray, box):
    x, y, w, h = box
    # Lower central face region, resized to make movement scoring comparable.
    x1 = max(0, x + int(w * 0.18))
    x2 = min(gray.shape[1], x + int(w * 0.82))
    y1 = max(0, y + int(h * 0.58))
    y2 = min(gray.shape[0], y + int(h * 0.92))
    patch = gray[y1:y2, x1:x2]
    if patch.size == 0:
        return None
    return cv2.resize(patch, (40, 20), interpolation=cv2.INTER_AREA)


def sample_active_face_track(video_path: str, start_sec: float, duration_sec: float,
                             sample_interval: float = 0.65, max_width: int = 480):
    """Return (selected_track_samples, diagnostics) for the likely speaking face.

    Samples are (local_time, source_x, source_y). Diagnostics deliberately call
    this a visual activity estimate; it cannot prove who is speaking.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return [], {"faces_seen": 0, "confidence": "low", "method": "fallback"}
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if width <= 0 or height <= 0:
        cap.release()
        return [], {"faces_seen": 0, "confidence": "low", "method": "fallback"}
    detector = _cascade()
    if detector is None:
        cap.release()
        return [], {"faces_seen": 0, "confidence": "low", "method": "fallback"}

    scale = min(1.0, float(max_width) / float(width))
    tracks = {}
    next_id = 0
    previous_patches = {}
    t = 0.0
    while t <= max(0.0, duration_sec) + 0.001:
        cap.set(cv2.CAP_PROP_POS_MSEC, (start_sec + t) * 1000.0)
        ok, frame = cap.read()
        if not ok or frame is None:
            t += sample_interval
            continue
        if scale < 1.0:
            frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detections = detector.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=5,
                                               minSize=(max(24, int(28 * scale)),) * 2)
        current_ids = set()
        assigned = []
        for x, y, w, h in detections:
            cx, cy = (x + w / 2.0) / scale, (y + h / 2.0) / scale
            box = (int(x), int(y), int(w), int(h))
            choices = []
            for tid, track in tracks.items():
                if tid in current_ids or not track["samples"]:
                    continue
                px, py = track["samples"][-1][1:]
                dist = math.hypot(cx - px, cy - py) / max(width, height)
                if dist < 0.22:
                    choices.append((dist, tid))
            if choices:
                tid = min(choices)[1]
            else:
                tid = next_id
                next_id += 1
                tracks[tid] = {"samples": [], "motion": [], "areas": []}
            current_ids.add(tid)
            patch = _mouth_patch(gray, box)
            motion = 0.0
            if patch is not None and tid in previous_patches:
                motion = float(np.mean(cv2.absdiff(patch, previous_patches[tid]))) / 255.0
            if patch is not None:
                previous_patches[tid] = patch
            tracks[tid]["samples"].append((round(t, 3), float(cx), float(cy)))
            tracks[tid]["motion"].append(motion)
            tracks[tid]["areas"].append(float(w * h))
            assigned.append(tid)
        # Discard stale patch references for faces not currently visible.
        previous_patches = {tid: patch for tid, patch in previous_patches.items() if tid in current_ids}
        t += sample_interval
    cap.release()

    valid = [(tid, data) for tid, data in tracks.items() if len(data["samples"]) >= 2]
    if not valid:
        return [], {"faces_seen": len(tracks), "confidence": "low", "method": "continuity fallback"}
    ranked = []
    for tid, data in valid:
        motion = data["motion"]
        # Average temporal mouth-region change, gently normalized for face size.
        activity = sum(motion[1:]) / max(1, len(motion) - 1)
        ranked.append((activity, tid, data))
    ranked.sort(key=lambda item: item[0], reverse=True)
    best_activity, best_id, best_data = ranked[0]
    second_activity = ranked[1][0] if len(ranked) > 1 else 0.0
    margin = best_activity - second_activity
    confidence = "high" if best_activity > 0.045 and margin > 0.012 else (
        "medium" if best_activity > 0.025 and margin > 0.006 else "low")
    samples = best_data["samples"]
    # If visual activity is ambiguous, use the longest/most stable face track.
    if confidence == "low":
        best_data = max((item[1] for item in valid), key=lambda d: len(d["samples"]))
        samples = best_data["samples"]
        method = "continuity fallback (speaker ambiguous)"
    else:
        method = "visible mouth-motion estimate"
    return samples, {
        "faces_seen": len(tracks),
        "confidence": confidence,
        "method": method,
        "tracked_samples": len(samples),
    }
