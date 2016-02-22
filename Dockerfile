FROM haproxy:1.6.3

EXPOSE 443

RUN apt-get update && apt-get install -y --no-install-recommends python3-pip && \
    pip3 install boto3 jinja2

CMD /elastic-haproxy.py

COPY elastic-haproxy.py /
