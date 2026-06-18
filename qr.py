"""QR code generation and scanning helpers."""

from __future__ import annotations

import os

from utils import QR_CODES_DIR, relative_qr_path, resolve_project_path


def _load_qr_modules():
    """Import QR-related libraries only when needed."""
    missing: list[str] = []

    try:
        import qrcode  # type: ignore
    except ModuleNotFoundError:
        qrcode = None
        missing.append("qrcode")

    try:
        import cv2  # type: ignore
    except ModuleNotFoundError:
        cv2 = None
        missing.append("opencv-python")

    try:
        import numpy as np  # type: ignore
    except ModuleNotFoundError:
        np = None
        missing.append("numpy")

    if missing:
        raise RuntimeError(
            "Missing QR dependencies: "
            + ", ".join(missing)
            + ". Install them with: pip install qrcode opencv-python numpy"
        )

    return qrcode, cv2, np


def _ensure_pillow_available() -> None:
    """Ensure Pillow is available for QR image creation."""
    try:
        from PIL import Image  # type: ignore  # noqa: F401
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Missing QR image dependency: Pillow. Install it with: pip install Pillow"
        ) from error


def generate_qr_code(product_id: str) -> str:
    """Generate and save a QR code containing the product id."""
    qrcode, _, _ = _load_qr_modules()
    _ensure_pillow_available()
    os.makedirs(QR_CODES_DIR, exist_ok=True)

    try:
        qr_image = qrcode.make(product_id)
    except ModuleNotFoundError as error:
        if error.name == "PIL":
            raise RuntimeError(
                "Missing QR image dependency: Pillow. Install it with: pip install Pillow"
            ) from error
        raise
    relative_path = relative_qr_path(product_id)
    absolute_path = resolve_project_path(relative_path)
    qr_image.save(absolute_path)
    return relative_path


def scan_qr_webcam(camera_index: int = 0) -> str:
    """Scan a QR code live from the webcam and return the decoded product id."""
    _, cv2, np = _load_qr_modules()

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError("Unable to access webcam. Check the camera connection and permissions.")

    detector = cv2.QRCodeDetector()
    window_name = "QR Scanner"

    try:
        while True:
            success, frame = cap.read()
            if not success:
                raise RuntimeError("Unable to read frames from the webcam.")

            frame = np.array(frame)
            decoded_value, points, _ = detector.detectAndDecode(frame)

            if points is not None:
                points = points.astype(int).reshape(-1, 2)
                for index in range(len(points)):
                    start = tuple(points[index])
                    end = tuple(points[(index + 1) % len(points)])
                    cv2.line(frame, start, end, (0, 255, 0), 2)

            instruction = "Show QR to camera | Press Q to cancel"
            cv2.putText(
                frame,
                instruction,
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            if decoded_value:
                cv2.putText(
                    frame,
                    f"Scanned: {decoded_value}",
                    (20, 65),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow(window_name, frame)
                cv2.waitKey(800)
                return decoded_value.strip()

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in {ord("q"), ord("Q"), 27}:
                raise RuntimeError("Webcam QR scan cancelled.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
