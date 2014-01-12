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
    for node in doc['Reservations'][0]['Instances']:
        instances.add(node['PrivateDnsName'])

    return instances


def restart_haproxy(config):
    """Restarts haproxy with zero downtime.
    """
    pidfile = '/var/run/haproxy.pid'
    f = open(pidfile)
    data = f.read()
    f.close()

    proc = subprocess.Popen(['/usr/sbin/haproxy',
        '-f', config,
        '-p', pidfile,
        '-sf', data],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        return 1

    return 0


def main():
    parser = optparse.OptionParser('Usage: %prog <options>')
    parser.add_option('-c', '--config', dest='config', default='haproxy.cfg',
        help='HAProxy configuration file to use.')
    parser.add_option('-g', '--group', dest='group',
        help='The ID of a security group.')
    (opts, args) = parser.parse_args()

    if opts.group is None:
        parser.print_help()
        return 1

    instances = get_running_instances(opts.group)
    if 0 != len(instances):
        src = open(opts.config)
#        dst = open(opts.config + '.tmp', 'w')
        for line in src:
            p = re.match(r'[^#](\s+)server(\s+)(\w+)(\s+)([^\s:]+)(.*)', line)
#            if p:
#                TODO
#            else:
#                dst.write(line)

#        os.rename(opts.config + '.tmp', opts.config)
#        restart_aproxy(opts.config)

    return 0


if __name__ == '__main__':
    sys.exit(main())
