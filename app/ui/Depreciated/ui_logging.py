import os
import sys
import logging
import threading
from datetime import datetime
from typing import Union, Optional, Dict, Any

import ttkbootstrap as ttk
from PIL import Image, ImageTk
from contextlib import contextmanager

import traceback

logger = logging.getLogger(__name__)

@contextmanager
def text_widget_editable(text_widget):
    """Context manager to temporarily make a text widget editable"""
    try:
        text_widget.configure(state='normal')
        yield text_widget
    finally:
        text_widget.configure(state='disabled')

class UILoggingMixin:
    """Mixin class providing advanced logging capabilities"""
    
    def resize_image_thumbnail(self, image: Image.Image, max_width: int = 300) -> Image.Image:
        """Resize image to thumbnail maintaining aspect ratio"""
        width_percent = (max_width / float(image.size[0]))
        height_size = int((float(image.size[1]) * float(width_percent)))
        return image.resize((max_width, height_size), Image.LANCZOS)
    
    def update_output_log(self, message: str, screenshot: Optional[Image.Image] = None) -> None:
        """Update output log with message and optional screenshot"""
        try:
            with text_widget_editable(self.output_log_text) as output_log:
                if not message and not screenshot:
                    output_log.delete('1.0', 'end')
                
                if message:
                    output_log.insert('1.0', f"{message}\n")
                
                if screenshot:
                    try:
                        thumbnail = self.resize_image_thumbnail(screenshot)
                        photo = ImageTk.PhotoImage(thumbnail)
                        output_log.image_create('1.0', image=photo)
                        output_log.image = photo
                        output_log.insert('1.0', '\n')
                    except Exception as img_error:
                        logger.error(f"Failed to process screenshot: {img_error}")
                        output_log.insert('1.0', "[ERROR] Failed to process screenshot\n")
                
                output_log.see('1.0')
        except Exception as e:
            logger.error(f"Error in update_output_log: {e}")

    def log_system_action(self, action_type: str, details: Union[Dict[str, Any], str, None] = None) -> None:
        """Log system actions with thread safety"""
        def format_details(details):
            if isinstance(details, dict):
                return ', '.join(f"{k}={v}" for k, v in details.items())
            return str(details) if details else ''

        def log_action():
            try:
                timestamp = datetime.now().strftime('%H:%M:%S')
                formatted_details = format_details(details)
                log_entry = f"[{timestamp}] {action_type}: {formatted_details}\n" if formatted_details else f"[{timestamp}] {action_type}\n"
                
                with text_widget_editable(self.output_log_text) as output_log:
                    output_log.insert('1.0', log_entry)
                    output_log.see('1.0')
            except Exception as e:
                logger.error(f"Logging error: {e}")

        if threading.current_thread() is threading.main_thread():
            log_action()
        else:
            self.output_log_text.after(0, log_action)

    def display_screenshot_in_output_log(self) -> None:
        """Capture and display screenshot in output log"""
        try:
            from utils.screen import Screen
            screenshot = Screen().get_screenshot()
            
            if screenshot:
                self.update_output_log("Screenshot captured:", screenshot)
            else:
                self.update_output_log("No screenshot could be captured")
        except ImportError:
            self.update_output_log("Error: Screen utility not available")
        except Exception as e:
            error_details = f"Unexpected error capturing screenshot: {str(e)}\n{traceback.format_exc()}"
            self.update_output_log(error_details)
