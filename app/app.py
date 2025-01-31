import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import threading
import logging
from multiprocessing import freeze_support
import queue

from core import Core
from app.ui import UI


class App:
    """
    +----------------------------------------------------+
    | App                                                |
    |                                                    |
    |    +-------+                                       |
    |    |  GUI  |                                       |
    |    +-------+                                       |
    |        ^                                           |
    |        | (via MP Queues)                           |
    |        v                                           |
    |  +-----------+  (Screenshot + Goal)  +-----------+ |
    |  |           | --------------------> |           | |
    |  |    Core   |                       |    LLM    | |
    |  |           | <-------------------- |  (GPT-4V) | |
    |  +-----------+    (Instructions)     +-----------+ |
    |        |                                           |
    |        v                                           |
    |  +-------------+                                   |
    |  | Interpreter |                                   |
    |  +-------------+                                   |
    |        |                                           |
    |        v                                           |
    |  +-------------+                                   |
    |  |   Executer  |                                   |
    |  +-------------+                                   |
    +----------------------------------------------------+
    """

    def __init__(self):
        # Ensure DISPLAY is set before importing other modules
        if 'DISPLAY' not in os.environ:
            logging.warning("No DISPLAY environment variable found. Setting up virtual display.")
            os.environ['DISPLAY'] = ':99'

        self.core = Core()
        self.ui = UI()

        # Threading event to signal thread termination
        self.stop_event = threading.Event()

        # Create threads to facilitate communication between core and ui through queues
        self.core_to_ui_connection_thread = threading.Thread(
            target=self.send_status_from_core_to_ui, 
            daemon=True
        )
        self.ui_to_core_connection_thread = threading.Thread(
            target=self.send_user_request_from_ui_to_core, 
            daemon=True
        )

    def run(self) -> None:
        # Start threads before running UI
        self.core_to_ui_connection_thread.start()
        self.ui_to_core_connection_thread.start()

        try:
            self.ui.run()
        finally:
            # Signal threads to stop
            self.stop_event.set()
            
            # Wait for threads to finish
            self.core_to_ui_connection_thread.join(timeout=2)
            self.ui_to_core_connection_thread.join(timeout=2)

    def send_status_from_core_to_ui(self) -> None:
        while not self.stop_event.is_set():
            try:
                # Use a timeout to periodically check stop_event
                status = self.core.status_queue.get(timeout=1)
                print(f'Sending status: {status}')
                self.ui.display_current_status(status)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in send_status_from_core_to_ui: {e}")
                break

    def send_user_request_from_ui_to_core(self) -> None:
        while not self.stop_event.is_set():
            try:
                # Use a timeout to periodically check stop_event
                command_obj = self.ui.main_window.user_request_queue.get(timeout=1)
                
                # If it's a stop command
                if command_obj.get('command') == 'stop':
                    self.core.stop_previous_request()
                else:
                    # Extract the command from the command object
                    user_request = command_obj.get('command', '')
                    print(f'Sending user request: {user_request}')
                    
                    threading.Thread(
                        target=self.core.execute_user_request, 
                        args=(user_request,), 
                        daemon=True
                    ).start()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in send_user_request_from_ui_to_core: {e}")
                break

    def cleanup(self):
        # Signal threads to stop
        self.stop_event.set()
        
        # Wait for threads to finish
        self.core_to_ui_connection_thread.join(timeout=2)
        self.ui_to_core_connection_thread.join(timeout=2)
        
        # Cleanup core resources
        self.core.cleanup()


if __name__ == '__main__':
    freeze_support()  # As required by pyinstaller https://www.pyinstaller.org/en/stable/common-issues-and-pitfalls.html#multi-processing
    app = App()
    try:
        app.run()
    except KeyboardInterrupt:
        print("Application interrupted by user.")
    finally:
        app.cleanup()
        sys.exit(0)
