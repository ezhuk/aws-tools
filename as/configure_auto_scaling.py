#!/usr/bin/env python
# Copyright (c) 2013 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Configures AWS Auto Scaling.

This script is intended to simplify the process of setting up AWS Auto
Scaling to automatically manage system capacity based on average CPU
usage of running instances.

Usage:
    ./configure_auto_scaling.py <name> [options]
"""

import json
import optparse
import subprocess
import sys


def create_launch_configuration(options):
    """Creates a new launch configuration.

    The launch configuration name must be unique and the total number
    of created configurations must be less than the maximum limit which
    is set to 100 by default.

    Args:
        A dictionary that specifies necessary configuration options.

    Returns:
        The status code that is set to 0 on success and 1 otherwise.
    """
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
    """Creates a new auto scaling group.

    The auto scaling group name must be unique and the specified launch
    configuration and load balancer must be created.

    Args:
        A dictionary that specifies necessary configuration options.

    Returns:
        The status code that is set to 0 on success and 1 otherwise.
    """
    proc = subprocess.Popen(['aws',
        'autoscaling',
        'create-auto-scaling-group',
        '--auto-scaling-group-name', options['auto_scaling_group'],
        '--launch-configuration-name', options['launch_config'],
        '--min-size', options['min'],
        '--max-size', options['max'],
        '--availability-zones', options['zone']],
        '--load-balancer-names', options['load_balancer']],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        return 1

    return 0


def create_scaling_policy(options):
    """Creates a new scaling policy.

    The specified auto scaling group the newly created policy will be
    associated with must exist.

    Args:
        A dictionary that specifies necessary configuration options.

    Returns:
        Name of the newly created scaling policy on success or an empty
        string otherwise.
    """
    proc = subprocess.Popen(['aws',
        'autoscaling',
        'put-scaling-policy',
        '--auto-scaling-group-name', options['auto_scaling_group'],
        '--policy-name', options['name'],
        '--scaling-adjustment', options['adjustment'],
        '--adjustment-type', 'ChangeInCapacity'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        return ''

    doc = json.loads(out)
    return doc['PolicyARN']


def create_metric_alarm(options):
    """Creates a new metric alarm.

    The specified auto scaling group and action the newly created alarm
    will be associated with must exist.

    Args:
        A dictionary that specifies necessary configuration options.

    Returns:
        The status code that is set to 0 on success and 1 otherwise.
    """
    proc = subprocess.Popen(['aws',
        'cloudwatch',
        'put-metric-alarm',
        '--alarm-name', options['name'],
        '--alarm-actions', options['action'],
        '--metric-name', 'CPUUtilization',
        '--namespace', 'AWS/EC2',
        '--statistic', 'Average',
        '--dimensions', '[{"Name":"AutoScalingGroupName","Value":"' + options['auto_scaling_group'] + '"}]',
        '--period', '300',
        '--evaluation-periods', '1',
        '--threshold', options['threshold'],
        '--comparison-operator', options['operator']],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        print out
        print err
        return 1

    return 0


def main():
    parser = optparse.OptionParser('Usage: %prog <name> [options]')
    parser.add_option('-i', '--image', dest='image', default='ami-a43909e1',
        help='The Amazon  Machine  Image (AMI) ID that will be used to launch '
             'EC2 instances. The most recent Amazon Linux AMI 2013.09.2 (ami-'
             'a43909e1) is used by default.')
    parser.add_option('-t', '--type', dest='type', default='t1.micro',
        help='The type of the Amazon EC2 instance. If not specified, micro '
             'instance (t1.micro) type will be used.')
    parser.add_option('-k', '--key', dest='key',
        help='The name of the key pair to use when creating EC2 instances. '
             'This options is required.')
    parser.add_option('-g', '--group', dest='group',
        help='Security group that will be used when creating EC2 instances. '
             'This option is required.')
    parser.add_option('-m', '--min', dest='min', default='2',
        help='The minimum number of EC2 instances in the auto scaling group. '
             'If not specified, 2 will be used.')
    parser.add_option('-M', '--max', dest='max', default='4',
        help='The maximum size of the auto scaling group. By default it is '
             'set to 4.')
    parser.add_option('-z', '--zone', dest='zone',
        help='The availability zone for the auto scaling group. This option '
             'is required.')
    parser.add_option('-l', '--load-balancer', dest='load_balancer',
        help='The name of an existing AWS load balancer to use, if any.')
    (opts, args) = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        return 1

    if opts.key is None or \
       opts.group is None or \
       opts.zone is None:
        parser.print_help()
        return 1

    options = vars(opts)
    options['name'] = args[0]
    options['launch_config'] = options['name'] + '-LC'
    options['auto_scaling_group'] = options['name'] + '-ASG'

    if create_launch_configuration(options):
        print '[ERROR] could not create launch configuration'
        return 1

    if create_auto_scaling_group(options):
        print '[ERROR] could not create auto scaling group'
        return 1

    policy_options = {
        'auto_scaling_group': options['auto_scaling_group'],
        'name': options['name'] + '-SP-UP',
        'adjustment': '1'
    }
    arn = create_scaling_policy(policy_options)
    if not arn:
        print '[ERROR] could not create scaling policy'
        return 1

    alarm_options = {
        'auto_scaling_group': options['auto_scaling_group'],
        'name': options['name'] + '-MA-CPU-HIGH',
        'action': arn,
        'threshold': '60',
        'operator': 'GreaterThanThreshold'
    }
    if create_metric_alarm(alarm_options):
        print '[ERROR] could not create metric alarm'
        return 1

    policy_options = {
        'auto_scaling_group': options['auto_scaling_group'],
        'name': options['name'] + '-SP-DOWN',
        'adjustment': '-1'
    }
    arn = create_scaling_policy(policy_options)
    if not arn:
        print '[ERROR] could not create scaling policy'
        return 1

    alarm_options = {
        'auto_scaling_group': options['auto_scaling_group'],
        'name': options['name'] + '-MA-CPU-LOW',
        'action': arn,
        'threshold': '40',
        'operator': 'LessThanThreshold'
    }
    if create_metric_alarm(alarm_options):
        print '[ERROR] could not create metric alarm'
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
