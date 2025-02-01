import os
import sys
import logging
import threading
from typing import Optional, Dict, Any

import ttkbootstrap as ttk
from .ui_logging import UILoggingMixin
from utils.settings import Settings
from tkinter import filedialog, messagebox

class SettingsWindow(ttk.Toplevel, UILoggingMixin):
    """
    Self-contained settings sub-window for the UI
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title('Settings')
        
        # Set precise window dimensions
        window_width = 370
        window_height = 620
        
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
        
        # Create main content frame
        content_frame = ttk.Frame(self)
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create settings sections
        self.create_general_settings(content_frame)
        self.create_screenshot_settings(content_frame)
        self.create_mobile_settings(content_frame)
        self.create_theme_settings(content_frame)
        
        # Create AI Model Settings button
        self.create_ai_model_settings_button(content_frame)
        
        # Save and Cancel buttons
        self.create_action_buttons(content_frame)
        
        # Load existing settings
        self.load_settings()
    
    def create_general_settings(self, parent):
        """Create general settings section"""
        general_frame = ttk.LabelFrame(parent, text='General Settings', bootstyle='primary')
        general_frame.pack(fill='x', pady=(0, 10), padx=5)
        
        # Log Level Selection
        ttk.Label(general_frame, text='Log Level:', bootstyle='primary').pack(anchor='w', padx=5, pady=(10, 0))
        self.log_level_var = ttk.StringVar(value='INFO')
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        self.log_level_combo = ttk.Combobox(
            general_frame, 
            textvariable=self.log_level_var, 
            values=log_levels, 
            state='readonly', 
            width=30
        )
        self.log_level_combo.pack(padx=5, pady=(0, 10), fill='x')
        
        # Auto-update checkbox
        self.auto_update_var = ttk.BooleanVar(value=True)
        self.auto_update_check = ttk.Checkbutton(
            general_frame, 
            text='Enable Auto-Update', 
            variable=self.auto_update_var, 
            bootstyle='primary'
        )
        self.auto_update_check.pack(anchor='w', padx=5, pady=5)
    
    def create_screenshot_settings(self, parent):
        """Create screenshot settings section"""
        screenshot_frame = ttk.LabelFrame(parent, text='Screenshot Settings', bootstyle='primary')
        screenshot_frame.pack(fill='x', pady=(0, 10), padx=5)
        
        # Screenshot Directory
        ttk.Label(screenshot_frame, text='Screenshot Directory:', bootstyle='primary').pack(anchor='w', padx=5, pady=(10, 0))
        
        screenshot_dir_frame = ttk.Frame(screenshot_frame)
        screenshot_dir_frame.pack(fill='x', padx=5, pady=(0, 10))
        
        self.screenshot_dir_var = ttk.StringVar(value=os.path.expanduser('~/Screenshots'))
        self.screenshot_dir_entry = ttk.Entry(screenshot_dir_frame, textvariable=self.screenshot_dir_var, width=30)
        self.screenshot_dir_entry.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        browse_btn = ttk.Button(
            screenshot_dir_frame, 
            text='Browse', 
            bootstyle='secondary', 
            command=self.browse_screenshot_dir
        )
        browse_btn.pack(side='right')
        
        # Screenshot Format
        ttk.Label(screenshot_frame, text='Screenshot Format:', bootstyle='primary').pack(anchor='w', padx=5, pady=(10, 0))
        self.screenshot_format_var = ttk.StringVar(value='PNG')
        screenshot_formats = ['PNG', 'JPEG', 'BMP']
        self.screenshot_format_combo = ttk.Combobox(
            screenshot_frame, 
            textvariable=self.screenshot_format_var, 
            values=screenshot_formats, 
            state='readonly', 
            width=30
        )
        self.screenshot_format_combo.pack(padx=5, pady=(0, 10), fill='x')
    
    def create_mobile_settings(self, parent):
        """Create mobile interface settings section"""
        mobile_frame = ttk.LabelFrame(parent, text='Mobile Interface', bootstyle='primary')
        mobile_frame.pack(fill='x', pady=(0, 10), padx=5)
        
        # Mobile Port
        ttk.Label(mobile_frame, text='Mobile Interface Port:', bootstyle='primary').pack(anchor='w', padx=5, pady=(10, 0))
        self.mobile_port_var = ttk.IntVar(value=7860)
        self.mobile_port_entry = ttk.Entry(mobile_frame, textvariable=self.mobile_port_var, width=30)
        self.mobile_port_entry.pack(padx=5, pady=(0, 10), fill='x')
        
        # Mobile Interface Checkbox
        self.mobile_interface_var = ttk.BooleanVar(value=False)
        self.mobile_interface_check = ttk.Checkbutton(
            mobile_frame, 
            text='Enable Mobile Interface', 
            variable=self.mobile_interface_var, 
            bootstyle='primary'
        )
        self.mobile_interface_check.pack(anchor='w', padx=5, pady=5)
    
    def create_theme_settings(self, parent):
        """Create theme settings section"""
        theme_frame = ttk.LabelFrame(parent, text='Theme Settings', bootstyle='primary')
        theme_frame.pack(fill='x', pady=(0, 10), padx=5)
        
        # Theme Selection
        ttk.Label(theme_frame, text='Application Theme:', bootstyle='primary').pack(anchor='w', padx=5, pady=(10, 0))
        self.theme_var = ttk.StringVar(value='darkly')
        themes = [
            'darkly', 'flatly', 'journal', 'litera', 
            'lumen', 'minty', 'pulse', 'sandstone', 
            'united', 'yeti', 'cosmo', 'cyborg'
        ]
        self.theme_combo = ttk.Combobox(
            theme_frame, 
            textvariable=self.theme_var, 
            values=themes, 
            state='readonly', 
            width=30
        )
        self.theme_combo.pack(padx=5, pady=(0, 10), fill='x')
    
    def create_ai_model_settings_button(self, parent):
        """Create AI Model Settings button"""
        ai_model_settings_btn = ttk.Button(
            parent, 
            text='AI Model Settings', 
            bootstyle='secondary', 
            command=self.open_ai_model_settings
        )
        ai_model_settings_btn.pack(side='left', padx=5, pady=5)

    def open_ai_model_settings(self):
        """Open AI Model Settings window"""
        from app.ui.ui_aimodelsettings import AdvancedSettingsWindow
        AdvancedSettingsWindow(self)

    def create_action_buttons(self, parent):
        """Create save and cancel buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=(10, 0))
        
        save_btn = ttk.Button(
            button_frame, 
            text='Save Settings', 
            bootstyle='success', 
            command=self.save_settings
        )
        save_btn.pack(side='left', padx=5, expand=True, fill='x')
        
        ai_model_settings_btn = ttk.Button(
            button_frame, 
            text='AI Model Settings', 
            bootstyle='secondary', 
            command=self.open_ai_model_settings
        )
        ai_model_settings_btn.pack(side='left', padx=5, pady=5)
        
        cancel_btn = ttk.Button(
            button_frame, 
            text='Cancel', 
            bootstyle='danger', 
            command=self.destroy
        )
        cancel_btn.pack(side='right', padx=5, expand=True, fill='x')
    
    def browse_screenshot_dir(self):
        """Open directory selection dialog for screenshots"""
        selected_dir = filedialog.askdirectory(
            title='Select Screenshot Directory', 
            initialdir=os.path.expanduser('~')
        )
        if selected_dir:
            self.screenshot_dir_var.set(selected_dir)
    
    def load_settings(self):
        """Load existing settings into the UI"""
        settings_dict = self.settings.get_dict()
        
        # Log Level
        self.log_level_var.set(settings_dict.get('log_level', 'INFO'))
        
        # Auto Update
        self.auto_update_var.set(settings_dict.get('auto_update', True))
        
        # Screenshot Settings
        self.screenshot_dir_var.set(settings_dict.get('screenshot_dir', os.path.expanduser('~/Screenshots')))
        self.screenshot_format_var.set(settings_dict.get('screenshot_format', 'PNG'))
        
        # Mobile Interface
        self.mobile_port_var.set(settings_dict.get('mobile_port', 7860))
        self.mobile_interface_var.set(settings_dict.get('mobile_interface', False))
        
        # Theme
        self.theme_var.set(settings_dict.get('theme', 'darkly'))
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            settings_dict = {
                'log_level': self.log_level_var.get(),
                'auto_update': self.auto_update_var.get(),
                'screenshot_dir': self.screenshot_dir_var.get(),
                'screenshot_format': self.screenshot_format_var.get(),
                'mobile_port': self.mobile_port_var.get(),
                'mobile_interface': self.mobile_interface_var.get(),
                'theme': self.theme_var.get()
            }
            
            # Save settings
            self.settings.save_settings_to_file(settings_dict)
            
            # Optional: Apply theme if changed
            if hasattr(self.master, 'change_theme'):
                self.master.change_theme(settings_dict['theme'])
            
            # Close settings window
            self.destroy()
        
        except Exception as e:
            messagebox.showerror('Settings Error', f'Failed to save settings: {str(e)}')