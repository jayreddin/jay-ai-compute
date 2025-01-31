import os
import sys
import importlib.util
import threading
from turtle import hideturtle
import webbrowser
from multiprocessing import Queue
from pathlib import Path
from datetime import datetime
from typing import Union
import re

# import speech_recognition as sr
import ttkbootstrap as ttk
from PIL import Image, ImageTk

from llm import DEFAULT_MODEL_NAME
from utils.settings import Settings
from version import version


def open_link(url) -> None:
    webbrowser.open_new(url)


class UI:
    def __init__(self):
        self.main_window = self.MainWindow()

    def run(self) -> None:
        self.main_window.mainloop()

    def display_current_status(self, text: str):
        self.main_window.update_message(text)

    class AdvancedSettingsWindow(ttk.Toplevel):
        """
        Self-contained settings sub-window for the UI
        """

        def __init__(self, parent):
            super().__init__(parent)
            self.title('AI Model Settings')
            
            # Initialize settings
            self.settings = Settings()
            
            # Set precise window dimensions
            window_width = 370
            window_height = 820
            
            # Set window size and minimum size
            self.geometry(f'{window_width}x{window_height}')
            self.minsize(window_width, window_height)
            
            # Ensure window doesn't expand unnecessarily
            self.grid_propagate(False)
            
            # Position the window directly on top of the parent window
            self.transient(parent)  # Set as a child window of the parent
            self.grab_set()  # Make modal
            
            # Calculate parent window position and center this window
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            
            x = parent_x + (parent_width - window_width) // 2
            y = parent_y + (parent_height - window_height) // 2
            
            self.geometry(f'+{x}+{y}')
            
            # Main content frame
            content_frame = ttk.Frame(self)
            content_frame.pack(fill='both', expand=True, padx=10, pady=10)
            content_frame.columnconfigure(0, weight=1)

            # OpenAI Card-like Frame
            openai_frame = ttk.LabelFrame(content_frame, text='OpenAI', bootstyle='primary')
            openai_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=(0, 10))
            openai_frame.columnconfigure(0, weight=1)

            # OpenAI API Key Input
            label_api = ttk.Label(openai_frame, text='OpenAI API Key:', bootstyle="primary")
            label_api.grid(row=0, column=0, sticky='w', padx=5, pady=(10, 5))
            self.api_key_entry = ttk.Entry(openai_frame, width=50)
            self.api_key_entry.grid(row=1, column=0, sticky='ew', padx=5, pady=(0, 10))

            # Model Selection for OpenAI
            ttk.Label(openai_frame, text='Select OpenAI Model:', bootstyle="primary").grid(row=2, column=0, sticky='w', padx=5, pady=(10, 5))
            
            # Model selection radio buttons
            self.model_var = ttk.StringVar(value='gpt-4o')  # default selection
            models = [
                ('GPT-4o (Default. Medium-Accurate, Medium-Fast)', 'gpt-4o'),
                ('GPT-4o-mini (Cheapest, Fastest)', 'gpt-4o-mini'),
                ('GPT-4v (Deprecated. Most-Accurate, Slowest)', 'gpt-4-vision-preview'),
                ('GPT-4-Turbo (Least Accurate, Fast)', 'gpt-4-turbo')
            ]
            
            # Create a frame to hold the radio buttons
            radio_frame = ttk.Frame(openai_frame)
            radio_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=(0, 10))
            
            for text, value in models:
                ttk.Radiobutton(
                    radio_frame, 
                    text=text, 
                    value=value, 
                    variable=self.model_var, 
                    bootstyle="info"
                ).pack(anchor=ttk.W, pady=5)

            # Save Button for OpenAI Settings
            save_model_button = ttk.Button(
                openai_frame, 
                text='Save OpenAI Settings', 
                bootstyle="success", 
                command=self.save_openai_settings
            )
            save_model_button.grid(row=4, column=0, sticky='ew', padx=5, pady=10)

            # Custom AI Model Card-like Frame
            custom_model_frame = ttk.LabelFrame(content_frame, text='Custom AI Model', bootstyle='primary')
            custom_model_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=(0, 10))
            custom_model_frame.columnconfigure(0, weight=1)

            # Custom Model Selection
            ttk.Label(custom_model_frame, text='Custom Model:', bootstyle="primary").grid(row=0, column=0, sticky='w', padx=5, pady=(10, 5))
            self.custom_model_var = ttk.StringVar(value='custom')
            ttk.Radiobutton(
                custom_model_frame, 
                text='Enable Custom Model', 
                value='custom', 
                variable=self.custom_model_var, 
                bootstyle="info"
            ).grid(row=1, column=0, sticky='w', padx=5, pady=(0, 10))

            # Custom Base URL Input
            label_base_url = ttk.Label(custom_model_frame, text='Custom Base URL:', bootstyle="secondary")
            label_base_url.grid(row=2, column=0, sticky='w', padx=5, pady=(10, 5))
            self.base_url_entry = ttk.Entry(custom_model_frame, width=50)
            self.base_url_entry.grid(row=3, column=0, sticky='ew', padx=5, pady=(0, 10))

            # Custom Base Model Input
            label_base_model = ttk.Label(custom_model_frame, text='Custom Base Model:', bootstyle="secondary")
            label_base_model.grid(row=4, column=0, sticky='w', padx=5, pady=(10, 5))
            self.base_model_entry = ttk.Entry(custom_model_frame, width=50)
            self.base_model_entry.grid(row=5, column=0, sticky='ew', padx=5, pady=(0, 10))

            # Custom Model API Key Input
            label_custom_model_api_key = ttk.Label(custom_model_frame, text='Custom Model API Key:', bootstyle="secondary")
            label_custom_model_api_key.grid(row=6, column=0, sticky='w', padx=5, pady=(10, 5))
            self.custom_model_api_key_entry = ttk.Entry(custom_model_frame, width=50)
            self.custom_model_api_key_entry.grid(row=7, column=0, sticky='ew', padx=5, pady=(0, 10))

            # Save Button for Custom Model Settings
            save_custom_model_button = ttk.Button(
                custom_model_frame, 
                text='Save Custom Model Settings', 
                bootstyle="warning", 
                command=self.save_custom_model_settings
            )
            save_custom_model_button.grid(row=8, column=0, sticky='ew', padx=5, pady=10)

            # Reload Button for Model Settings
            reload_button = ttk.Button(
                content_frame, 
                text='Reload Model Selected', 
                bootstyle="info-outline", 
                command=self.reload_button
            )
            reload_button.grid(row=2, column=0, sticky='ew', padx=5, pady=(0, 10))

            # Populate UI
            settings_dict = self.settings.get_dict()

            if 'api_key' in settings_dict:
                self.api_key_entry.insert(0, settings_dict['api_key'])
            if 'model' in settings_dict:
                self.model_var.set(settings_dict['model'])
            if 'base_url' in settings_dict:
                self.base_url_entry.insert(0, settings_dict['base_url'])
            if 'base_model' in settings_dict:
                self.base_model_entry.insert(0, settings_dict['base_model'])
            if 'custom_model_api_key' in settings_dict:
                self.custom_model_api_key_entry.insert(0, settings_dict['custom_model_api_key'])

        def save_openai_settings(self) -> None:
            # Save OpenAI specific settings
            settings_dict = {}
            
            # Save API Key if present
            api_key = self.api_key_entry.get().strip()
            
            # Save Model if present
            model = self.model_var.get()
            
            if api_key:
                settings_dict['api_key'] = api_key
            
            settings_dict['model'] = model
            
            # Save settings
            self.settings.save_settings_to_file(settings_dict)
            
            # Update model display label in main window
            if hasattr(self, 'parent') and hasattr(self.parent, 'model_display_label'):
                self.parent.model_display_label.configure(text=f"Current Model: {model}")
            
            self.destroy()

        def save_custom_model_settings(self) -> None:
            # Save settings for Custom Model
            settings_dict = {}
            
            # Save Base URL if present
            base_url = self.base_url_entry.get().strip()
            if base_url:
                settings_dict['base_url'] = base_url
            
            # Save Base Model if present
            base_model = self.base_model_entry.get().strip()
            if base_model:
                settings_dict['base_model'] = base_model
                settings_dict['model'] = base_model
            
            # Save Custom Model API Key if present
            custom_model_api_key = self.custom_model_api_key_entry.get().strip()
            if custom_model_api_key:
                settings_dict['custom_model_api_key'] = custom_model_api_key
                # Override the active API key with custom model API key
                settings_dict['api_key'] = custom_model_api_key
            
            # Save settings
            self.settings.save_settings_to_file(settings_dict)
            
            # Update model display label in main window
            if hasattr(self, 'parent') and hasattr(self.parent, 'model_display_label'):
                display_model = base_model if base_model else 'Custom Model'
                self.parent.model_display_label.configure(text=f"Current Model: {display_model}")
            
            self.destroy()

        def reload_button(self) -> None:
            # Reload settings from file
            settings_dict = self.settings.get_dict()
            
            # Repopulate UI with current settings
            if 'api_key' in settings_dict:
                self.api_key_entry.delete(0, 'end')
                self.api_key_entry.insert(0, settings_dict['api_key'])
            
            if 'model' in settings_dict:
                self.model_var.set(settings_dict['model'])
            
            if 'base_url' in settings_dict:
                self.base_url_entry.delete(0, 'end')
                self.base_url_entry.insert(0, settings_dict['base_url'])
            
            if 'base_model' in settings_dict:
                self.base_model_entry.delete(0, 'end')
                self.base_model_entry.insert(0, settings_dict['base_model'])
            
            if 'custom_model_api_key' in settings_dict:
                self.custom_model_api_key_entry.delete(0, 'end')
                self.custom_model_api_key_entry.insert(0, settings_dict['custom_model_api_key'])

    class SettingsWindow(ttk.Toplevel):
        """
        Self-contained settings sub-window for the UI
        """

        def __init__(self, parent):
            super().__init__(parent)
            self.title('Settings')
            
            # Initialize settings
            self.settings = Settings()
            
            # Set precise window dimensions
            window_width = 370
            window_height = 450
            
            # Set window size and minimum size
            self.geometry(f'{window_width}x{window_height}')
            self.minsize(window_width, window_height)
            
            # Ensure window doesn't expand unnecessarily
            self.grid_propagate(False)
            
            # Position the window directly on top of the parent window
            self.transient(parent)  # Set as a child window of the parent
            self.grab_set()  # Make modal
            
            # Calculate parent window position and center this window
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            
            x = parent_x + (parent_width - window_width) // 2
            y = parent_y + (parent_height - window_height) // 2
            
            self.geometry(f'+{x}+{y}')
            
            # Main content frame
            content_frame = ttk.Frame(self)
            content_frame.pack(fill='both', expand=True, padx=10, pady=10)
            content_frame.columnconfigure(0, weight=1)

            # Browser Selection with card-like border
            browser_frame = ttk.LabelFrame(content_frame, text='Default Browser:', bootstyle='primary')
            browser_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=(0, 10))
            browser_frame.columnconfigure(0, weight=1)
            
            self.browser_combobox = ttk.Combobox(
                browser_frame, 
                values=['Chrome', 'Firefox', 'Safari', 'Edge', 'Default'], 
                state='readonly'
            )
            self.browser_combobox.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

            # Theme Selection with card-like border
            theme_frame = ttk.LabelFrame(content_frame, text='Theme:', bootstyle='primary')
            theme_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=(0, 10))
            theme_frame.columnconfigure(0, weight=1)
            
            self.available_themes = ['darkly', 'cyborg', 'journal', 'solar', 'superhero']
            self.theme_combobox = ttk.Combobox(
                theme_frame, 
                values=self.available_themes, 
                state='readonly'
            )
            self.theme_combobox.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
            self.theme_combobox.bind('<<ComboboxSelected>>', self.on_theme_change)

            # Ding Sound Toggle
            self.play_ding = ttk.IntVar(value=0)
            play_ding_check = ttk.Checkbutton(
                content_frame, 
                text='Play Ding on Completion', 
                variable=self.play_ding,
                bootstyle="success-round-toggle"
            )
            play_ding_check.grid(row=2, column=0, sticky='w', padx=5, pady=(0, 10))

            # Custom LLM Guidance with card-like border
            llm_frame = ttk.LabelFrame(content_frame, text='Custom LLM Guidance:', bootstyle='primary')
            llm_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=(0, 10))
            llm_frame.columnconfigure(0, weight=1)
            
            self.llm_instructions_text = ttk.Text(
                llm_frame, 
                height=4, 
                wrap=ttk.WORD
            )
            self.llm_instructions_text.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

            # Buttons Frame (Reload and AI Model Settings)
            buttons_frame = ttk.Frame(content_frame)
            buttons_frame.grid(row=4, column=0, sticky='ew', padx=5, pady=(0, 10))
            buttons_frame.columnconfigure(0, weight=1)
            buttons_frame.columnconfigure(1, weight=1)

            # Reload Button (changed to blue)
            reload_button = ttk.Button(
                buttons_frame, 
                text='Reload Model', 
                bootstyle="info-outline", 
                command=self.reload_button
            )
            reload_button.grid(row=0, column=0, sticky='ew', padx=(0, 5))

            # AI Model Settings Button
            advanced_settings_button = ttk.Button(
                buttons_frame, 
                text='AI Model Settings', 
                bootstyle="info-outline", 
                command=self.open_advanced_settings
            )
            advanced_settings_button.grid(row=0, column=1, sticky='ew', padx=(5, 0))

            # Save Settings Button
            save_button = ttk.Button(
                content_frame, 
                text='Save Settings', 
                bootstyle="success", 
                command=self.save_button
            )
            save_button.grid(row=5, column=0, sticky='ew', padx=5, pady=(0, 10))

            # Populate UI
            settings_dict = self.settings.get_dict()

            if 'default_browser' in settings_dict:
                self.browser_combobox.set(settings_dict['default_browser'])
            if 'play_ding_on_completion' in settings_dict:
                self.play_ding.set(1 if settings_dict['play_ding_on_completion'] else 0)
            if 'custom_llm_instructions':
                self.llm_instructions_text.insert('1.0', settings_dict['custom_llm_instructions'])
            self.theme_combobox.set(settings_dict.get('theme', 'superhero'))

        def on_theme_change(self, event=None):
            # Theme change logic remains the same
            theme_name = self.theme_combobox.get()
            self.change_theme(theme_name)

        def save_button(self):
            # Save settings
            settings_dict = {}
            settings_dict['default_browser'] = self.browser_combobox.get()
            settings_dict['play_ding_on_completion'] = bool(self.play_ding.get())
            settings_dict['theme'] = self.theme_combobox.get()
            settings_dict['custom_llm_instructions'] = self.llm_instructions_text.get('1.0', 'end-1c')

            # Save to settings file
            self.settings.save_settings_to_file(settings_dict)
            
            # Close the settings window
            self.destroy()

        def reload_button(self):
            # Reload settings from file
            settings_dict = self.settings.get_dict()
            
            # Repopulate UI with current settings
            if 'default_browser' in settings_dict:
                self.browser_combobox.set(settings_dict['default_browser'])
            if 'play_ding_on_completion' in settings_dict:
                self.play_ding.set(1 if settings_dict['play_ding_on_completion'] else 0)
            if 'custom_llm_instructions' in settings_dict:
                self.llm_instructions_text.delete('1.0', 'end')
                self.llm_instructions_text.insert('1.0', settings_dict['custom_llm_instructions'])
            self.theme_combobox.set(settings_dict.get('theme', 'superhero'))

        def open_advanced_settings(self):
            # Open the Advanced Settings (AI Model Settings) window
            advanced_settings_window = UI.AdvancedSettingsWindow(self)
            advanced_settings_window.grab_set()  # Make the window modal

    class MainWindow(ttk.Window):
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
                sticky='ew',    # Expand horizontally
                pady=(0, 10)    # Add some padding below
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
                command=self.execute_user_request
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
                font=('Arial', 16),  # Increased font size
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
                font=('Arial', 16),  # Larger font
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

            # Settings Button - make responsive
            settings_button = ttk.Button(
                self, 
                text='Settings', 
                bootstyle="info-outline", 
                command=self.open_settings
            )
            settings_button.grid(
                row=8, 
                column=0, 
                sticky='ew', 
                padx=10, 
                pady=10
            )

            # Mobile Button
            mobile_button = ttk.Button(
                self, 
                text='Mobile', 
                bootstyle="info-outline", 
                command=self.open_mobile_interface
            )
            mobile_button.grid(
                row=8, 
                column=1, 
                sticky='ew', 
                padx=10, 
                pady=10
            )

            # Reload Model Button
            reload_model_button = ttk.Button(
                self, 
                text='Reload Model', 
                bootstyle="info-outline", 
                command=self.reload_model_settings
            )
            reload_model_button.grid(
                row=9, 
                column=0, 
                columnspan=2, 
                sticky='ew', 
                padx=10, 
                pady=10
            )

        def open_settings(self) -> None:
            UI.SettingsWindow(self)

        def stop_previous_request(self) -> None:
            # Interrupt currently running request by queueing a stop signal.
            self.user_request_queue.put('stop')

        def display_input(self) -> str:
            # Get the input and update the conversation display
            user_input = self.input_text.get("1.0", "end-1c")
            
            # Enable text widget to insert text
            self.conversation_text.configure(state='normal')
            
            # Insert user input if not empty at the TOP
            if user_input.strip():
                # Insert at the top
                self.conversation_text.insert('1.0', f'You: {user_input.strip()}\n')
                
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
                    'user request submitted'
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

                    # Insert at the top of the text
                    self.conversation_text.insert('1.0', f'AI: {message.strip()}\n')

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

                # Insert "Thinking..." message at the top
                self.conversation_text.insert('1.0', 'AI: Thinking...\n')

                # Scroll to the top
                self.conversation_text.see('1.0')

                # Disable text widget to make it read-only
                self.conversation_text.configure(state='disabled')

            # Schedule show_thinking and update_text to run on the main thread using after
            self.after(0, show_thinking)
            self.after(1000, update_text)

        def update_output_log(self, message: str, screenshot: Image = None) -> None:
            """
            Update the output log with a message and optional screenshot.
            
            :param message: Text message to display in the output log
            :param screenshot: Optional PIL Image object to display as a thumbnail
            """
            try:
                # Enable text widget for editing
                self.output_log_text.config(state='normal')
                
                # Clear previous content if message is empty
                if not message and not screenshot:
                    self.output_log_text.delete('1.0', 'end')
                
                # Insert message
                if message:
                    self.output_log_text.insert('1.0', f"{message}\n")
                
                # Insert screenshot thumbnail if provided
                if screenshot:
                    try:
                        # Resize screenshot to a thumbnail while maintaining aspect ratio
                        max_width = 300  # Adjust based on your UI preferences
                        width_percent = (max_width / float(screenshot.size[0]))
                        height_size = int((float(screenshot.size[1]) * float(width_percent)))
                        thumbnail = screenshot.resize((max_width, height_size), Image.LANCZOS)
                        
                        # Convert PIL Image to PhotoImage for Tkinter
                        photo = ImageTk.PhotoImage(thumbnail)
                        
                        # Insert the image into the text widget
                        self.output_log_text.image_create('1.0', image=photo)
                        # Keep a reference to prevent garbage collection
                        self.output_log_text.image = photo
                        
                        # Add a newline after the image
                        self.output_log_text.insert('1.0', '\n')
                    
                    except Exception as img_error:
                        self.output_log_text.insert('1.0', f"[ERROR] Failed to process screenshot: {str(img_error)}\n")
                
                # Scroll to the top
                self.output_log_text.see('1.0')
            
            except Exception as e:
                print(f"Error in update_output_log: {e}")
            
            finally:
                # Always disable text widget to make it read-only
                self.output_log_text.config(state='disabled')

        def log_system_action(self, action_type: str, details: Union[dict, str, None] = None) -> None:
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
                
                # Thread-safe log update
                try:
                    self.output_log_text.configure(state='normal')
                    self.output_log_text.insert('1.0', log_entry)
                    self.output_log_text.see('1.0')
                    self.output_log_text.configure(state='disabled')
                except Exception as e:
                    print(f"Logging error: {e}")

            # Ensure thread-safe execution
            if threading.current_thread() is threading.main_thread():
                log_action()
            else:
                self.output_log_text.after(0, log_action)

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
                style='primary.TButton',
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

def display_screenshot_in_output_log(self) -> None:
    """
    Capture and display the current screenshot in the Output Log.
    
    This method uses the Screen utility to capture a screenshot and then
    displays it in the output log text widget.
    """
    try:
        from utils.screen import Screen
        
        # Capture screenshot
        screenshot = Screen().get_screenshot()
        
        # Display screenshot in output log with a descriptive message
        self.update_output_log("Screenshot captured:", screenshot)
    
    except Exception as e:
        # Log any errors that occur during screenshot capture or display
        self.update_output_log(f"Error capturing screenshot: {str(e)}")