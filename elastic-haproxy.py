#!/usr/bin/env python3

import boto3
import jinja2
import logging
import os
import subprocess
import sys
from multiprocessing import Process

HAPROXY_CFG = '/usr/local/etc/haproxy.cfg'


def get_haproxy_cfg_template():
    template = os.getenv('HAPROXY_CFG_TEMPLATE')

    if not template:
        sys.stderr.write('Missing HAPROXY_CFG_TEMPLATE environment variable\n')
        sys.exit(1)

    if template.startswith('/'):
        with open(template) as fd:
            template = fd.read()

    return template


def get_filters(val=None):
    '''
    >>> [sorted(x.items()) for x in get_filters('tag:Name=myinstance')]
    [[('Name', 'tag:Name'), ('Values', ['myinstance'])]]
    '''
    filters = list(filter(None, (val or os.getenv('BACKEND_INSTANCES_FILTERS', '')).split(',')))

    if not filters:
        sys.stderr.write('Missing BACKEND_INSTANCES_FILTERS environment variable\n')
        sys.exit(1)

    for filt in filters:
        name, _, values = filt.partition('=')
        yield {'Name': name, 'Values': values.split('|')}


def generate_haproxy_cfg(template):
    filters = list(get_filters())

    ec2 = boto3.client('ec2')

    servers = set()
    reservations = ec2.describe_instances(Filters=filters)['Reservations']
    for r in reservations:
        for i in r['Instances']:
            if 'PrivateIpAddress' in i:
                servers.add(i['PrivateIpAddress'])

    servers = sorted(servers)

    logging.info('Generating haproxy.cfg with %d servers..', len(servers))
    tpl = jinja2.Template(template)
    rendered_template = tpl.render(servers=servers)

    with open(HAPROXY_CFG + '.tmp', 'w') as fd:
        fd.write(rendered_template)
    os.rename(HAPROXY_CFG + '.tmp', HAPROXY_CFG)


def start_haproxy():
    logging.info('Starting HAProxy..')
    subprocess.check_call(['haproxy', '-f', HAPROXY_CFG])


def main():
    logging.basicConfig(level=logging.INFO)
    template = get_haproxy_cfg_template()

    generate_haproxy_cfg(template)
    proc = Process(target=start_haproxy)
    proc.start()
    proc.join()



if __name__ == '__main__':
    main()
