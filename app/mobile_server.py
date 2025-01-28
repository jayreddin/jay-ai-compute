import os
import sys
import threading
import queue
from typing import Dict, Any, Optional, List

import gradio as gr
import qrcode

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from core import Core
from utils.settings import Settings

class MobileServer:
    def __init__(self, core_instance: Optional[Core] = None):
        """
        Initialize Mobile Server with optional Core instance.

        Args:
            core_instance (Core, optional): Existing Core instance to synchronize. 
                                            Creates a new Core instance if not provided.
        """
        self.core: Core = core_instance or Core()
        self.app: Optional[gr.Blocks] = None
        self.public_url: Optional[str] = None
        
        # Thread-safe communication queues
        self.input_queue: queue.Queue = queue.Queue()
        self.output_queue: queue.Queue = queue.Queue()
        
        # Shared state with thread-safe mechanisms
        self.shared_state: Dict[str, Any] = {
            'conversation_history': [],
            'current_input': '',
            'current_output': '',
            'output_log': [],
            'lock': threading.Lock()
        }

    def update_shared_state(self, key: str, value: Any) -> None:
        """
        Thread-safe method to update shared state.

        Args:
            key (str): Key in shared state to update
            value (Any): Value to set for the given key
        """
        with self.shared_state['lock']:
            self.shared_state[key] = value

    def get_shared_state(self, key: str) -> Any:
        """
        Thread-safe method to retrieve shared state.

        Args:
            key (str): Key in shared state to retrieve

        Returns:
            Any: Value of the specified key
        """
        with self.shared_state['lock']:
            return self.shared_state[key]

    def create_gradio_interface(self) -> gr.Blocks:
        """
        Create synchronized Gradio interface.

        Returns:
            gr.Blocks: Configured Gradio interface for mobile interaction
        """
        def sync_input(input_text: str) -> str:
            """Synchronize input across interfaces"""
            self.update_shared_state('current_input', input_text)
            self.input_queue.put(input_text)
            return input_text

        def process_input(input_text: str) -> str:
            """
            Process input and generate response.

            Args:
                input_text (str): User input text

            Returns:
                str: Generated response or error message
            """
            try:
                # Process input using Core
                response = self.core.generate_response(input_text)
                
                # Update shared state
                with self.shared_state['lock']:
                    self.shared_state['conversation_history'].append({
                        'input': input_text,
                        'output': response
                    })
                    self.shared_state['current_output'] = response
                
                # Put response in output queue
                self.output_queue.put(response)
                
                return response
            except Exception as e:
                error_response = f"Error: {str(e)}"
                self.output_queue.put(error_response)
                return error_response

        with gr.Blocks() as interface:
            with gr.Row():
                with gr.Column():
                    # Input components
                    input_textbox = gr.Textbox(
                        label="Input", 
                        placeholder="Enter your message...",
                        value=lambda: self.get_shared_state('current_input')
                    )
                    input_textbox.change(
                        fn=sync_input, 
                        inputs=input_textbox, 
                        outputs=input_textbox
                    )
                    
                    submit_btn = gr.Button("Send")
                    
                with gr.Column():
                    # Output components
                    output_textbox = gr.Textbox(
                        label="Output", 
                        interactive=False,
                        value=lambda: self.get_shared_state('current_output')
                    )
                    
                    conversation_history = gr.Dataframe(
                        headers=['Input', 'Output'],
                        value=lambda: self.get_shared_state('conversation_history')
                    )
            
            # Bind submit button
            submit_btn.click(
                fn=process_input, 
                inputs=input_textbox, 
                outputs=[output_textbox, conversation_history]
            )

        return interface

    def start(self) -> Optional[str]:
        """
        Start or stop the Gradio server. (Simplified, no queue)

        Returns:
            Optional[str]: Public URL for the Gradio interface, or None if failed
        """
        # If server is already running, stop it
        if self.app is not None:
            self.stop()
            return None

        # Create Gradio interface
        interface = self.create_gradio_interface()
    
        # Find an available port
        import socket
        def find_free_port() -> int:
            """Find and return a free network port"""
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                s.listen(1)
                port = s.getsockname()[1]
            return port

        try:
            # Determine port and launch configuration
            free_port = find_free_port()
            gradio_kwargs = {
                'share': True,  # Enable public sharing
                'server_name': '0.0.0.0',  # Listen on all network interfaces
                'server_port': free_port,  # Use dynamically found port
                'prevent_thread_lock': True,  # Prevent blocking the main thread
                'show_error': True,  # Show detailed errors
            }
            
            # Launch without queue
            self.app, local_url, public_url = interface.launch(**gradio_kwargs)
        
            # Prefer public URL, fallback to local URL
            self.public_url = public_url or local_url or f'http://0.0.0.0:{free_port}'
        
            # Generate and save QR code
            qr_code_path = self.generate_qr_code(self.public_url)
        
            print(f"Gradio Mobile Interface URL (No Queue): {self.public_url}")
            print(f"QR Code saved to: {qr_code_path}")

            print(f"Mobile Interface URL: {self.public_url}")
            return self.public_url

        except Exception as e:
            print(f"Error starting Gradio server (No Queue): {e}")
            import traceback
            traceback.print_exc()
            with open("server_status.txt", "w") as f:
                f.write("Server failed to start.\n")
            
            # Additional cleanup
            try:
                if hasattr(self, 'app'):
                    self.app.close()
            except Exception:
                pass
            
            # Reset server state
            self.app = None
            self.public_url = None
            
            return None

    def stop(self) -> None:
        """
        Stop the Gradio server and clean up resources.
        """
        if self.app:
            try:
                self.app.close()
            except Exception as e:
                print(f"Error stopping Gradio server: {e}")
            finally:
                self.app = None
                self.public_url = None

    def generate_qr_code(self, url: str) -> str:
        """
        Generate QR code for given URL.

        Args:
            url (str): URL to encode in QR code

        Returns:
            str: Path to generated QR code image
        """
        # Ensure URL is valid
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Create and save QR code image
        qr_code_dir = os.path.join(os.path.dirname(__file__), 'qr_codes')
        os.makedirs(qr_code_dir, exist_ok=True)
        qr_code_path = os.path.join(qr_code_dir, 'mobile_interface_qr.png')
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save(qr_code_path)

        return qr_code_path
