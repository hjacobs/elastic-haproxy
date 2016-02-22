#!/usr/bin/env python3

import base64
import boto3
import jinja2
import logging
import os
import subprocess
import sys
import time
from multiprocessing import Process

HAPROXY_CFG = '/usr/local/etc/haproxy.cfg'
HAPROXY_PID = '/var/run/haproxy.pid'


def get_haproxy_cfg_template():
    raw_template = os.getenv('HAPROXY_CFG_TEMPLATE')

    if not raw_template:
        sys.stderr.write('Missing HAPROXY_CFG_TEMPLATE environment variable\n')
        sys.exit(1)

    if raw_template.startswith('/'):
        with open(raw_template) as fd:
            template = fd.read()
    else:
        template = base64.b64decode(raw_template).decode('utf-8')

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

    logging.info('Rendering HAProxy configuration with %d servers..', len(servers))
    tpl = jinja2.Template(template)
    rendered_template = tpl.render(servers=servers)

    try:
        with open(HAPROXY_CFG) as fd:
            current_config = fd.read()
    except:
        current_config = None

    if current_config != rendered_template:
        logging.info('Writing new HAProxy configuration to haproxy.cfg..')
        with open(HAPROXY_CFG + '.tmp', 'w') as fd:
            fd.write(rendered_template)
        os.rename(HAPROXY_CFG + '.tmp', HAPROXY_CFG)
        return True
    else:
        return False


def start_haproxy():
    logging.info('Starting HAProxy..')
    subprocess.check_call(['haproxy', '-D', '-f', HAPROXY_CFG, '-p', HAPROXY_PID])


def reload_haproxy():
    logging.info('Reloading HAProxy..')
    with open(HAPROXY_PID) as fd:
        pid = fd.read().strip()
    subprocess.check_call(['haproxy', '-D', '-f', HAPROXY_CFG, '-p', HAPROXY_PID, '-sf', pid])


def run_background_job(template):
    delay = int(os.getenv('UPDATE_INTERVAL', 30))
    while True:
        try:
            time.sleep(delay)
            if generate_haproxy_cfg(template):
                reload_haproxy()
        except Exception as e:
            logging.exception('Error while running update: {}'.format(e))


def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('botocore.vendored.requests.packages.urllib3').setLevel(logging.WARN)
    template = get_haproxy_cfg_template()

    generate_haproxy_cfg(template)
    haproxy = Process(target=start_haproxy)
    haproxy.start()
    job = Process(target=run_background_job, args=(template, ))
    job.start()

    for proc in (haproxy, job):
        proc.join(5)


if __name__ == '__main__':
    main()
