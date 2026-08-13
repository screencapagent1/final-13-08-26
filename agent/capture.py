from importlib import import_module
from io import BytesIO
import struct
import zlib
from typing import Any


def _load_mss() -> Any:
    """Load the screen-capture backend when it is needed."""
    return import_module("mss")


def _encode_png(rgb: bytes, width: int, height: int) -> bytes:
    """Encode RGB pixel data as a PNG without an external imaging package."""
    scanlines = b"".join(
        b"\x00" + rgb[row * width * 3 : (row + 1) * width * 3]
        for row in range(height)
    )

    def chunk(kind: bytes, data: bytes) -> bytes:
        payload = kind + data
        return (
            struct.pack(">I", len(data))
            + payload
            + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(scanlines))
        + chunk(b"IEND", b"")
    )


class ScreenCapture:
    """
    Handles screen capture operations.

    Screenshots are captured and converted into an in-memory
    PNG buffer. No screenshot file is saved locally.
    """

    def capture_png(self) -> BytesIO:
        """
        Capture the complete virtual desktop.

        Returns:
            BytesIO: PNG image stored in memory.
        """

        with _load_mss().mss() as screen:
            # Monitor 0 represents the entire virtual desktop.
            monitor = screen.monitors[0]

            screenshot = screen.grab(monitor)

            image_buffer = BytesIO()
            image_buffer.write(
                _encode_png(
                    screenshot.rgb,
                    screenshot.size[0],
                    screenshot.size[1],
                )
            )

            image_buffer.seek(0)

            return image_buffer