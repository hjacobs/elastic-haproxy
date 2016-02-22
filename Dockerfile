FROM haproxy:1.6.3

EXPOSE 443

RUN apt-get update && apt-get install -y --no-install-recommends python3-pip && \
    pip3 install boto3 jinja2

# allow us to write the config even when not running as root
RUN chmod 777 /usr/local/etc/haproxy

CMD /elastic-haproxy.py

COPY elastic-haproxy.py /

COPY scm-source.json /
