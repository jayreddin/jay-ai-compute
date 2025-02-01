import os
import sys
import threading
import logging
import re
from datetime import datetime
from typing import Union, Optional, Dict, Any
from multiprocessing import Queue
import importlib.util

import ttkbootstrap as ttk
from PIL import Image, ImageTk

from ui.logging_mixin import UILoggingMixin
from utils.settings import Settings
from ui.ui_utils import text_widget_editable
from version import version

logger = logging.getLogger(__name__)


class MainWindow(ttk.Window, UILoggingMixin):
    def change_theme(self, theme_name: str) -> None:
        self.style.theme_use(theme_name)

    def __init__(self):
        settings = Settings()
        settings_dict = settings.get_dict()
        theme = settings_dict.get('theme', 'superhero')

        try:
            super().__init__(themename=theme)
        except:
            super().__init__()  # https://github.com/AmberSahdev/Open-Interface/issues/35

        self.title('J AI Compute')

        # Set precise window dimensions
        window_width = 370  # Reduced to 300
        window_height = 820  # Set to 700

        # Set window size and minimum size
        self.geometry(f'{window_width}x{window_height}')
        self.minsize(window_width, window_height)

        # Ensure window doesn't expand unnecessarily
        self.grid_propagate(False)  # Prevent automatic resizing

        # Configure grid to be responsive
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)  # Reduce weight for second column
        self.grid_rowconfigure(0, weight=0)  # Heading row

        # Create main frame with controlled expansion
        frame = ttk.Frame(self)
        frame.grid(
            row=0,
            column=0,
            columnspan=2,  # Span both columns
            sticky='nsew',
            padx=10,
            pady=10
        )

        # Carefully control frame's column and row configurations
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=0)  # Minimal weight for second column
        frame.grid_rowconfigure(5, weight=1)  # Give weight to Output Log row

        # MP Queue to facilitate communication between UI and Core.
        # Put user requests received from UI text box into this queue which will then be dequeued in App to be sent
        # to core.
        self.user_request_queue = Queue()

        # Heading with centered text
        heading_label = ttk.Label(
            frame,
            text='Ask AI To Control Your Desktop',
            font=('Helvetica', 12, 'bold'),
            anchor='center'
        )
        heading_label.grid(
            column=0,
            row=1,
            columnspan=2,  # Span both columns
            sticky='ew',  # Expand horizontally
            pady=(0, 10)  # Add some padding below
        )

        # Input Command Frame - card-like border
        self.input_command_frame = ttk.LabelFrame(
            frame,
            text='Input Command Below:',
            bootstyle='primary'
        )
        self.input_command_frame.grid(
            row=3,
            column=0,
            columnspan=2,
            padx=10,
            pady=10,
            sticky='ew'
        )
        frame.grid_rowconfigure(3, weight=0)

        # Input Text Box - dynamically resizable
        self.input_text = ttk.Text(
            self.input_command_frame,
            height=2,  # Start with 2 rows
            wrap=ttk.WORD,
            font=('Arial', 16)  # Increased font size
        )
        self.input_text.grid(
            row=0,
            column=0,
            padx=10,
            pady=10,
            sticky='ew'
        )
        self.input_command_frame.grid_columnconfigure(0, weight=1)

        # Prevent newline on Enter key
        def prevent_newline(event):
            # Trigger submit instead of adding a newline
            self.execute_user_request()
            return 'break'  # Completely stop the default Enter key behavior

        # Bind Enter key to submit without newline
        self.input_text.bind('<Return>', prevent_newline)
        self.input_text.bind('<KP_Enter>', prevent_newline)
        self.input_text.bind('<Shift-Return>', lambda event: None)  # Allow Shift+Enter for actual newline if needed

        # Dynamic text box resizing
        def on_input_change(event):
            # Adjust text box height based on content
            lines = self.input_text.get('1.0', 'end-1c').count('\n') + 1
            current_height = self.input_text.winfo_height()
            self.input_text.configure(height=min(max(2, lines), 10))  # Limit max height to 10 rows

        self.input_text.bind('<KeyRelease>', on_input_change)

        # Submit Button - make responsive
        self.submit_button = ttk.Button(
            frame,
            text='Submit',
            command=self.execute_user_request,
            bootstyle='success'
        )
        self.submit_button.grid(
            row=4,
            column=0,
            padx=(10, 5),
            pady=(5, 10),
            sticky='ew'
        )

        # Stop Button - make responsive
        self.stop_button = ttk.Button(
            frame,
            text='Cancel',
            bootstyle="danger",
            command=self.stop_previous_request
        )
        self.stop_button.grid(
            row=4,
            column=1,
            padx=(5, 10),
            pady=(5, 10),
            sticky='ew'
        )

        # Model Display Label
        settings = Settings()
        settings_dict = settings.get_dict()
        self.model_display_label = ttk.Label(
            frame,
            text=f"Current Model: {settings_dict.get('model', 'Not Set')}",
            bootstyle="primary",
            anchor='center'  # Center the text
        )
        self.model_display_label.grid(
            row=5,  # Positioned just below the title
            column=0,
            columnspan=2,
            sticky='ew',
            padx=10,
            pady=5
        )

        # Conversation Frame - make responsive
        self.conversation_frame = ttk.LabelFrame(
            frame,
            text='Conversations',  # Centered by default
            bootstyle='primary'
        )
        self.conversation_frame.grid(
            row=6,
            column=0,
            columnspan=2,
            padx=10,
            pady=10,
            sticky='nsew'
        )
        frame.grid_rowconfigure(6, weight=1)  # Allow conversation frame to expand

        # Conversation Text with Scrollbar
        conversation_text_frame = ttk.Frame(self.conversation_frame)
        conversation_text_frame.grid(
            row=0,
            column=0,
            padx=10,
            pady=10,
            sticky='nsew'
        )
        conversation_text_frame.grid_columnconfigure(0, weight=1)
        conversation_text_frame.grid_rowconfigure(0, weight=1)

        # Scrollbar for Conversation Text
        self.conversation_text_scrollbar = ttk.Scrollbar(conversation_text_frame)
        self.conversation_text_scrollbar.grid(
            row=0,
            column=1,
            sticky='ns'
        )

        # Conversation Text - make responsive with scrollbar
        self.conversation_text = ttk.Text(
            conversation_text_frame,
            wrap=ttk.WORD,
            font=('Arial', 12),  # Increased font size
            height=6,
            yscrollcommand=self.conversation_text_scrollbar.set
        )
        self.conversation_text.grid(
            row=0,
            column=0,
            sticky='nsew'
        )
        # Configure scrollbar
        self.conversation_text_scrollbar.config(command=self.conversation_text.yview)

        # Configure tags for colored and bold text
        self.conversation_text.tag_config('ai', foreground='light gray', font=('Arial', 12, 'bold'))
        self.conversation_text.tag_config('you', foreground='blue', font=('Arial', 12, 'bold'))

        self.conversation_frame.grid_rowconfigure(0, weight=1)
        self.conversation_frame.grid_columnconfigure(0, weight=1)

        # Ensure the main frame can expand
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(6, weight=1)  # Critical: give weight to Output Log row

        # Output Log Frame - card-like border with full expansion
        self.output_log_frame = ttk.LabelFrame(
            frame,
            text='Output Log:',
            bootstyle='primary'
        )
        self.output_log_frame.grid(
            row=7,
            column=0,
            columnspan=2,  # Span across both columns
            padx=10,
            pady=10,
            sticky='nsew'  # Expand in all directions
        )

        # Ensure Output Log frame can expand
        self.output_log_frame.grid_columnconfigure(0, weight=1)
        self.output_log_frame.grid_rowconfigure(0, weight=1)

        # Output Log Text Frame with Scrollbar - full expansion
        output_log_text_frame = ttk.Frame(self.output_log_frame)
        output_log_text_frame.grid(
            row=0,
            column=0,
            padx=10,
            pady=10,
            sticky='nsew'  # Critical for resizing
        )
        output_log_text_frame.grid_columnconfigure(0, weight=1)  # Text box column
        output_log_text_frame.grid_rowconfigure(0, weight=1)  # Text box row

        # Scrollbar for Output Log
        self.output_log_scrollbar = ttk.Scrollbar(output_log_text_frame)
        self.output_log_scrollbar.grid(
            row=0,
            column=1,
            sticky='ns'
        )

        # Output Log Text Box - fully dynamic
        self.output_log_text = ttk.Text(
            output_log_text_frame,
            wrap=ttk.WORD,
            font=('Arial', 12),  # Larger font
            height=6,  # Initial height
            state='disabled',  # Read-only
            yscrollcommand=self.output_log_scrollbar.set
        )
        self.output_log_text.grid(
            row=0,
            column=0,
            sticky='nsew'  # Expand in all directions
        )

        # Configure scrollbar
        self.output_log_scrollbar.config(command=self.output_log_text.yview)

         # Clear Output Log button
        self.clear_log_button = ttk.Button(
            frame,
            text='Clear Output Log',
            bootstyle='success',
            command=self.clear_output_log
        )
        self.clear_log_button.grid(
            row=8,
            column=0,
            sticky='ew',
            padx=10,
            pady=10
        )

        # Settings Button - make responsive
        settings_button = ttk.Button(
            self,
            text='Settings',
            bootstyle="success",
            command=self.open_settings
        )
        settings_button.grid(
            row=9,
            column=0,
            sticky='ew',
            padx=10,
            pady=10
        )

        # Mobile Button
        mobile_button = ttk.Button(
            self,
            text='Mobile',
            bootstyle="success",
            command=self.open_mobile_interface
        )
        mobile_button.grid(
            row=9,
            column=1,
            sticky='ew',
            padx=10,
            pady=10
        )

        # Reload Model Button
        reload_model_button = ttk.Button(
            self,
            text='Reload Model',
            bootstyle="success",
            command=self.reload_model_settings
        )
        reload_model_button.grid(
            row=10,
            column=0,
            columnspan=2,
            sticky='ew',
            padx=10,
            pady=10
        )

    def open_settings(self) -> None:
        from ui.settings_window import SettingsWindow
        SettingsWindow(self)

    def stop_previous_request(self) -> None:
        # Interrupt currently running request by queueing a stop signal as a dictionary.
        self.user_request_queue.put({'command': 'stop'})

    def display_input(self) -> str:
        # Get the input and update the conversation display
        user_input = self.input_text.get("1.0", "end-1c")

        # Enable text widget to insert text
        self.conversation_text.configure(state='normal')

        # Insert user input if not empty at the TOP with the 'you' tag
        if user_input.strip():
            # Insert at the top with the 'you' tag for formatting
            self.conversation_text.insert('1.0', f'You: {user_input.strip()}\n', 'you')
            
            # Scroll to the top
            self.conversation_text.see('1.0')

        # Disable text widget to make it read-only
        self.conversation_text.configure(state='disabled')

        # Clear the input text box
        self.input_text.delete('1.0', ttk.END)

        return user_input.strip()

    def update_message(self, message: str) -> None:
       # Update the conversation text with AI replies only
        # Ensure thread safety when updating the Tkinter GUI.
        def update_text():
            # Comprehensive list of phrases to filter out
            filtered_phrases = [
                'fetching instructions',
                'waiting for',
                'typing',
                'pressing enter',
                'loading',
                'based on current state',
                'processing',
                'preparing',
                'initializing',
                'submitting',
                'opening spotlight',
                'selecting the top',
                'thinking',
                'analyzing',
                'interpreting',
                'generating',
                'retrieving',
                'parsing',
                'exception unable',
                'user message',
                'typing',
                'please send',
                'the user has already',
                'the user typed',
                'the user said',
                'pressing enter',
                'press enter to submit',
                'the user just said',
                'user request submitted',
                'i have already typed',
                'i will press the enter key',
                'responding to the user',
                'message',
                'typed and submitted',
                'user said',
                'user requested',
                'user sent',
                'the user request'
            ]

            # Check if the message should be filtered
            should_filter = any(
                phrase in message.lower()
                for phrase in filtered_phrases
            )

            # Enable text widget to insert text
            self.conversation_text.configure(state='normal')

            # Insert only meaningful AI responses at the TOP
            if message.strip() and not should_filter:
                # Remove any previous "Thinking..." message
                thinking_start = self.conversation_text.search('AI: Thinking...', '1.0', stopindex='end')
                if thinking_start:
                    thinking_end = f"{thinking_start} lineend+1c"
                    self.conversation_text.delete(thinking_start, thinking_end)

                # Insert at the top of the text with the 'ai' tag for formatting
                self.conversation_text.insert('1.0', f'AI: {message.strip()}\n', 'ai')

            # Scroll to the top
            self.conversation_text.see('1.0')

            # Disable text widget to make it read-only
            self.conversation_text.configure(state='disabled')

            # Log filtered messages in Output Log
            if message.strip() and should_filter:
                self.update_output_log(message)

            # Log status messages
            if 'Sending status:' in message:
                status = message.split('Sending status:')[-1].strip()
                self.log_system_action('Status', {'message': status})

        def show_thinking():
            # Enable text widget to insert text
            self.conversation_text.configure(state='normal')

            # Insert "Thinking..." message at the top with the 'ai' tag
            self.conversation_text.insert('1.0', 'AI: Thinking...\n', 'ai')

            # Scroll to the top
            self.conversation_text.see('1.0')

            # Disable text widget to make it read-only
            self.conversation_text.configure(state='disabled')

        # Schedule show_thinking and update_text to run on the main thread using after
        self.after(0, show_thinking)
        self.after(1000, update_text)

    def open_mobile_interface(self):
        """
        Open the mobile interface and display QR code.

        Creates a Gradio server and displays QR code in a popup window.
        """

        def launch_mobile_server():
            try:
                # Add project root to Python path
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)

                # Dynamically import mobile_server module
                mobile_server_path = os.path.join(os.path.dirname(__file__), 'mobile_server.py')
                spec = importlib.util.spec_from_file_location("mobile_server", mobile_server_path)
                mobile_server_module = importlib.util.module_from_spec(spec)
                sys.modules["mobile_server"] = mobile_server_module
                spec.loader.exec_module(mobile_server_module)

                # Create mobile server instance with current core
                core_instance = getattr(self, 'core', None)
                if core_instance is None:
                  from core import Core
                  core_instance = Core()

                mobile_server = mobile_server_module.MobileServer(core_instance=core_instance)

                # Start server and get public URL
                public_url = mobile_server.start()

                # Ensure we have a valid URL
                if not public_url:
                    raise ValueError("Failed to start mobile server")

                # Generate QR code
                qr_code_path = mobile_server.generate_qr_code(public_url)

                # Display QR code in a popup window (thread-safe)
                def update_ui():
                    try:
                        # Create QR Code Popup Window
                        qr_popup = ttk.Toplevel(self)
                        qr_popup.title("Mobile Interface QR Code")
                        qr_popup.geometry("400x400")
                        qr_popup.resizable(False, False)

                        # Position the popup next to the main window
                        main_window_geo = self.geometry()
                        main_x = self.winfo_x()
                        main_y = self.winfo_y()
                        main_width = self.winfo_width()

                        # Parse main window geometry
                        geo_match = re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', main_window_geo)
                        if geo_match:
                            # Position popup to the right of the main window
                            popup_x = main_x + main_width + 10
                            popup_y = main_y
                            qr_popup.geometry(f"+{popup_x}+{popup_y}")

                        # Frame to organize content
                        content_frame = ttk.Frame(qr_popup)
                        content_frame.pack(expand=True, fill='both', padx=10, pady=10)

                        # QR Code Label
                        qr_label = ttk.Label(content_frame)
                        qr_label.pack(pady=(0, 10), expand=True)

                        # Load and convert QR code image
                        qr_image = Image.open(qr_code_path)
                        qr_photo = ImageTk.PhotoImage(qr_image)

                        # Insert the image into the text widget
                        qr_label.configure(image=qr_photo)
                        qr_label.image = qr_photo  # Keep a reference

                        # URL Label with improved styling
                        url_label = ttk.Label(
                            content_frame,
                            text=f"Scan QR to Open:\n{public_url}",
                            font=('Arial', 8),
                            bootstyle='secondary'
                        )
                        url_label.pack(pady=(5, 0))

                        # Instructions Label
                        instructions_label = ttk.Label(
                            content_frame,
                            text="Open Mobile Interface",
                            font=('Arial', 7, 'italic'),
                            bootstyle='light'
                        )
                        instructions_label.pack(pady=(2, 0))

                    except Exception as ui_error:
                        print(f"Error updating UI: {ui_error}")
                        import traceback
                        traceback.print_exc()

                # Schedule UI updates on the main thread
                self.after(0, update_ui)

                # Store mobile server for potential later use
                self.mobile_server = mobile_server

            except Exception as e:
                # Log any errors with more detailed information
                import traceback
                error_message = f"Error opening mobile interface: {str(e)}\n{traceback.format_exc()}"
                print(error_message)
                self.update_output_log(error_message)

        # Start mobile server in a separate thread to prevent UI freezing
        threading.Thread(target=launch_mobile_server, daemon=True).start()

    def create_reload_mobile_button(self):
        """
        Create a button to launch the mobile interface and generate QR code

        Returns:
            ttk.Button: Mobile interface launch button
        """
        mobile_button = ttk.Button(
            self,
            text="Mobile",
            style='success.TButton',
            command=self.open_mobile_interface
        )
        mobile_button.pack(side='left', padx=5, pady=5)
        return mobile_button

    def create_widgets(self):
        # Existing widget creation code...

        # Add reload mobile button after save button
        self.reload_mobile_btn = self.create_reload_mobile_button()

    def reload_model_settings(self) -> None:
        # Reload settings from the settings file
        settings = Settings()
        settings_dict = settings.get_dict()

        # Update model display
        if 'model' in settings_dict:
            model = settings_dict['model']
            self.model_display_label.configure(text=f"Current Model: {model}")

        # Update OpenAI API key and base URL if needed
        if 'base_url' in settings_dict:
            os.environ['OPENAI_BASE_URL'] = settings_dict['base_url']

    def execute_user_request(self, event=None) -> None:
        # Puts the user request received from the UI into the MP queue being read in App to be sent to Core.
        user_request = self.display_input()

        if user_request == '' or user_request is None:
            return

        self.update_message('Fetching Instructions')

        # Wrap the user request in a dictionary with an id
        command_obj = {
            'id': 'ui_command',
            'command': user_request,
            'type': 'text'
        }

        self.user_request_queue.put(command_obj)

    def clear_output_log(self):
        """
        Clears the content of the output log text area.
        """
        self.update_output_log("")  # Clear the log