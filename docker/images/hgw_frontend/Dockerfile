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


FROM crs4/web_base:latest
LABEL maintainer="Vittorio Meloni <vittorio.meloni@crs4.it>"


ARG HTTP_PORT=8000

ENV DJANGO_APP_NAME=hgw_frontend
ENV HTTP_PORT=${HTTP_PORT}


COPY resources/docker-entrypoint.sh /custom_entrypoint/
COPY resources/launch-source-notification-consumer.sh /
COPY resources/launch-connector-notification-consumer.sh /
COPY resources/launch-consent-notification-consumer.sh /
COPY service/ /container/service/

RUN chmod +x /custom_entrypoint/docker-entrypoint.sh
RUN chmod +x /launch-source-notification-consumer.sh
RUN chmod +x /launch-connector-notification-consumer.sh
RUN chmod +x /launch-consent-notification-consumer.sh

EXPOSE ${HTTP_PORT}
