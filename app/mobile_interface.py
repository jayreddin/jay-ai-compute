import os
import sys
import threading
import queue
import gradio as gr

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from core import Core
from utils.settings import Settings

class MobileInterface:
    def __init__(self, core_instance=None):
        """
        Initialize Mobile Interface with optional Core instance
        
        Args:
            core_instance (Core, optional): Existing Core instance to synchronize
        """
        self.core = core_instance or Core()
        
        # Thread-safe communication queues
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # Shared state with thread-safe mechanisms
        self.shared_state = {
            'conversation_history': [],
            'current_input': '',
            'current_output': '',
            'output_log': [],
            'lock': threading.Lock()
        }

    def update_shared_state(self, key, value):
        """
        Thread-safe method to update shared state
        
        Args:
            key (str): Key in shared state
            value (any): Value to update
        """
        with self.shared_state['lock']:
            self.shared_state[key] = value

    def get_shared_state(self, key):
        """
        Thread-safe method to retrieve shared state
        
        Args:
            key (str): Key in shared state
        
        Returns:
            any: Value of the key
        """
        with self.shared_state['lock']:
            return self.shared_state[key]

    def create_interface(self):
        """
        Create synchronized Gradio interface
        
        Returns:
            gr.Blocks: Gradio interface
        """
        def sync_input(input_text):
            """Synchronize input across interfaces"""
            self.update_shared_state('current_input', input_text)
            self.input_queue.put(input_text)
            return input_text

        def process_input(input_text):
            """Process input and generate response"""
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

    def launch(self, share=True):
        """
        Launch the mobile interface
        
        Args:
            share (bool, optional): Whether to create a public share link. Defaults to True.
        
        Returns:
            str: Public URL of the interface
        """
        interface = self.create_interface()
        
        try:
            app = interface.launch(
                share=share,
                server_name='0.0.0.0',
                prevent_thread_lock=True
            )
            
            # Get public URL
            public_url = app.share_url if share else app.local_url
            
            return public_url
        
        except Exception as e:
            print(f"Error launching mobile interface: {e}")
            return None

def main():
    """
    Standalone launch of mobile interface
    """
    mobile_interface = MobileInterface()
    mobile_interface.launch()

if __name__ == "__main__":
    main()