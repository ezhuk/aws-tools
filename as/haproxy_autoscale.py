#!/usr/bin/env python
# Copyright (c) 2013 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Updates haproxy configuration.

This tool updates backends section in haproxy configuration with a list
of currently running EC2 instances associated with a security group and
restarts it (zero downtime) if necessary.

Usage:
    ./haproxy_autoscale.py <options>
"""

import json
import optparse
import os
import re
import subprocess
import sys
import time


def get_running_instances(group):
    """Retrieves a list of currently running EC2 instances that belong
    to the specified security group.
    """
    proc = subprocess.Popen(['aws',
        'ec2',
        'describe-instances',
        '--filters','['
            '{"Name":"instance.group-id","Values":["' + group + '"]},'
            '{"Name":"instance-state-name","Values":["running"]}'
        ']'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        return set()

    instances = set()
    doc = json.loads(out)
    if 0 != len(doc['Reservations']):
        for node in doc['Reservations'][0]['Instances']:
            instances.add(node['PrivateDnsName'])

    return instances


def read_file(path):
    """Returns the content of an entire file.
    """
    with open(path) as f:
        return f.read()


def save_file(path, data):
    """Writes data into a file specified by its path.
    """
    with open(path, 'w') as f:
        for line in data:
            f.write(line)


def restart_haproxy(config):
    """Restarts haproxy with zero downtime.
    """
    pidfile = '/var/run/haproxy.pid'
    proc = subprocess.Popen(['/usr/sbin/haproxy',
        '-f', config,
        '-p', pidfile,
        '-sf', read_file(pidfile)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        return 1

    return 0


def main():
    parser = optparse.OptionParser('Usage: %prog <options>')
    parser.add_option('-c', '--config', dest='config', default='/etc/haproxy/haproxy.cfg',
        help='HAProxy configuration file to use.')
    parser.add_option('-g', '--group', dest='group',
        help='The ID of a security group.')
    (opts, args) = parser.parse_args()

    if opts.group is None:
        parser.print_help()
        return 1

    config = list()
    old = set()
    with open(opts.config) as f:
        for line in f:
            p = re.match(r'[^#](\s+)server(\s+)(\w+)(\s+)([^\s:]+)(.*)', line)
            if p:
                old.add(p.groups()[4])
            else:
                config.append(line)

    new = get_running_instances(opts.group)
    if sorted(new) != sorted(old):
        for pp, item in enumerate(new):
            config.append('    server app{0} {1} check\n'.format(pp, item))

        os.rename(opts.config, opts.config + time.strftime('.%Y%m%d%H%M%S', time.gmtime()))
        save_file(opts.config, config)
        restart_haproxy(opts.config)

    return 0


if __name__ == '__main__':
    sys.exit(main())
