import json
import os
import logging
from multiprocessing import Queue
from time import sleep
from typing import Any
import webbrowser
import subprocess

try:
    import pyautogui
except Exception as e:
    logging.warning(f"Warning: Could not import pyautogui: {e}")
    logging.warning("Running in headless mode. Some GUI automation features will be disabled.")
    pyautogui = None

class Interpreter:
    def __init__(self, status_queue: Queue):
        # MP Queue to put current status of execution in while processes commands.
        # It helps us reflect the current status on the UI.
        self.status_queue = status_queue
        
        # Check and warn about GUI automation capabilities
        if pyautogui is None:
            logging.warning("WARNING: GUI automation is not available. Some functionality will be limited.")
            self.headless_mode = True
        else:
            self.headless_mode = False

    def process_commands(self, json_commands: list[dict[str, Any]]) -> bool:
        """
        Reads a list of JSON commands and runs the corresponding function call as specified in context.txt
        :param json_commands: List of JSON Objects with format as described in context.txt
        :return: True for successful execution, False for exception while interpreting or executing.
        """
        for command in json_commands:
            success = self.process_command(command)
            if not success:
                return False  # End early and return
        return True

    def process_command(self, json_command: dict[str, Any]) -> bool:
        """
        Reads the passed in JSON object and extracts relevant details. Format is specified in context.txt.
        After interpretation, it proceeds to execute the appropriate function call.

        :return: True for successful execution, False for exception while interpreting or executing.
        """
        function_name = json_command['function']
        parameters = json_command.get('parameters', {})
        human_readable_justification = json_command.get('human_readable_justification')
        print(f'Now performing - {function_name} - {parameters} - {human_readable_justification}')
        self.status_queue.put(human_readable_justification)
        
        # Comprehensive handling for headless mode
        gui_functions = ['click', 'moveTo', 'typewrite', 'write', 'press', 'hotkey']
        if self.headless_mode and function_name in gui_functions:
            logging.warning(f"Skipping GUI function {function_name} in headless mode.")
            return True # Simulate action without executing for headless mode
        
        try:
            self.execute_function(function_name, parameters)
            return True
        except Exception as e:
            self.status_queue.put(f'We are having a problem executing this step - {type(e)} - {e}')
            self.status_queue.put(f'This was the json we received from the LLM: {json.dumps(json_command, indent=2)}')
            self.status_queue.put(f'This is what we extracted:\n         function_name:{function_name}\n         parameters:{parameters}')
            return False

    def execute_function(self, function_name: str, parameters: dict[str, Any]) -> None:
        """
            We are expecting only two types of function calls below
            1. time.sleep() - to wait for web pages, applications, and other things to load.
            2. pyautogui calls to interact with system's mouse and keyboard.
        """
        # Sometimes pyautogui needs warming up i.e. sometimes first call isn't executed hence padding a random call here
        if pyautogui is not None:
            pyautogui.press("command", interval=0.2)

        if function_name == "sleep":
            secs = parameters.get("secs")
            if secs:
                sleep(secs)
        elif function_name == "open_url":
            url = parameters.get("url")
            self.open_url_in_browser(url)
        elif function_name == "open_application":
             app_name = parameters.get("name")
             self.open_application(app_name)
        elif function_name == "run_terminal_command":
            command = parameters.get("command")
            self.run_terminal_command(command)
        elif pyautogui is not None and hasattr(pyautogui, function_name):
            # Execute the corresponding pyautogui function i.e. Keyboard or Mouse commands.
            function_to_call = getattr(pyautogui, function_name)
            if function_name == 'write' and ('string' in parameters or 'text' in parameters):
                # 'write' function expects a string, not a 'text' keyword argument but LLM sometimes gets confused on the parameter name.
                string_to_write = parameters.get('string') or parameters.get('text')
                interval = parameters.get('interval', 0.1)
                function_to_call(string_to_write, interval=interval)
            elif function_name == 'press' and ('keys' in parameters):
                keys = parameters.get('keys', [])
                presses = parameters.get('presses', 1)
                interval = parameters.get('interval', 0.2)
                for key in keys:
                    function_to_call(key, presses=presses, interval=interval)
            elif function_name == 'press' and ('key' in parameters): # Modified this line
                 key = parameters.get('key') # Added this line
                 function_to_call(key) # Modified this line
            elif function_name == 'hotkey' and ('keys' in parameters):
                keys = parameters.get('keys', [])
                function_to_call(*keys)
            else:
                # For other functions, pass the parameters as they are
                function_to_call(**parameters)
        else:
            print(f'No such function {function_name} in our interface\'s interpreter')
    
    def open_url_in_browser(self, url: str) -> None:
        """
        Opens the URL in the default browser.

         Args:
             url (str): The URL to open.
        """
        self.status_queue.put(f'opening URL {url}')
        
        settings = Settings()
        settings_dict = settings.get_dict()
        default_browser = settings_dict.get('default_browser', 'Default')
        
        if default_browser == 'Default':
            webbrowser.open(url)
        elif default_browser == 'Chrome':
            webbrowser.get('chrome').open(url)
        elif default_browser == 'Firefox':
            webbrowser.get('firefox').open(url)
        elif default_browser == 'Safari':
            webbrowser.get('safari').open(url)
        elif default_browser == 'Edge':
             webbrowser.get('edge').open(url)
        else:
             webbrowser.open(url)

    def open_application(self, app_name: str) -> None:
        """
        Opens an application.

        Args:
             app_name (str): The application name to open.
        """
        self.status_queue.put(f'opening application {app_name}')
        try:
          subprocess.Popen(app_name, shell=True) # Use shell=True so subprocess will use the shell to call the application
        except Exception as e:
          self.status_queue.put(f"Error opening application '{app_name}': {e}")

    def run_terminal_command(self, command: str) -> None:
        """
        Opens a terminal and executes the command.

        Args:
             command (str): The terminal command to execute.
        """
        self.status_queue.put(f'running terminal command: {command}')
        try:
            subprocess.Popen(['/bin/bash', '-c', command])
        except Exception as e:
           self.status_queue.put(f'Error running terminal command {command}: {e}')