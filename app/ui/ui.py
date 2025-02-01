from ui.main_window import MainWindow

class UI:
    def __init__(self):
        self.main_window = MainWindow()

    def run(self):
        self.main_window.mainloop()

    def display_current_status(self, text):
        self.main_window.update_message(text)