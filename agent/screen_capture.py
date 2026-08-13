from io import BytesIO

import mss
from PIL import Image


class ScreenCapture:
    """
    Captures the screen and returns the image
    as an in-memory PNG buffer.

    No screenshot file is saved locally.
    """

    def capture_png(self) -> BytesIO:
        """
        Capture the complete virtual desktop.

        Returns:
            BytesIO:
                PNG image stored in memory.
        """

        with mss.mss() as screen:

            # Capture the complete virtual screen.
            # Monitor 0 represents all monitors.
            screenshot = screen.grab(
                screen.monitors[0]
            )

            # Convert MSS screenshot
            # into a Pillow image.
            image = Image.frombytes(
                "RGB",
                screenshot.size,
                screenshot.rgb,
            )

            # Store the image in memory.
            image_buffer = BytesIO()

            image.save(
                image_buffer,
                format="PNG",
            )

            image_buffer.seek(0)

            return image_buffer