#!/usr/bin/env python
# Copyright (c) 2013 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

import optparse
import subprocess
import sys


def create_launch_configuration(options):
    proc = subprocess.Popen(['aws',
        'autoscaling',
        'create-launch-configuration',
        '--launch-configuration-name', options['launch_config'],
        '--image-id', options['image'],
        '--key-name', options['key'],
        '--security-groups', options['group'],
        '--instance-type', options['type']],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        return 1

    return 0


def create_auto_scaling_group(options):
    proc = subprocess.Popen(['aws',
        'autoscaling',
        'create-auto-scaling-group',
        '--auto-scaling-group-name', options['auto_scaling_group'],
        '--launch-configuration-name', options['launch_config'],
        '--min-size', options['min'],
        '--max-size', options['max'],
        '--availability-zones', options['zone'],
        '--load-balancer-names', options['load_balancer']],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        return 1

    return 0


def main():
    parser = optparse.OptionParser('Usage: %prog <name> [options]')
    parser.add_option('-i', '--image', dest='image', default='ami-a43909e1',
        help='The Amazon  Machine  Image (AMI) ID that will be used to launch '
             'EC2 instances. The most recent Amazon Linux AMI 2013.09.2 (ami-'
             'a43909e1) is used by default.')
    parser.add_option('-t', '--type', dest='type', default='t1.micro',
        help='The type of the Amazon EC2 instance. Micro instance (t1.micro) '
             'is used by default.')
    parser.add_option('-k', '--key', dest='key',
        help='The name of the key pair to use when creating EC2 instances.')
    parser.add_option('-g', '--group', dest='group',
        help='The security groups to use when creating EC2 instances.')
    parser.add_option('-m', '--min', dest='min', default='2', help='')
    parser.add_option('-M', '--max', dest='max', default='4', help='')
    parser.add_option('-z', '--zone', dest='zone', help='')
    parser.add_option('-l', '--load-balancer', dest='load_balancer', help='')
    (opts, args) = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        return 1

    options = vars(opts)
    options['name'] = args[0]
    options['launch_config'] = options['name'] + '-LC'
    options['auto_scaling_group'] = options['name'] + '-ASG'

    print options

    if create_launch_configuration(options):
        print '[ERROR] could not create launch configuration'
        return 1

    if create_auto_scaling_group(options):
        print '[ERROR] could not create auto scaling group'
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
