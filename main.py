import openai
from dotenv import find_dotenv, load_dotenv
import time 
import logging
import json
import os 
import pvporcupine
import pyaudio
import struct
from functions import control_light, control_fan
import azure.cognitiveservices.speech as speechsdk



load_dotenv()

client = openai.OpenAI()

model = "gpt-3.5-turbo-16k"

instructions = "Your name is Jarvis, an AI assistant created by Rahul Rajeev."

class AssistantManager:
    thread_id = None
    assistant_id = os.environ.get("ASSISTANT_ID")

    def __init__(self):
        self.client = client
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        

        # initailizing the assistant 
        if AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id=AssistantManager.assistant_id
            )

        # storing the existing thread if there is one 
        if AssistantManager.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id=AssistantManager.thread_id
            )

    def create_thread(self):
        if not self.thread:
            thread_obj = self.client.beta.threads.create()
            AssistantManager.thread_id = thread_obj.id
            self.thread = thread_obj
           

    
    def add_messsage_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id, role=role, content=content
            )

    def run_assistant(self, instructions):
        if self.thread and self.assistant:
            self.run = self.client.beta.threads.runs.create(
                thread_id = self.thread.id,
                assistant_id = self.assistant.id,
                instructions = instructions
            )

    def process_message(self):
        if self.thread:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            
            last_message = messages.data[0]
           
            role = last_message.role
            response = last_message.content[0].text.value
            print("\n Jarvis : ", response)

    # for monitoring what happens in between the execution of run 
    def wait_for_completion(self):
        if self.thread and self.run:
            while True:
                time.sleep(5)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id = self.thread_id,
                    run_id = self.run.id
                )
               
                # checking the status of the models executions 
                if run_status.status == "completed":
                    self.process_message()
                    break
                elif run_status.status == "requires_action":
                    pass
                    print("Function calling working ")
                    self.call_required_function(
                        required_actions=run_status.required_action.submit_tool_outputs.model_dump()
                    )
                    # if we the use the tools like function it will happen here 

    def call_required_function(self, required_actions):
        if not self.run:
            return
        tool_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])

            if func_name == "light_controller":
                output = control_light(arguments["intent"], arguments["device"])
                tool_outputs.append({"tool_call_id": action["id"], "output": output})
            elif func_name == "control_fan":
                output = control_fan(arguments["device"], arguments["speed"])
                tool_outputs.append({"tool_call_id": action["id"], "output": output})
            else:
                raise ValueError(f"Unknown function: {func_name}")
            
            #  submitting the out of function calls to the assistant 
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id, run_id=self.run.id, tool_outputs=tool_outputs
        )


                

    def run_steps(self):
        run_steps = self.client.beta.threads.runs.steps.list(
            thread_id=self.thread.id, run_id=self.run.id
        )
        print(f"Run-Steps::: {run_steps}")
        return run_steps.data
    

def create_speech_recognizer():
    speech_config = speechsdk.SpeechConfig(
        subscription=os.environ.get("SPEECH_KEY"),
        region=os.environ.get("SPEECH_REGION")
    )
    speech_config.speech_recognition_language = "en-US"
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    return speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)



# Initialize Porcupine for wake word detection
access_key = os.getenv("PICOVOICE_ACCESS_KEY")
porcupine = pvporcupine.create(
    access_key=access_key,
    keyword_paths=["Hey-Jarvis_en_windows_v3_0_0.ppn"]
)

# Set up the microphone for Porcupine
pa = pyaudio.PyAudio()
stream = pa.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=porcupine.sample_rate,
    input=True,
    frames_per_buffer=porcupine.frame_length
)


def wake_word_detector():
    """Detect the wake word using Porcupine and PyAudio."""
    print("Listening for the wake word...")
    try:
        while True:
            # Read audio input in chunks matching Porcupine's frame_length
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            
            # Convert raw audio bytes to integers
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            # Process the audio frame with Porcupine
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("Wake word detected!")
                return True
    except Exception as e:
        print(f"Error during wake word detection: {e}")
        return False



def listen_and_transcribe(recognizer):
    print("Listening for your command...")
    result = recognizer.recognize_once_async().get()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(result.text))
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized.")
        return None
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
        return None


# Main function to integrate with assistant
def main():
    recognizer = create_speech_recognizer()
    manager = AssistantManager()

    while True:
        # Listen for the keyword "Jarvis"
        if wake_word_detector():
            # Once "Jarvis" is detected, listen for the command
            user_command = listen_and_transcribe(recognizer)
            if user_command:
                if user_command.lower() in ("exit", "exit.", "stop", "stop."):
                    print("Goodbye")
                    break

                # Pass the command to the assistant
                manager.create_thread()
                manager.add_messsage_to_thread(role="user", content=user_command)
                manager.run_assistant(instructions=instructions)
                manager.wait_for_completion()


if __name__ == "__main__":
    main()
        
