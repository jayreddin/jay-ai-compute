import ttkbootstrap as ttk
from ui.logging_mixin import UILoggingMixin
from utils.settings import Settings


class SettingsWindow(ttk.Toplevel, UILoggingMixin):
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
        from ui.advanced_settings_window import AdvancedSettingsWindow
        advanced_settings_window = AdvancedSettingsWindow(self)
        advanced_settings_window.grab_set()  # Make the window modal