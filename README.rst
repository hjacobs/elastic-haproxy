=========================
HAProxy Appliance for AWS
=========================

.. code-block:: bash

    $ openssl req -x509 -nodes -newkey rsa:2048 -keyout key.pem -out cert.pem -days 300
    $ cat cert.pem key.pem > haproxy-example.pem
    $ docker run -it -p 8443:443 -v $HOME/.aws:/root/.aws -e BACKEND_INSTANCES_FILTERS=tag:StackName=mystack -e "HAPROXY_CFG_TEMPLATE=$(cat haproxy_template.cfg)" -v $(pwd)/haproxy-example.pem:/haproxy.pem test
