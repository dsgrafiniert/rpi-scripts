import requests
from utilities import wait_for_internet_connection, clean_fields, get_default_gateway_interface_linux, get_ip_address
#import thingspeak # Source: https://github.com/mchwalisz/thingspeak/
import logging
import struct
import math
import json
import paho.mqtt.client as mqttClient


logger = logging.getLogger('HoneyPi.thingspeak')

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
        client.connect(mqtt_server["server_url"])
        
        for (topic_index, topic) in enumerate(mqtt_data, 0):
            topic_id = topic["ts_channel_id"]
            if topic_id:
                logger.info('Topic ' + str(topic_index) + ' with ID ' + str(topic_id) + ' transfer with source IP ' + defaultgatewayinterfaceip + ' using default gateway on ' + str(defaultgatewayinterface))
                    connectionError = publish_single_topic(topic, client, debug)
                    connectionErrorWithinAnyChannel.append(connectionError)
            else:
                logger.warning("No MQTT publish for this topic (" + str(topic_index) + ") because because topic_id is None.")

        client.disconnect()
        return any(c == True for c in connectionErrorWithinAnyChannel)
    except Exception as ex:
        logger.exception("Exception in publish_all_mqtt_topics")

def publish_single_topic(topic, client, debug):
    # do-while to retry failed transfer
    retries = 0
    MAX_RETRIES = 3
    isConnectionError = True
    logger.debug("Start of publish_single_topic")
    while isConnectionError:
        try:
            # convert_lorawan(ts_fields_cleaned)
            msg_info = client.publish(topic.channel, topic.message, qos=1)
                            if msg_info.is_published() == False:
                                    msg_info.wait_for_publish()
                                    
                                    
            if debug:
                logger.debug("Data succesfully transfered to ThingSpeak. " + response)
            else:
                logger.info("Data succesfully transfered to ThingSpeak.")
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

def thingspeak_update(write_key, data, server_url='https://api.thingspeak.com', ts_datetime=None, timeout=15, fmt='json'):
    """Update channel feed.

    Full reference:
    https://mathworks.com/help/thingspeak/update-channel-feed.html
    """
    logger.debug("Start of thingspeak_update")
    if write_key is not None:
        data['api_key'] = write_key
    if ts_datetime is not None:
        data['created_at'] = ts_datetime
    url = '{ts}/update.{fmt}'.format(
        ts=server_url,
        fmt=fmt,
    )
    logger.debug("Start of post request")
    response = requests.post(url, params=data, timeout=timeout)
    response.raise_for_status()
    logger.debug("End of post request")
    if fmt == 'json':
        return json.dumps(response.json())
    else:
        return response.text
