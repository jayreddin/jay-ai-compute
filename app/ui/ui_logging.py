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
    """
    Context manager to temporarily make a text widget editable and then read-only.
    
    :param text_widget: Tkinter text widget to manage
    """
    try:
        text_widget.configure(state='normal')
        yield text_widget
    finally:
        text_widget.configure(state='disabled')

class UILoggingMixin:
    """
    A mixin class providing advanced logging capabilities for UI components.
    """
    
    def resize_image_thumbnail(self, image: Image.Image, max_width: int = 300) -> Image.Image:
        """
        Resize an image to a thumbnail while maintaining aspect ratio.
        
        :param image: PIL Image to resize
        :param max_width: Maximum width for the thumbnail
        :return: Resized PIL Image
        """
        width_percent = (max_width / float(image.size[0]))
        height_size = int((float(image.size[1]) * float(width_percent)))
        return image.resize((max_width, height_size), Image.LANCZOS)
    
    def update_output_log(self, message: str, screenshot: Optional[Image.Image] = None) -> None:
        """
        Update the output log with a message and optional screenshot.
        
        :param message: Text message to display in the output log
        :param screenshot: Optional PIL Image object to display as a thumbnail
        """
        try:
            with text_widget_editable(self.output_log_text) as output_log:
                # Clear previous content if message is empty
                if not message and not screenshot:
                    output_log.delete('1.0', 'end')
                
                # Insert message
                if message:
                    output_log.insert('1.0', f"{message}\n")
                
                # Insert screenshot thumbnail if provided
                if screenshot:
                    try:
                        # Resize screenshot to a thumbnail
                        thumbnail = self.resize_image_thumbnail(screenshot)
                        
                        # Convert PIL Image to PhotoImage for Tkinter
                        photo = ImageTk.PhotoImage(thumbnail)
                        
                        # Insert the image into the text widget
                        output_log.image_create('1.0', image=photo)
                        # Keep a reference to prevent garbage collection
                        output_log.image = photo
                        
                        # Add a newline after the image
                        output_log.insert('1.0', '\n')
                    
                    except Exception as img_error:
                        logger.error(f"Failed to process screenshot: {img_error}")
                        output_log.insert('1.0', f"[ERROR] Failed to process screenshot\n")
                
                # Scroll to the top
                output_log.see('1.0')
        
        except Exception as e:
            logger.error(f"Error in update_output_log: {e}")
    
    def log_system_action(self, action_type: str, details: Union[Dict[str, Any], str, None] = None) -> None:
        """
        Log system actions and status messages to the Output Log
        
        :param action_type: Type of action being performed
        :param details: Optional details as dict, string, or None
        """
        def format_details(details):
            if isinstance(details, dict):
                # Convert dictionary to a readable string
                return ', '.join(f"{k}={v}" for k, v in details.items())
            elif isinstance(details, str):
                return details
            return ''

        def log_action():
            # Prepare the log message
            timestamp = datetime.now().strftime('%H:%M:%S')
            formatted_details = format_details(details)
            
            # Construct log entry
            if formatted_details:
                log_entry = f"[{timestamp}] {action_type}: {formatted_details}\n"
            else:
                log_entry = f"[{timestamp}] {action_type}\n"
            
            # Thread-safe log update using context manager
            try:
                with text_widget_editable(self.output_log_text) as output_log:
                    output_log.insert('1.0', log_entry)
                    output_log.see('1.0')
            except Exception as e:
                logger.error(f"Logging error: {e}")

        # Ensure thread-safe execution
        if threading.current_thread() is threading.main_thread():
            log_action()
        else:
            self.output_log_text.after(0, log_action)
    
    def display_screenshot_in_output_log(self) -> None:
        """
        Capture and display the current screenshot in the Output Log.
        
        This method uses the Screen utility to capture a screenshot and then
        displays it in the output log text widget.
        
        Handles potential import and screenshot capture errors gracefully.
        """
        try:
            from utils.screen import Screen
        except ImportError:
            self.update_output_log("Error: Screen utility not available")
            return

        try:
            # Capture screenshot with error handling for screenshot capture
            screenshot = Screen().get_screenshot()
            
            if screenshot is None:
                self.update_output_log("No screenshot could be captured")
                return
            
            # Display screenshot in output log with a descriptive message
            self.update_output_log("Screenshot captured:", screenshot)

        except Exception as e:
            # Log any errors that occur during screenshot capture or display
            error_details = f"Unexpected error capturing screenshot: {str(e)}\n{traceback.format_exc()}"
            self.update_output_log(error_details)
    
    def mock_system_action(self, action_name: str, *args, **kwargs) -> None:
        """
        Generic mock method for system actions with flexible logging
        
        :param action_name: Name of the action being performed
        :param args: Positional arguments
        :param kwargs: Keyword arguments
        """
        # Combine args and kwargs for logging
        details = {}
        if args:
            details['args'] = args
        if kwargs:
            details.update(kwargs)
        
        # Log the action
        self.log_system_action(action_name, details)

    # Specific mock methods for common actions
    def mock_pyautogui_write(self, text: str, interval: float = 0.05) -> None:
        """Mock pyautogui.write with logging"""
        self.mock_system_action('pyautogui.write', text=text, interval=interval)

    def mock_pyautogui_press(self, keys: str) -> None:
        """Mock pyautogui.press with logging"""
        self.mock_system_action('pyautogui.press', keys=keys)