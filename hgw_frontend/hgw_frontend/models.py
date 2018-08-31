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


from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from oauth2_provider.models import AbstractApplication

from hgw_common.utils import generate_id
from hgw_frontend.settings import REQUEST_VALIDITY_SECONDS, DEFAULT_SCOPES


class FlowRequest(models.Model):
    PENDING = 'PE'
    ACTIVE = 'AC'
    DELETE_REQUESTED = 'DR'

    STATUS_CHOICES = (
        (PENDING, 'PENDING'),
        (ACTIVE, 'ACTIVE'),
        (DELETE_REQUESTED, 'DELETE_REQUIRED')
    )

    flow_id = models.CharField(max_length=32, blank=False)
    process_id = models.CharField(max_length=32, blank=False)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, blank=False, default=PENDING)
    person_id = models.CharField(max_length=20, blank=True, null=True)
    profile = models.ForeignKey('hgw_common.Profile', on_delete=models.CASCADE, null=True)
    destination = models.ForeignKey('Destination')
    start_validity = models.DateTimeField(null=False)
    expire_validity = models.DateTimeField(null=False)


def get_validity():
    return timezone.now() + timedelta(seconds=REQUEST_VALIDITY_SECONDS)


def get_confirmation_code():
    return get_random_string(32)


class ConfirmationCode(models.Model):
    flow_request = models.ForeignKey('FlowRequest', on_delete=models.CASCADE)
    code = models.CharField(max_length=32, blank=False, null=False, unique=True, default=get_confirmation_code)
    validity = models.DateTimeField(default=get_validity)

    def check_validity(self):
        return timezone.now() < self.validity


class ConsentConfirmation(models.Model):
    flow_request = models.ForeignKey('FlowRequest', on_delete=models.CASCADE)
    consent_id = models.CharField(max_length=32, blank=False, null=False, unique=True)
    confirmation_id = models.CharField(max_length=32, blank=False, null=False)
    destination_endpoint_callback_url = models.CharField(max_length=100, blank=False, null=False)


class HGWFrontendUser(AbstractUser):
    fiscalNumber = models.CharField(max_length=16, blank=True, null=True)


class Destination(models.Model):
    KAFKA = 'K'
    REST = 'R'

    destination_id = models.CharField(max_length=32, default=generate_id, null=True, unique=True)
    rest_or_kafka = models.CharField(max_length=1, default='K', blank=False, null=False,
                                     choices=((KAFKA, 'REST'), (REST, 'KAFKA')))
    name = models.CharField(max_length=30, null=False, blank=False, unique=True)
    kafka_public_key = models.TextField(max_length=500, null=True, help_text="Public key in PEM format")

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()


class RESTClient(AbstractApplication):

    STANDARD = 'ST'
    SUPER = 'SU'

    ROLE_CHOICES = (
        ('ST', STANDARD),
        ('SU', SUPER)
    )

    destination = models.OneToOneField('Destination', null=True, blank=True)
    client_role = models.CharField(max_length=2, choices=ROLE_CHOICES, null=False, blank=False, default=STANDARD)
    scopes = models.CharField(max_length=100, blank=False, null=False, default=" ".join(DEFAULT_SCOPES),
                              help_text="Space separated scopes to assign to the REST client")

    def is_super_client(self):
        return self.client_role == self.SUPER

    def has_scope(self, scope):
        return scope in self.scopes
