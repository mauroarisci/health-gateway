# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import json
import logging
from json.decoder import JSONDecodeError
from traceback import format_exc

from django.conf import settings
from kafka import KafkaProducer
from kafka.errors import (KafkaError, KafkaTimeoutError, NoBrokersAvailable,
                          TopicAuthorizationFailedError)

from hgw_common.messaging import (SendingError, SerializationError,
                                  UnknownSender)
from hgw_common.messaging.serializer import JSONSerializer

# from hgw_common.utils import get_logger

level = logging.DEBUG
logger = logging.getLogger('sender')
fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handlers = [logging.StreamHandler()]

class GenericSender():
    """
    Generic sender abstract class. Subclass should implement the
    real notification process
    """

    def send(self, message):
        """
        Abstract send method. Subclasses should implement this
        """
        raise NotImplementedError


class KafkaConfig(object):
    def __init__(self, config: dict):
        self.config = config

        super(KafkaConfig, self).__init__()


class KafkaSender(GenericSender):
    """
    A sender that publish updates in a kafka topic

    :param topic: the topic where to publish the messages
    :param config: a dict with the configuration parameters for the KafkaProducer. Refer to kafka-python
        module
    """

    def __init__(self, topic: str, config: dict, serializer: type):
        self.topic = topic
        self.config = config
        self.producer = None
        self.serializer = serializer()
        super(KafkaSender, self).__init__()

    def _create_producer(self):
        try:
            if self.producer is None:
                self.producer = KafkaProducer(**self.config)
        except NoBrokersAvailable:
            raise SendingError('Cannot connect to kafka broker')

    def send(self, message):
        try:
            self._create_producer()
        except SendingError:
            logger.error('Error connecting to Kafka')
            return False

        try:
            future = self.producer.send(self.topic, value=self.serializer.serialize(message))
        except KafkaTimeoutError:
            logger.error('Cannot get topic %s metadata. Probably the token does not exist', self.topic)
            return False
        except SerializationError:
            return False

        # Block for 'synchronous' sends
        try:
            future.get(timeout=2)
        except TopicAuthorizationFailedError:
            logger.debug('Missing write permission to write in topic %s', self.topic)
            return False
        except KafkaError:
            logger.debug('An error occurred sending message to topic %s. Error details %s', self.topic, format_exc())
            # Decide what to do if producer request failed...
            return False
        else:
            return True

    def send_async(self, message):
        try:
            self._create_producer()
        except SendingError:
            return False

        try:
            self.producer.send(self.topic, self.serializer.serialize(message))
        except SerializationError:
            return False


def create_sender(name):
    """
    Methods that returns the correct sender based on the settings file
    """
    if settings.NOTIFICATION_TYPE == 'kafka':
        kafka_config = {
            'bootstrap_servers': settings.KAFKA_BROKER,
            'security_protocol': 'SSL' if hasattr(settings, 'KAFKA_SSL') and settings.KAFKA_SSL else 'PLAINTEXT',
            'ssl_check_hostname': True,
            'ssl_cafile': settings.KAFKA_CA_CERT if hasattr(settings, 'KAFKA_SSL') and settings.KAFKA_SSL else None,
            'ssl_certfile': settings.KAFKA_CLIENT_CERT if hasattr(settings, 'KAFKA_SSL') and settings.KAFKA_SSL else None,
            'ssl_keyfile': settings.KAFKA_CLIENT_KEY if hasattr(settings, 'KAFKA_SSL') and settings.KAFKA_SSL else None
        }

        return KafkaSender(name, kafka_config, JSONSerializer)

    raise UnknownSender("Cannot instantiate a sender")
