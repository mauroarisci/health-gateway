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


from django.http import Http404, HttpResponse
from kafka import KafkaProducer, TopicPartition
from kafka.errors import NoBrokersAvailable
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from hgw_backend.settings import KAFKA_BROKER, KAFKA_CA_CERT, KAFKA_CLIENT_KEY, KAFKA_CLIENT_CERT
from hgw_common.cipher import Cipher, is_encrypted
from hgw_common.utils import TokenHasResourceDetailedScope
from .models import Source
from .serializers import SourceSerializer


def home(request):
    return HttpResponse('<a href="/admin/">Click here to access admin page</a>')


class SourcesList(APIView):

    def get_object(self, source_id):
        try:
            return Source.objects.get(source_id=source_id)
        except Source.DoesNotExist:
            raise Http404

    def get(self, request, source_id=None, format=None):
        if source_id:
            source = self.get_object(source_id)
            serializer = SourceSerializer(source)
        else:
            sources = Source.objects.all()
            serializer = SourceSerializer(sources, many=True)
        return Response(serializer.data, content_type='application/json')


class Messages(APIView):
    permission_classes = (TokenHasResourceDetailedScope,)
    required_scopes = ['messages']

    @staticmethod
    def _get_kafka_producer():
        kp = KafkaProducer(bootstrap_servers=KAFKA_BROKER,
                           security_protocol='SSL',
                           ssl_check_hostname=True,
                           ssl_cafile=KAFKA_CA_CERT,
                           ssl_certfile=KAFKA_CLIENT_CERT,
                           ssl_keyfile=KAFKA_CLIENT_KEY)

        return kp

    @staticmethod
    def _get_kafka_topic(request):
        return request.auth.application.source.source_id

    def post(self, request):
        if 'channel_id' not in request.data or 'payload' not in request.data:
            return Response({'error': 'missing_parameters'}, status.HTTP_400_BAD_REQUEST)
        payload = request.data['payload'].encode('utf-8')

        if not is_encrypted(payload):
            return Response({'error': 'not_encrypted_payload'}, status.HTTP_400_BAD_REQUEST)

        channel_id = request.data['channel_id'].encode('utf-8')
        try:
            kp = self._get_kafka_producer()
        except NoBrokersAvailable:
            return Response({'error': 'cannot_send_message'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            topic = self._get_kafka_topic(request)
            kp.send(topic, channel_id, payload)

        return Response({}, 200)

