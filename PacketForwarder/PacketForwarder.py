import serial
import time
import paho.mqtt.client as mqtt
import json
import time
import datetime

# MQTT Setting
client_name = 'LoraGateway'
broker_hostname = 'mqtt.flexiot.xl.co.id'
broker_port = 1883
broker_user = 'rabbit'
broker_pass = 'rabbit'

event_topic = 'generic_brand_777generic_devicev2/common'
action_topic = 'generic_brand_777/generic_device/v2/sub'

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
        pub_status = mqtt_client.publish(event_topic, payload, 2)
        if pub_status[0] == mqtt.MQTT_ERR_SUCCESS:
            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')
            print("{} Published : SensorID {}, Type {}, Rssi {}, Data {}".format(timestamp, dev_id, dev_type, dev_rssi, dev_data))
        else:
            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')
            print("{} ERROR : Unable to publish {}".format(timestamp, pub_status))
    except Exception as e:
        print(e)


def on_message(client, userdata, message):
    message_payload = str(message.payload.decode("utf-8"))
    print("message received " , message_payload)
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)

    #serial_com is passed as userdata before connection
    serial_com = userdata
    try:
        serial_com.write(bytes([0x01, 0x01, 0x01, 0x0A]))
    except serial.SerialTimeoutException:
        print("ERROR : Serial writing timeout")


def start_forwarder(com_port, baudrate = 115200, read_timeout_sec = 2, write_timeout_sec = 1):
    com = serial.Serial(com_port, baudrate, 8, 'N',
        1, read_timeout_sec, False, False, write_timeout_sec)

    client = mqtt.Client(client_name)
    client.username_pw_set(broker_user, broker_pass)
    client.user_data_set(com)
    client.connect(broker_hostname, broker_port)
    
    #action subscribe
    client.subscribe(action_topic)
    client.on_message = on_message
    client.loop_start()
    
    data = []
    while True:
        data = com.read_until(serial.LF)
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')
        if data == b'':
            continue

        if data[0] == 83:
            print("{} {}".format(timestamp, data.decode().replace('\n', '')))
            continue
        
        data = list(data)
        if len(data) < 4:
            print("{} ERR : Insufficient data : {}".format(timestamp, data))
            continue

        process_data(client, data)
