#!/usr/bin/env python

"""
This is a python script that handles communication between a gateway and mqtt.
"""

import paho.mqtt.client as mqtt
import serial
import io
import signal
import sys

from config_file import get_conf

# conf file file default path
conf_file_path = 'serial-to-mqtt.conf'

# callback functions
def on_connect(client, userdata, flags, rc):
    print('connected with result: ' + str(rc))
    print(f"Suscribe to DHN/{str(userdata['network id'])}/#")
    #subscribe whenever connecting or reconnecting 
    client.subscribe("DHN/" + str(userdata['network id']) + "/#")


def on_message(client, userdata, msg):
    spTopic = msg.topic.split("/")
    
    # topic that the web server subscribe 
    topic = "DHN/OUT/" + '/'.join(spTopic[1:2])
    
    # Try to publish if not, print out the error
    try:
        client.publish(topic, msg.payload,1)
    except:
        print(topic)
        print(msg.payload)

    print(f"Sending from on message {topic}/{msg.payload}")
# signal handler for ctrl-c


def signal_handler(signal, frame):
    print("Ending Program.....")
    sys.exit(0)


def main():

    # exit gracefully if sigint is received
    signal.signal(signal.SIGINT, signal_handler)

    # get consts from the config file
    with open(conf_file_path, 'r') as conf_file:
        config = get_conf(conf_file)
        conf_file.close()

    # Serial Comms Setup

    # setup the serial port based on the config file
    gateway_ser = serial.Serial()
    gateway_ser.baudrate = config['baudrate']
    gateway_ser.timeout = None  # set blocking

    # check to see if the user inputed a serial port
    if len(sys.argv) == 2:
        gateway_ser.port = sys.argv[1]
    else:
        gateway_ser.port = config['serial port']

    # attempt to open the serial port
    try:
        gateway_ser.open()
    except serial.SerialException:
        print('could not find serial port: ' + gateway_ser.port)
        sys.exit(1)

    # MQTT Setup
    server_ip = config['server ip']
    server_port = config['server port']
    client_id = config['client id']

    client = mqtt.Client(client_id)

    # set the user data to the open and working serial port
    userdata = dict()
    userdata['serial'] = gateway_ser
    userdata['network id'] = 0  # TODO get from the gateway
    client.user_data_set(userdata)

    # set the callback functions
    client.on_connect = on_connect
    client.on_message = on_message

    # start the connection
    client.connect(server_ip, server_port)

    # start the thread for processing incoming data
    client.loop_start()

    # TODO get the network ID from the gateway
    network_id = 0

    pub_topic_prefix = "DHN/" + str(network_id)
    # main loop
    while True:

        # block waiting for a message from the gateway in Serial    
        topic = gateway_ser.readline()
        topic = topic.decode()

        # clean up the message
        topic = topic.strip()
        topic= topic.split('/')

        payload = '/'.join(topic[2:])
        
        print(f"Sending {'/'.join(topic[0:2])}/{payload}")
        
        try:
            client.publish('/'.join(topic[0:2]), payload,1)
        except:
            print(topic)
            print(payload)

    # stop the thread
    client.loop_stop()


if __name__ == '__main__':
    main()
