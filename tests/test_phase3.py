"""Dependency-light checks for Phase 3 multi-face helpers."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np
from multi_face_tracker import _mouth_patch, sample_active_face_track


def test_mouth_patch_returns_normalized_region():
    frame = np.zeros((120, 100), dtype=np.uint8)
    patch = _mouth_patch(frame, (20, 10, 50, 60))
    assert patch is not None
    assert patch.shape == (20, 40)


def test_multi_face_tracker_handles_video_without_detectable_faces(tmp_path):
    path = str(tmp_path / "blank.mp4")
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 5.0, (160, 120))
    assert writer.isOpened()
    for _ in range(5):
        writer.write(np.zeros((120, 160, 3), dtype=np.uint8))
    writer.release()
    samples, info = sample_active_face_track(path, 0, 0.8, sample_interval=0.4)
    assert isinstance(samples, list)
    assert info["confidence"] in {"low", "medium", "high"}
    assert "faces_seen" in info


if __name__ == "__main__":
    test_mouth_patch_returns_normalized_region()
    print("Phase 3 helper tests passed.")
