import os
import sys
import logging
import threading
from typing import Optional, Dict, Any

import ttkbootstrap as ttk
from .ui_logging import UILoggingMixin
from utils.settings import Settings
from tkinter import messagebox, BooleanVar

class AdvancedSettingsWindow(ttk.Toplevel, UILoggingMixin):
    """
    Self-contained advanced settings sub-window for the UI
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title('AI Model Settings')
        
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
        
        # Initialize settings
        self.settings = Settings()
        
        # Main content frame
        content_frame = ttk.Frame(self)
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        content_frame.columnconfigure(0, weight=1)

        # OpenAI Checkbox and Card-like Frame
        openai_checkbox_frame = ttk.Frame(content_frame)
        openai_checkbox_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=(0, 10))
        
        self.openai_enabled_var = BooleanVar(value=False)
        openai_checkbox = ttk.Checkbutton(
            openai_checkbox_frame, 
            text='OpenAI', 
            variable=self.openai_enabled_var, 
            bootstyle="primary", 
            command=self.toggle_openai_frame
        )
        openai_checkbox.pack(side='left', padx=(0, 10))

        # OpenAI Card-like Frame
        self.openai_frame = ttk.LabelFrame(content_frame, text='OpenAI Settings', bootstyle='primary')
        self.openai_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=(0, 10))
        self.openai_frame.columnconfigure(0, weight=1)
        self.openai_frame.grid_remove()  # Initially hidden

        # OpenAI API Key Input
        label_api = ttk.Label(self.openai_frame, text='OpenAI API Key:', bootstyle="primary")
        label_api.grid(row=0, column=0, sticky='w', padx=5, pady=(10, 5))
        self.api_key_entry = ttk.Entry(self.openai_frame, width=50)
        self.api_key_entry.grid(row=1, column=0, sticky='ew', padx=5, pady=(0, 10))

        # Model Selection for OpenAI
        ttk.Label(self.openai_frame, text='Select OpenAI Model:', bootstyle="primary").grid(row=2, column=0, sticky='w', padx=5, pady=(10, 5))
        
        # Model selection radio buttons
        self.model_var = ttk.StringVar(value='gpt-4o')  # default selection
        models = [
            ('GPT-4o (Default. Medium-Accurate, Medium-Fast)', 'gpt-4o'),
            ('GPT-4o-mini (Cheapest, Fastest)', 'gpt-4o-mini'),
            ('GPT-4v (Deprecated. Most-Accurate, Slowest)', 'gpt-4-vision-preview'),
            ('GPT-4-Turbo (Least Accurate, Fast)', 'gpt-4-turbo')
        ]
        
        # Create a frame to hold the radio buttons
        radio_frame = ttk.Frame(self.openai_frame)
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
            self.openai_frame, 
            text='Save OpenAI Settings', 
            bootstyle="success", 
            command=self.save_openai_settings
        )
        save_model_button.grid(row=4, column=0, sticky='ew', padx=5, pady=10)

        # Custom AI Model Checkbox and Card-like Frame
        custom_model_checkbox_frame = ttk.Frame(content_frame)
        custom_model_checkbox_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=(0, 10))
        
        self.custom_model_enabled_var = BooleanVar(value=False)
        custom_model_checkbox = ttk.Checkbutton(
            custom_model_checkbox_frame, 
            text='Custom AI Model', 
            variable=self.custom_model_enabled_var, 
            bootstyle="primary", 
            command=self.toggle_custom_model_frame
        )
        custom_model_checkbox.pack(side='left', padx=(0, 10))

        # Custom AI Model Card-like Frame
        self.custom_model_frame = ttk.LabelFrame(content_frame, text='Custom AI Model Settings', bootstyle='primary')
        self.custom_model_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=(0, 10))
        self.custom_model_frame.columnconfigure(0, weight=1)
        self.custom_model_frame.grid_remove()  # Initially hidden

        # Custom Model Selection
        ttk.Label(self.custom_model_frame, text='Custom Model:', bootstyle="primary").grid(row=0, column=0, sticky='w', padx=5, pady=(10, 5))
        self.custom_model_var = ttk.StringVar(value='custom')
        ttk.Radiobutton(
            self.custom_model_frame, 
            text='Enable Custom Model', 
            value='custom', 
            variable=self.custom_model_var, 
            bootstyle="info"
        ).grid(row=1, column=0, sticky='w', padx=5, pady=(0, 10))

        # Custom Base URL Input
        label_base_url = ttk.Label(self.custom_model_frame, text='Custom Base URL:', bootstyle="secondary")
        label_base_url.grid(row=2, column=0, sticky='w', padx=5, pady=(10, 5))
        self.base_url_entry = ttk.Entry(self.custom_model_frame, width=50)
        self.base_url_entry.grid(row=3, column=0, sticky='ew', padx=5, pady=(0, 10))

        # Custom Base Model Input
        label_base_model = ttk.Label(self.custom_model_frame, text='Custom Base Model:', bootstyle="secondary")
        label_base_model.grid(row=4, column=0, sticky='w', padx=5, pady=(10, 5))
        self.base_model_entry = ttk.Entry(self.custom_model_frame, width=50)
        self.base_model_entry.grid(row=5, column=0, sticky='ew', padx=5, pady=(0, 10))

        # Custom Model API Key Input
        label_custom_model_api_key = ttk.Label(self.custom_model_frame, text='Custom Model API Key:', bootstyle="secondary")
        label_custom_model_api_key.grid(row=6, column=0, sticky='w', padx=5, pady=(10, 5))
        self.custom_model_api_key_entry = ttk.Entry(self.custom_model_frame, width=50)
        self.custom_model_api_key_entry.grid(row=7, column=0, sticky='ew', padx=5, pady=(0, 10))

        # Save Button for Custom Model Settings
        save_custom_model_button = ttk.Button(
            self.custom_model_frame, 
            text='Save Custom Model Settings', 
            bootstyle="success", 
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
        reload_button.grid(row=4, column=0, sticky='ew', padx=5, pady=(0, 10))

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

    def toggle_openai_frame(self):
        """
        Toggle visibility of OpenAI settings frame based on checkbox
        """
        if self.openai_enabled_var.get():
            self.openai_frame.grid()
        else:
            self.openai_frame.grid_remove()

    def toggle_custom_model_frame(self):
        """
        Toggle visibility of Custom Model settings frame based on checkbox
        """
        if self.custom_model_enabled_var.get():
            self.custom_model_frame.grid()
        else:
            self.custom_model_frame.grid_remove()

    def save_openai_settings(self) -> None:
        """
        Save OpenAI specific settings and reload the app
        """
        try:
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
            
            # Provide feedback
            messagebox.showinfo('Settings Saved', 'OpenAI settings have been successfully saved.')
            
            # Reload the application
            if hasattr(self, 'parent') and hasattr(self.parent, 'reload_application'):
                self.parent.reload_application()

            self.destroy()
        
        except Exception as e:
            messagebox.showerror('Save Error', f'Failed to save OpenAI settings: {str(e)}')

    def save_custom_model_settings(self) -> None:
        """
        Save settings for Custom Model and reload the app
        """
        try:
            settings_dict = {}
            
            # Save Base URL if present
            base_url = self.base_url_entry.get().strip()
            
            # Save Base Model if present
            base_model = self.base_model_entry.get().strip()
            
            # Save Custom Model API Key if present
            custom_model_api_key = self.custom_model_api_key_entry.get().strip()
            
            if base_url:
                settings_dict['base_url'] = base_url
            
            if base_model:
                settings_dict['base_model'] = base_model
            
            if custom_model_api_key:
                settings_dict['custom_model_api_key'] = custom_model_api_key
            
            # Save settings
            self.settings.save_settings_to_file(settings_dict)
            
            # Update model display label in main window
            if hasattr(self, 'parent') and hasattr(self.parent, 'model_display_label'):
                self.parent.model_display_label.configure(text=f"Current Model: Custom")
            
            # Provide feedback
            messagebox.showinfo('Settings Saved', 'Custom AI Model settings have been successfully saved.')
            
            # Reload the application
            if hasattr(self, 'parent') and hasattr(self.parent, 'reload_application'):
                self.parent.reload_application()

            self.destroy()
        
        except Exception as e:
            messagebox.showerror('Save Error', f'Failed to save Custom AI Model settings: {str(e)}')

    def reload_button(self) -> None:
        """
        Reload the currently selected model settings
        """
        try:
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
            
            # Provide feedback
            messagebox.showinfo('Settings Reloaded', 'Model settings have been reloaded from file.')
        
        except Exception as e:
            messagebox.showerror('Reload Error', f'Failed to reload model settings: {str(e)}')