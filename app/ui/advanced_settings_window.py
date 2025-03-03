import ttkbootstrap as ttk
from ui.logging_mixin import UILoggingMixin
from utils.settings import Settings


class AdvancedSettingsWindow(ttk.Toplevel, UILoggingMixin):
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
        ttk.Label(openai_frame, text='Select OpenAI Model:', bootstyle="primary").grid(row=2, column=0, sticky='w', padx=5,
                                                                                       pady=(10, 5))

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
        ttk.Label(custom_model_frame, text='Custom Model:', bootstyle="primary").grid(row=0, column=0, sticky='w', padx=5,
                                                                                     pady=(10, 5))
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