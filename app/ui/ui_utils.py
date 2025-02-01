from contextlib import contextmanager

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