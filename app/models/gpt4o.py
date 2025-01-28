import json
import time
from typing import Any

from models.model import Model
from openai.types.beta.threads.message import Message
from utils.screen import Screen


# TODO
# [ ] Function calling with assistants api - https://platform.openai.com/docs/assistants/tools/function-calling/quickstart

class GPT4o(Model):
    def __init__(self, model_name, base_url, api_key, context):
        super().__init__(model_name, base_url, api_key, context)

        # GPT4o has Assistant Mode enabled that we can utilize to make Open Interface be more contextually aware
        self.assistant = self.client.beta.assistants.create(
            name='Open Interface Backend',
            instructions=self.context,
            model=model_name,
            # tools=[],
        )

        self.thread = self.client.beta.threads.create()

        # IDs of images uploaded to OpenAI for use with the assistants API, can be cleaned up once thread is no longer needed
        self.list_of_image_ids = []

    def get_instructions_for_objective(self, original_user_request: str, step_num: int = 0) -> dict[str, Any]:
        # Upload screenshot to OpenAI - Note: Don't delete files from openai while the thread is active
        openai_screenshot_file_id = self.upload_screenshot_and_get_file_id()

        self.list_of_image_ids.append(openai_screenshot_file_id)

        # Format user request to send to LLM
        formatted_user_request = self.format_user_request_for_llm(original_user_request, step_num,
                                                                  openai_screenshot_file_id)

        # Read response
        llm_response = self.send_message_to_llm(formatted_user_request)
        json_instructions: dict[str, Any] = self.convert_llm_response_to_json_instructions(llm_response)

        return json_instructions

    def send_message_to_llm(self, formatted_user_request) -> Message:
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role='user',
            content=formatted_user_request
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            instructions=''
        )

        while run.status != 'completed':
            print(f'Waiting for response, sleeping for 1. run.status={run.status}')
            time.sleep(1)

            if run.status == 'failed':
                print(f'failed run run.required_action:{run.required_action} run.last_error: {run.last_error}\n\n')
                return None

        if run.status == 'completed':
            # NOTE: Apparently right now the API doesn't have a way to retrieve just the last message???
            #  So instead you get all messages and take the latest one
            response = self.client.beta.threads.messages.list(
                thread_id=self.thread.id
            )

            return response.data[0]
        else:
            print('Run did not complete successfully.')
            return None

    def upload_screenshot_and_get_file_id(self):
        """
        Upload screenshot to OpenAI and display in UI output log.
        
        :return: File ID of uploaded screenshot
        """
        # Import Screen utility and get screenshot file path
        from utils.screen import Screen
        filepath = Screen().get_screenshot_file()
        
        # Optional: Display screenshot in UI output log if UI is available
        try:
            from app import App
            if hasattr(App, 'ui') and App.ui:
                App.ui.display_screenshot_in_output_log()
        except Exception as display_error:
            print(f"Could not display screenshot in output log: {display_error}")
        
        # Existing screenshot upload logic
        try:
            # Your existing OpenAI screenshot upload code here
            openai_file = self.client.files.create(
                file=open(filepath, "rb"),
                purpose="vision"
            )
            return openai_file.id
        
        except Exception as upload_error:
            print(f"Error uploading screenshot: {upload_error}")
            return None

    def format_user_request_for_llm(self, original_user_request, step_num, openai_screenshot_file_id) -> list[
        dict[str, Any]]:
        request_data: str = json.dumps({
            'original_user_request': original_user_request,
            'step_num': step_num
        })

        content = [
            {
                'type': 'text',
                'text': request_data
            },
            {
                'type': 'image_file',
                'image_file': {
                    'file_id': openai_screenshot_file_id
                }
            }
        ]

        return content

    def convert_llm_response_to_json_instructions(self, llm_response: Message) -> dict[str, Any]:
        llm_response_data: str = llm_response.content[0].text.value.strip()

        # Our current LLM model does not guarantee a JSON response hence we manually parse the JSON part of the response
        # Check for updates here - https://platform.openai.com/docs/guides/text-generation/json-mode
        start_index = llm_response_data.find('{')
        end_index = llm_response_data.rfind('}')

        try:
            json_response = json.loads(llm_response_data[start_index:end_index + 1].strip())
        except Exception as e:
            print(f'Error while parsing JSON response - {e}')
            json_response = {}

        return json_response

    def cleanup(self):
        # Note: Cannot delete screenshots while the thread is active. Cleanup during shut down.
        for id in self.list_of_image_ids:
            self.client.files.delete(id)
        self.thread = self.client.beta.threads.create()  # Using old thread even by accident would cause Image errors
