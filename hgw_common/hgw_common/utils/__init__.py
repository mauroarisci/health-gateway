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

import yaml
from django.conf import settings
from django.db import DatabaseError
from django.http import Http404
from django.utils.crypto import get_random_string
from kafka import KafkaConsumer, TopicPartition
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import exception_handler


def create_broker_parameters_from_settings():
    """
    Function to create broker parameters from django settings
    """
    parameters = {
        'broker_type': settings.NOTIFICATION_TYPE,
    }
    if settings.NOTIFICATION_TYPE == 'kafka':
        parameters.update({
            'broker_url': settings.KAFKA_BROKER,
            'ssl': hasattr(settings, 'KAFKA_SSL') and settings.KAFKA_SSL,
            'ca_cert': settings.KAFKA_CA_CERT if hasattr(settings, 'KAFKA_SSL') and settings.KAFKA_SSL else None,
            'client_cert': settings.KAFKA_CLIENT_CERT if hasattr(settings, 'KAFKA_SSL') and settings.KAFKA_SSL else None,
            'client_key': settings.KAFKA_CLIENT_KEY if hasattr(settings, 'KAFKA_SSL') and settings.KAFKA_SSL else None,
        })
    return parameters


def generate_id():
    """
    Generates a random string of 32 characters to be used as an id for objects
    """
    return get_random_string(32)


def get_oauth_token(server_uri, client_id, client_secret):
    """
    Obtains an OAuth2 token from :param:`server_uri` using :param:`client_id` and
    :param:`client_secret` as authentication parameters
    """
    client = BackendApplicationClient(client_id)
    oauth_session = OAuth2Session(client=client)
    token_url = '{}/oauth2/token/'.format(server_uri)
    access_token = oauth_session.fetch_token(token_url=token_url, client_id=client_id,
                                             client_secret=client_secret)

    access_token = access_token["access_token"]
    access_token_header = {"Authorization": "Bearer {}".format(access_token)}
    return oauth_session, access_token_header


class ERRORS:
    MISSING_PARAMETERS = 'missing_parameters'
    FORBIDDEN = 'forbidden'
    NOT_AUTHENTICATED = 'not_authenticated'
    NOT_FOUND = 'not_found'
    DUPLICATED = 'duplicated'
    DB_ERROR = 'database_error'


def custom_exception_handler(exc, context):
    """
    Configures the Django Rest Framework return messages
    """
    if isinstance(exc, DatabaseError):
        response = Response({'errors': [ERRORS.DB_ERROR]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif isinstance(exc, Http404):
        response = Response({'errors': [ERRORS.NOT_FOUND]}, status=status.HTTP_404_NOT_FOUND)
    elif isinstance(exc, NotAuthenticated):
        response = Response({'errors': [ERRORS.NOT_AUTHENTICATED]}, status=status.HTTP_401_UNAUTHORIZED)
    elif isinstance(exc, PermissionDenied):
        response = Response({'errors': [ERRORS.FORBIDDEN]}, status=status.HTTP_403_FORBIDDEN)
    else:
        response = exception_handler(exc, context)

    return response
