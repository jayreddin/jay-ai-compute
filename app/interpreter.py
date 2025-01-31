import json
import os
import logging
from multiprocessing import Queue
from time import sleep
from typing import Any

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
            logging.warning(f"Skipping GUI function {function_name} in headless mode. Simulating action.")
            return self.simulate_headless_action(function_name, parameters)
        
        try:
            self.execute_function(function_name, parameters)
            return True
        except Exception as e:
            print(f'\nError:\nWe are having a problem executing this step - {type(e)} - {e}')
            print(f'This was the json we received from the LLM: {json.dumps(json_command, indent=2)}')
            print(f'This is what we extracted:')
            print(f'\t function_name:{function_name}')
            print(f'\t parameters:{parameters}')

            return False

    def simulate_headless_action(self, function_name: str, parameters: dict[str, Any]) -> bool:
        """
        Simulate actions in headless mode by logging and returning success
        """
        simulated_actions = {
            'click': f"Simulated click at {parameters.get('x', 'unknown')}, {parameters.get('y', 'unknown')}",
            'moveTo': f"Simulated mouse move to {parameters.get('x', 'unknown')}, {parameters.get('y', 'unknown')}",
            'typewrite': f"Simulated typing: {parameters.get('string', parameters.get('text', 'no text'))}",
            'write': f"Simulated writing: {parameters.get('string', parameters.get('text', 'no text'))}",
            'press': f"Simulated key press: {parameters.get('keys', parameters.get('key', 'no key'))}",
            'hotkey': f"Simulated hotkey: {list(parameters.values())}"
        }
        
        logging.info(simulated_actions.get(function_name, f"Simulated {function_name}"))
        return True

    def execute_function(self, function_name: str, parameters: dict[str, Any]) -> None:
        """
            We are expecting only two types of function calls below
            1. time.sleep() - to wait for web pages, applications, and other things to load.
            2. pyautogui calls to interact with system's mouse and keyboard.
        """
        # Sometimes pyautogui needs warming up i.e. sometimes first call isn't executed hence padding a random call here
        if pyautogui is not None:
            pyautogui.press("command", interval=0.2)

        if function_name == "sleep" and parameters.get("secs"):
            sleep(parameters.get("secs"))
        elif pyautogui is not None and hasattr(pyautogui, function_name):
            # Execute the corresponding pyautogui function i.e. Keyboard or Mouse commands.
            function_to_call = getattr(pyautogui, function_name)

            # Special handling for the 'write' function
            if function_name == 'write' and ('string' in parameters or 'text' in parameters):
                # 'write' function expects a string, not a 'text' keyword argument but LLM sometimes gets confused on the parameter name.
                string_to_write = parameters.get('string') or parameters.get('text')
                interval = parameters.get('interval', 0.1)
                function_to_call(string_to_write, interval=interval)
            elif function_name == 'press' and ('keys' in parameters or 'key' in parameters):
                # 'press' can take a list of keys or a single key
                keys_to_press = parameters.get('keys') or parameters.get('key')
                presses = parameters.get('presses', 1)
                interval = parameters.get('interval', 0.2)
                function_to_call(keys_to_press, presses=presses, interval=interval)
            elif function_name == 'hotkey':
                # 'hotkey' function expects multiple key arguments, not a list
                function_to_call(list(parameters.values()))
            else:
                # For other functions, pass the parameters as they are
                function_to_call(**parameters)
        else:
            print(f'No such function {function_name} in our interface\'s interpreter')
