import base64
import io
import os
import tempfile
import logging
from PIL import Image, ImageDraw

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except Exception as e:
    logging.warning(f"Could not import pyautogui: {e}")
    logging.warning("Running in headless mode. Screen capture features will be disabled.")
    PYAUTOGUI_AVAILABLE = False
    pyautogui = None

from utils.settings import Settings


class Screen:
    def get_size(self) -> tuple[int, int]:
        if not PYAUTOGUI_AVAILABLE:
            logging.warning("Screen size detection not available in headless mode.")
            return (0, 0)
        screen_width, screen_height = pyautogui.size()  # Get the size of the primary monitor.
        return screen_width, screen_height

    def get_screenshot(self) -> Image.Image:
        if not PYAUTOGUI_AVAILABLE:
            logging.warning("Screenshot capture not available in headless mode. Generating a placeholder image.")
            # Create a more informative placeholder image
            img = Image.new('RGB', (800, 600), color='lightgray')
            draw = ImageDraw.Draw(img)
            draw.text((50, 250), "Screenshot Unavailable in Headless Mode", fill='black')
            return img

        # Enable screen recording from settings
        img = pyautogui.screenshot()  # Takes roughly 100ms
        return img

    def get_screenshot_in_base64(self) -> str:
        # Base64 images work with ChatCompletions API but not Assistants API
        img_bytes = self.get_screenshot_as_file_object()
        encoded_image = base64.b64encode(img_bytes.read()).decode('utf-8')
        return encoded_image

    def get_screenshot_as_file_object(self):
        # In memory files don't work with OpenAI Assistants API because of missing filename attribute
        img_bytes = io.BytesIO()
        img = self.get_screenshot()
        img.save(img_bytes, format='PNG')  # Save the screenshot to an in-memory file.
        img_bytes.seek(0)
        return img_bytes

    def get_temp_filename_for_current_screenshot(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
            screenshot = self.get_screenshot()
            screenshot.save(tmpfile.name)
            return tmpfile.name

    def get_screenshot_file(self):
        # Gonna always keep a screenshot.png in ~/.open-interface/ because file objects, temp files, every other way has an error
        filename = 'screenshot.png'
        filepath = os.path.join(Settings().get_settings_directory_path(), filename)
        img = self.get_screenshot()
        img.save(filepath)
        return filepath
