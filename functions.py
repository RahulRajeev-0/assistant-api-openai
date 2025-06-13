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
        # consider the case like turn on fan or light (so user may not specify the speed) 
        # depending up how the device is configured we can set the payload
        if intent == "turn on":
            if device == "device5": # assume device5 is a fan so we are checking if its a fan
                payload_dict = {device:1, "speed":5}
            elif device == "device6": # assume device6 is a fan
                payload_dict = {device:1, "speed":5,}
            else:
                payload_dict = {device:1}

            print("working for turn on ")

        elif intent == "turn off":
            if device == "device5":
                payload_dict = {device:0, "speed":5}
            elif device == "device6":
                payload_dict = {device:0, "speed":5}
            else:
                payload_dict = {device:0}
            print("working for turn off")
        else:
            return "unable do the action , please say like turn on or turn off "

        payload = json.dumps(payload_dict)
        client.publish(topic=topic, payload=payload, qos=0)
        client.disconnect()
        return "turned light successfully"
    except Exception as e:
        print(f"Error: {e}")
        client.disconnect()
        return "unable to turn on light , sorry"


def control_fan(device: str, speed: int):
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
        if device == "fan1":
            payload_dict = {"device5": 1, "speed":speed}
        elif device == "fan2":
            payload_dict = {"device6":1, "speed":speed }
        else:
            return "unable to find the device , at the moment"
        payload = json.dumps(payload_dict)
        client.publish(topic=topic, payload=payload, qos=0)
        return "Successfully changed"
    except Exception as e:
        print("Error = ", e)
        return "something went wrong unable to change"





