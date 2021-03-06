from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from hgw_common.utils.authorization import TokenHasResourceDetailedScope
from hgw_frontend.models import Channel, ConsentConfirmation, FlowRequest
from hgw_frontend.serializers import ChannelSerializer


class ChannelView(ViewSet):
    permission_classes = (TokenHasResourceDetailedScope,)
    required_scopes = ['flow_request']

    @staticmethod
    def list(request):
        if request.auth.application.is_super_client():
            channels = Channel.objects.all()
        else:
            channels = Channel.objects.filter(flow_request__in=FlowRequest.objects.filter(destination=request.auth.application.destination))

        if 'status' in request.GET:
            if request.GET['status'] not in list(zip(*Channel.STATUS_CHOICES))[0]:
                return Response(request.data, status=status.HTTP_400_BAD_REQUEST)
            channels = channels.filter(status=request.GET['status'])
        serializer = ChannelSerializer(channels, many=True)
        return Response(serializer.data, headers={'X-Total-Count': channels.count()})

    @staticmethod
    def retrieve(request, channel_id):
        try:
            if request.auth.application.is_super_client():
                channel = Channel.objects.get(channel_id=channel_id)
            else:
                channel = Channel.objects.get(channel_id=channel_id,
                                              flow_request__in=FlowRequest.objects.filter(destination=request.auth.application.destination))
        except Channel.DoesNotExist:
            raise Http404
        serializer = ChannelSerializer(channel)
        return Response(serializer.data)

    @staticmethod
    def search(request):
        """
        REST function to search Channels. The only search parameter is consent_id
        """
        if 'consent_id' in request.GET:
            try:
                if request.auth.application.is_super_client():
                    consent_confirmation = ConsentConfirmation.objects.get(consent_id=request.GET['consent_id'])
                else:
                    flow_requests = FlowRequest.objects.filter(destination=request.auth.application.destination)
                    consent_confirmation = ConsentConfirmation.objects.get(consent_id=request.GET['consent_id'],
                                                                           flow_request__in=flow_requests)
                channel = consent_confirmation.channel
                serializer = ChannelSerializer(instance=channel)
            except ConsentConfirmation.DoesNotExist:
                raise Http404
            return Response(serializer.data, headers={'X-Total-Count': '1'})
        else:
            return Response({'errors': ['missing_parameter']}, status.HTTP_400_BAD_REQUEST)
