import requests
from utilities import wait_for_internet_connection, clean_fields, get_default_gateway_interface_linux, get_ip_address
#import thingspeak # Source: https://github.com/mchwalisz/thingspeak/
import logging
import struct
import math
import json
import paho.mqtt.client as mqttClient


logger = logging.getLogger('HoneyPi.mqtt')

def publish_all_mqtt_topics(mqtt_data, mqtt_server, offline, debug):
    try:
        defaultgatewayinterface = get_default_gateway_interface_linux()
        if defaultgatewayinterface == None:
            logger.error('No default gateway, MQTT publish upload will end in error!')
            defaultgatewayinterfaceip = ""
        else:
            defaultgatewayinterfaceip = get_ip_address(str(defaultgatewayinterface))
            if defaultgatewayinterfaceip == None:
                defaultgatewayinterfaceip = ""
        connectionErrorWithinAnyChannel = []
        client = mqttClient.Client()
        client.connect(mqtt_server.get("server_url"))
        client.loop_start()
        for (key, value) in mqtt_data.items():
            logger.debug('Topic ' + str(key) + ' with value ' + str(value) + ' transfer with source IP ' + defaultgatewayinterfaceip + ' using default gateway on ' + str(defaultgatewayinterface))
            connectionError = publish_single_topic(key, value, client, debug)
            connectionErrorWithinAnyChannel.append(connectionError)
        client.loop_stop()
        client.disconnect()
        return any(c == True for c in connectionErrorWithinAnyChannel)
    except Exception as ex:
        logger.exception("Exception in publish_all_mqtt_topics")

def publish_single_topic(topic, value, client, debug):
    # do-while to retry failed transfer
    retries = 0
    MAX_RETRIES = 3
    isConnectionError = True
    logger.info("Start of publish_single_topic")
    while isConnectionError:
        try:
            # convert_lorawan(ts_fields_cleaned)
            msg_info = client.publish(topic, value, qos=1)
            if msg_info.is_published() == False:
                msg_info.wait_for_publish()                    
            if debug:
                logger.debug("Data succesfully transfered to MQTT. " + response)
            else:
                logger.info("Data succesfully transfered to MQTT.")
            # break because transfer succeded
            isConnectionError = False
            break
        except Exception as ex:
            logger.error('Error: Exception while sending Data '+ repr(ex))
        finally:
            if isConnectionError:
                retries+=1
                # Break after 3 retries
                if retries > MAX_RETRIES:
                    break
                logger.warning("Waiting 15 seconds for internet connection to try transfer again (" + str(retries) + "/" + str(MAX_RETRIES) + ")...")
                wait_for_internet_connection(15)
                client.reconnect()

    return isConnectionError