
import paho.mqtt.client as paho
from paho import mqtt
from flask import Flask, render_template
import requests
#data of all sensors
data = {}

#Thingspeak url
elevator_pos="https://api.thingspeak.com/update?api_key=ZV2MQH5X04IBLC2I&field1="
elevator_spd="https://api.thingspeak.com/update?api_key=ZV2MQH5X04IBLC2I&field2="
elevator_queue= "https://api.thingspeak.com/update?api_key=ZV2MQH5X04IBLC2I&field3="

#Thingspeak url end

#function for Ubidots platform
def ubidots(label,value):
    TOKEN = "BBFF-9a8NOTBNaHBooZrvE7iMFcDf0nPE2y"  # Put your TOKEN here
    DEVICE_LABEL = "elevator"  # Put your device label here
    VARIABLE_LABEL_1 = label  # Put your first variable label here
    def build_payload(variable_1):
        # Creates two random values for sending data
        value_1 = value
        payload = {variable_1: value_1,}
        return payload


    def post_request(payload):
        # Creates the headers for the HTTP requests
        url = "http://industrial.api.ubidots.com"
        url = "{}/api/v1.6/devices/{}".format(url, DEVICE_LABEL)
        headers = {"X-Auth-Token": TOKEN, "Content-Type": "application/json"}

        # Makes the HTTP requests
        status = 400
        attempts = 0
        while status >= 400 and attempts <= 5:
            req = requests.post(url=url, headers=headers, json=payload)
            status = req.status_code
            attempts += 1
            #time.sleep(1)

        # Processes results
        print(req.status_code, req.json())
        if status >= 400:
            print("[ERROR] Could not send data after 5 attempts, please check \
                your token credentials and internet connection")
            return False

        print("[INFO] request made properly, your device is updated")
        return True


    def main():
        payload = build_payload(
            VARIABLE_LABEL_1)

        print("[INFO] Attemping to send data")
        post_request(payload)
        print("[INFO] finished")
    main()
#ubidot end





# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    if "Door_Position" in msg.topic:
        door_position = msg.payload.decode('utf8')  # This is a string
        door_position_integer = int(door_position)  # This is an integer
        print(f"The door is {door_position_integer}% opened.")
        data["door_position"] = door_position_integer

    if "Door_Status" in msg.topic:
        door_status = msg.payload.decode("utf-8")
        print("Door status: {}".format(door_status.split("Position")[0]))

        data["door_status"] = door_status.split("Position")[0]
    if "State" in msg.topic:
        state = msg.payload.decode("utf-8")
        print("State: {}".format(state))

        data["state"] = state
    if "building/Position" in msg.topic:
        elevator_position = msg.payload.decode("utf-8")
        print("Elevator position: {}".format(elevator_position))
        data["elevator_position"]=elevator_position
        # send data to Thingspeak
        requests.post(elevator_pos + elevator_position)
        # send data to Ubidots
        ubidots("elevator position", elevator_position)
    if "Speed" in msg.topic:
        speed = msg.payload.decode("utf-8")
        print("Speed: {}".format(speed))
        data["speed"]=speed[0:8]
        # send data to Thingspeak
        requests.post(elevator_spd + speed)
        # send data to Ubidots
        ubidots("elevator speed", speed)

    if "Queue" in msg.topic:
        Queue = msg.payload.decode("utf-8")
        print("Queue: {}".format(Queue))
        data["queue"]=Queue
        # send data to Thingspeak
        requests.post(elevator_queue + Queue)
        # send data to Ubidots
        ubidots("elevator queue", Queue)

client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect

# enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
client.username_pw_set("SotA2_Elevator", "z^!nENKNNDR4!Wj37SR3")
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
client.connect("33856ce158b64045a33edfdfe1bb55e8.s2.eu.hivemq.cloud", 8883)

# setting callbacks, use separate functions like above for better visibility
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_publish = on_publish

# subscribe to all topics of encyclopedia by using the wildcard "#"
client.subscribe("building/#", qos=1)

# loop_forever for simplicity, here you need to stop the loop manually
# you can also use loop_start and loop_stop
client.loop_start()

#Flask web server
app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def ren():
    return render_template('dashboard.html', data= data)

@app.route('/dashboard', methods=['GET', 'POST'])
def hello_world():
    return data

#Webserver is active on port 3569
app.run(host='0.0.0.0',debug=True, port=3569)
