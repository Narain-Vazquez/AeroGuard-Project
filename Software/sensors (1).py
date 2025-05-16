import json
import time
import requests
import RPi.GPIO as GPIO
from gpiozero import PWMOutputDevice
from subprocess import call

# Function to play different types of alarms
def play_alarm(alarm_type):
    LED_PIN = 27
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.output(LED_PIN, GPIO.HIGH)

    buzzer = PWMOutputDevice(17)
    buzzer.frequency = 1000
    buzzer.value = 0.5

    if alarm_type == "helmet":
        call(["aplay", "/home/aeroguard/Desktop/helmet_alarm.wav"])
    elif alarm_type == "lifejacket":
        call(["aplay", "/home/aeroguard/Desktop/lifejacket_alarm.wav"])
    elif alarm_type == "fire":
        call(["aplay", "/home/aeroguard/Desktop/fire_alarm.wav"])

    # Let the alarm sound for 1 second
    time.sleep(1)

    # Turn everything off
    buzzer.value = 0
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()

# Continuously monitor the remote state
while True:
    try:
        resp = requests.get("http://154.201.89.38:8001/state", timeout=5)
        data = resp.json()
        raw_state = data.get("state")
        if not raw_state:
            print("No 'state' field in response:", data)
        else:
            # Parse the JSON string into a dict
            state = json.loads(raw_state)
            #print("state is:", state)

            # Normalize to lowercase strings for comparison
            helmet = str(state.get("helmet", "")).lower()
            lifejacket = str(state.get("lifejacket", "")).lower()
            fire = str(state.get("fire", "")).lower()

            if helmet == "true":
                #print("Helmet not detected. Triggering alarm...")
                play_alarm("helmet")
            elif lifejacket == "true":
                #print("Lifejacket not detected. Triggering alarm...")
                play_alarm("lifejacket")
            elif fire == "true":
                #print("Fire detected. Triggering alarm...")
                play_alarm("fire")
            else:
                print("All clear. No alarm needed.")

    except Exception as e:
        print("Error occurred while requesting or processing state:", e)

    time.sleep(2)