import pvporcupine
import pyaudio
import struct  # For converting byte data to integers
import os
from dotenv import load_dotenv
load_dotenv()
# Get access key from environment variables
access_key = os.environ.get("PICOVOICE_ACCESS_KEY")

# Initialize Porcupine
porcupine = pvporcupine.create(
    access_key=access_key,
    keyword_paths=["Hey-Jarvis_en_windows_v3_0_0.ppn"]
)

# Set up the microphone
pa = pyaudio.PyAudio()
stream = pa.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=porcupine.sample_rate,
    input=True,
    frames_per_buffer=porcupine.frame_length  # Match Porcupine's frame_length
)

def wake_word_detector():
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
                
    finally:
        # Cleanup resources
        stream.close()
        pa.terminate()
        porcupine.delete()
