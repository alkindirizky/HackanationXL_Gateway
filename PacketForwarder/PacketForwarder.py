import serial
import time
import paho.mqtt.client as mqtt
import json

# MQTT Setting
client_name = 'LoraGateway'
broker_hostname = 'mqtt.flexiot.xl.co.id'
broker_port = 1883
broker_user = 'rabbit'
broker_pass = 'rabbit'
event_topic = 'generic_brand_777generic_devicev2/common'

def conv_to_sign_int8(val):
    if val >= 128:
        val -= 256
    
    return val

def process_data(mqtt_client, data):
    dev_rssi = conv_to_sign_int8(data[0])
    dev_type = data[1]
    dev_id = data[2]
    dev_data = data[3]

    #determine payload content
    payload = []
    if dev_type == 1:
        payload = {
            "eventName" : "SensorStatus",
            "status" : "none",
            "triggered" : str(dev_data),
            "RSSI" : str(dev_rssi),
            "mac" : "FFFFFFF{}".format(dev_id)
            }

        payload = json.dumps(payload)

    #publish the payload
    try:
        mqtt_client.publish(event_topic, payload)
        print("Published : {}".format(payload))
    except Exception as e:
        print(e)

def start_forwarder(com_port, baudrate = 115200, read_timeout_sec = 2, write_timeout_sec = 1):
    com = serial.Serial(com_port, baudrate, 8, 'N',
        1, read_timeout_sec, False, False, write_timeout_sec)

    client = mqtt.Client(client_name)
    client.username_pw_set(broker_user, broker_pass)
    client.connect(broker_hostname, broker_port)
    
    data = []
    while True:
        data = com.read_until(serial.LF)
        if data == b'':
            continue

        if data[0] == 83:
            print("{}".format(data.decode().replace('\n', '')))
            continue
        
        data = list(data)
        if len(data) < 4:
            print("ERR : Insufficient data : {}".format(data))
            continue

        process_data(client, data)
