import paho.mqtt.client as mqtt
import json 
import requests
import os 
from dotenv import find_dotenv, load_dotenv

load_dotenv()


def control_light(intent : str, device: str):
    client = mqtt.Client()    
    client.username_pw_set(os.environ.get("MQTT_USERNAME"), os.environ.get("MQTT_PASSWORD"))
    # Connect to the broker
    try:
        client.connect(
            os.environ.get("MQTT_BROKER"), 
            1883,
             keepalive=60
             )
        # Publish the message
        topic = os.environ.get("MQTT_TOPIC")
        print("intent = ", intent)

        if intent == "turn on":
            print("working for turn on ")
            payload_dict = {device:1, "client_id":"iniyal testing"}

        elif intent == "turn off":
            print("working for turn off")
            payload_dict = {device:0, "client_id":"iniyal testing"}
        else:
            return "unable do the action , please say like turn on or turn off "

        payload = json.dumps(payload_dict)
        client.publish(topic=topic, payload=payload,qos=0)
        client.disconnect()
        return "turned light successfully"
    except Exception as e:
        print(f"Error: {e}")
        client.disconnect()
        return "unable to turn on light , sorry"

    # Disconnect from the broker

def get_lead_count():
    try:
        response = requests.get(os.environ.get("GET_LEAD_COUNT_URL"))
        data = response.json()
        return json.dumps(data)
    except Exception as e:
        print("Error = ", e)
        return "unable to fatch leads data"




