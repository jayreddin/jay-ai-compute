import os
import sys
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .ui_logging import UILoggingMixin
from utils.settings import Settings
from tkinter import messagebox, BooleanVar

class AdvancedSettingsWindow(ttk.Toplevel, UILoggingMixin):
    """
    Enhanced settings window for managing AI model configurations.
    Provides interface for both OpenAI and custom model settings with improved UI/UX.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title('AI Model Settings')
        self.parent = parent
        
        # Window configuration
        self.window_width = 400
        self.window_height = 700
        self.setup_window_geometry()
        
        # Initialize settings
        self.settings = Settings()
        
        # Setup main container with padding
        self.setup_main_container()
        self.create_settings_interface()
        self._load_saved_settings()

    def setup_window_geometry(self):
        """Configure window size and position"""
        self.geometry(f'{self.window_width}x{self.window_height}')
        self.minsize(self.window_width, self.window_height)
        self.resizable(False, True)
        
        # Center window on parent
        x = self.parent.winfo_x() + (self.parent.winfo_width() - self.window_width) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - self.window_height) // 2
        self.geometry(f'+{x}+{y}')
        
        self.transient(self.parent)
        self.grab_set()

    def setup_main_container(self):
        """Setup main container with scrolling support"""
        # Create main frame
        self.main_frame = ttk.Frame(self, padding=10)
        self.main_frame.pack(fill=BOTH, expand=True)
        self.main_frame.columnconfigure(0, weight=1)

    def create_settings_interface(self):
        """Create the main settings interface"""
        # Header section
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, sticky=EW, pady=(0, 15))
        
        ttk.Label(
            header_frame,
            text="AI Model Configuration",
            font=('TkDefaultFont', 12, 'bold'),
            bootstyle="primary"
        ).pack(anchor=W)
        
        # Setup sections
        self._setup_model_type_selection() # Checkboxes for model type selection
        self._setup_openai_section()
        self._setup_custom_model_section()
        self._setup_action_buttons()

    def _setup_model_type_selection(self):
        """Setup Model Type Selection Section (Checkboxes)"""
        model_type_frame = ttk.Frame(self.main_frame)
        model_type_frame.grid(row=1, column=0, sticky=EW, pady=(0, 10))
        
        # OpenAI Models Checkbox
        self.openai_enabled_var = BooleanVar(value=False)
        openai_check = ttk.Checkbutton(
            model_type_frame,
            text="OpenAI Models",
            variable=self.openai_enabled_var,
            bootstyle="primary-round-toggle",
            command=self.toggle_openai_frame
        )
        openai_check.pack(side=LEFT, padx=10)
        
        # Custom AI Model Checkbox
        self.custom_enabled_var = BooleanVar(value=False)
        custom_check = ttk.Checkbutton(
            model_type_frame,
            text="Custom AI Models",
            variable=self.custom_enabled_var,
            bootstyle="primary-round-toggle",
            command=self.toggle_custom_model_frame
        )
        custom_check.pack(side=LEFT)

    def _setup_openai_section(self):
        """Setup OpenAI configuration section"""
        # OpenAI Settings Card
        self.openai_frame = ttk.LabelFrame(
            self.main_frame,
            text="OpenAI Configuration",
            bootstyle="primary"
        )
        self.openai_frame.grid(row=2, column=0, sticky=EW, pady=(0, 10))
        self.openai_frame.columnconfigure(0, weight=1)
        
        # API Key
        ttk.Label(
            self.openai_frame,
            text="API Key:",
            bootstyle="primary"
        ).grid(row=0, column=0, sticky=W, padx=5, pady=(10, 5))
        
        self.api_key_entry = ttk.Entry(self.openai_frame, show="•")
        self.api_key_entry.grid(row=1, column=0, sticky=EW, padx=5, pady=(0, 10))
        
        # Model Selection
        ttk.Label(
            self.openai_frame,
            text="Select Model:",
            bootstyle="primary"
        ).grid(row=2, column=0, sticky=W, padx=5, pady=(10, 5))
        
        self.model_var = ttk.StringVar(value='gpt-4o')
        models = [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4-vision-preview',
            'gpt-4-turbo'
        ]
        
        self.model_dropdown = ttk.Combobox(
            self.openai_frame,
            textvariable=self.model_var,
            values=models,
            state='readonly'
        )
        self.model_dropdown.grid(row=3, column=0, sticky=EW, padx=5, pady=(0, 10))
        
        # Save Button
        ttk.Button(
            self.openai_frame,
            text="Save OpenAI Settings",
            bootstyle="success",
            command=self.save_openai_settings
        ).grid(row=4, column=0, sticky=EW, padx=5, pady=10)
        
        self.openai_frame.grid_remove() # Initially hidden

    def _setup_custom_model_section(self):
        """Setup custom model configuration section"""
        # Custom Model Settings Card
        self.custom_frame = ttk.LabelFrame(
            self.main_frame,
            text="Custom Model Configuration",
            bootstyle="primary"
        )
        self.custom_frame.grid(row=4, column=0, sticky=EW, pady=(0, 10))
        self.custom_frame.columnconfigure(0, weight=1)
        
        # Custom Model Fields
        fields = [
            ("Base URL:", "base_url_entry", False),
            ("Model Name:", "base_model_entry", False),
            ("API Key:", "custom_model_api_key_entry", True)
        ]
        
        for idx, (label, attr_name, is_secret) in enumerate(fields):
            ttk.Label(
                self.custom_frame,
                text=label,
                bootstyle="primary"
            ).grid(row=idx * 2, column=0, sticky=W, padx=5, pady=(10, 5)) # Adjusted row number for labels
            
            entry = ttk.Entry(self.custom_frame, show="•" if is_secret else None)
            entry.grid(row=idx * 2 + 1, column=0, sticky=EW, padx=5, pady=(0, 5)) # Adjusted row number for entries
            setattr(self, attr_name, entry)
        
        # Save Button
        ttk.Button(
            self.custom_frame,
            text="Save Custom Model Settings",
            bootstyle="success",
            command=self.save_custom_model_settings
        ).grid(row=7, column=0, sticky=EW, padx=5, pady=10) # Adjusted row number for save button
        
        self.custom_frame.grid_remove() # Initially hidden

    def _setup_action_buttons(self):
        """Setup bottom action buttons"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=5, column=0, sticky=EW, pady=10)
        
        ttk.Button(
            button_frame,
            text="Reload Settings",
            bootstyle="info-outline",
            command=self.reload_settings
        ).pack(fill=X)

    def toggle_openai_frame(self):
        """Toggle visibility of OpenAI settings frame"""
        if self.openai_enabled_var.get():
            self.openai_frame.grid()
        else:
            self.openai_frame.grid_remove()

    def toggle_custom_model_frame(self):
        """Toggle visibility of Custom Model settings frame"""
        if self.custom_enabled_var.get():
            self.custom_frame.grid()
        else:
            self.custom_frame.grid_remove()

    def save_openai_settings(self):
        """Save OpenAI settings to file"""
        try:
            settings_update = {
                'api_key': self.api_key_entry.get().strip(),
                'model': self.model_var.get()
            }
            self.settings.save_settings_to_file(settings_update)
            messagebox.showinfo('Success', 'OpenAI settings saved successfully.')
        except Exception as e:
            logging.error(f"Error saving OpenAI settings: {e}")
            messagebox.showerror('Error', f'Failed to save settings: {e}')

    def save_custom_model_settings(self):
        """Save Custom Model settings to file"""
        try:
            settings_update = {
                'base_url': self.base_url_entry.get().strip(),
                'base_model': self.base_model_entry.get().strip(),
                'custom_model_api_key': self.custom_model_api_key_entry.get().strip()
            }
            self.settings.save_settings_to_file(settings_update)
            messagebox.showinfo('Success', 'Custom Model settings saved successfully.')
        except Exception as e:
            logging.error(f"Error saving Custom Model settings: {e}")
            messagebox.showerror('Error', f'Failed to save settings: {e}')

    def _load_saved_settings(self):
        """Load saved settings into UI elements"""
        settings_dict = self.settings.get_dict()
        
        # Load OpenAI settings
        if 'api_key' in settings_dict:
            self.api_key_entry.insert(0, settings_dict['api_key'])
        if 'model' in settings_dict:
            self.model_var.set(settings_dict['model'])
        
        # Load Custom Model settings
        if 'base_url' in settings_dict:
            self.base_url_entry.insert(0, settings_dict['base_url'])
        if 'base_model' in settings_dict:
            self.base_model_entry.insert(0, settings_dict['base_model'])
        if 'custom_model_api_key' in settings_dict:
            self.custom_model_api_key_entry.insert(0, settings_dict['custom_model_api_key'])

    def reload_settings(self):
        """Reload all settings from file"""
        try:
            settings_dict = self.settings.get_dict()
            
            # Clear and reload OpenAI settings
            self.api_key_entry.delete(0, 'end')
            self.model_var.set('gpt-4o')  # Reset to default
            if 'api_key' in settings_dict:
                self.api_key_entry.insert(0, settings_dict['api_key'])
            if 'model' in settings_dict:
                self.model_var.set(settings_dict['model'])
            
            # Clear and reload Custom Model settings
            self.base_url_entry.delete(0, 'end')
            self.base_model_entry.delete(0, 'end')
            self.custom_model_api_key_entry.delete(0, 'end')
            if 'base_url' in settings_dict:
                self.base_url_entry.insert(0, settings_dict['base_url'])
            if 'base_model' in settings_dict:
                self.base_model_entry.insert(0, settings_dict['base_model'])
            if 'custom_model_api_key' in settings_dict:
                self.custom_model_api_key_entry.insert(0, settings_dict['custom_model_api_key'])
        except Exception as e:
            logging.error(f"Error reloading settings: {e}")
            messagebox.showerror('Error', f'Failed to reload settings: {e}')
