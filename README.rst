=========================
HAProxy Appliance for AWS
=========================

.. code-block:: bash

    $ openssl req -x509 -nodes -newkey rsa:2048 -keyout key.pem -out cert.pem -days 300
    $ cat cert.pem key.pem > haproxy-example.pem
    $ sudo pip3 install scm-source && scm-source
    $ docker build -t elastic-haproxy .
    $ docker run -it -p 8443:443 -p 9090:9090 -v $HOME/.aws:/root/.aws -e AWS_REGION=eu-central-1 -e UPDATE_INTERVAL=3 -e BACKEND_INSTANCES_FILTERS=tag:StackName=mystack -e "HAPROXY_CFG_TEMPLATE=$(cat haproxy_template.cfg | base64)" -e "HAPROXY_PEM=$(cat haproxy-example.pem | base64)" elastic-haproxy


Configuration
=============

The following environment variables are supported:

``AWS_REGION``
    Optional AWS region ID. You don't need to specify this as it's loaded from the EC2 meta data service.
``HAPROXY_CFG_TEMPLATE``
    Filename of haproxy.cfg Jinja2_ template or base64 encoded template string.
``BACKEND_INSTANCES_FILTERS``
    Comma separated list of filters to find EC2 instances, e.g. ``tag:StackName=mystack`` would find all EC2 instances with a tag "StackName" with value "mystack".
``UPDATE_INTERVAL``
    Update interval in seconds, i.e. how often to query the AWS EC2 API.

.. _Jinja2: http://jinja.pocoo.org/
