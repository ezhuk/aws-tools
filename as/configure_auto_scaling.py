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

import boto.ec2.autoscale
import boto.ec2.cloudwatch
import json
import optparse
import subprocess
import sys
from boto.ec2.autoscale import LaunchConfiguration
from boto.ec2.autoscale import AutoScalingGroup
from boto.ec2.autoscale import ScalingPolicy
from boto.ec2.cloudwatch import MetricAlarm


class Error(Exception):
    pass


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
    parser.add_option('--min-threshold', dest='min_threshold', default='40',
        help='The minimum CPU utilization threshold that triggers an alarm. '
             'This option is not required and is set to 60% by default.')
    parser.add_option('--max-threshold', dest='max_threshold', default='60',
        help='The maximum CPU utilization threshold that triggers an alarm. '
             'This option is not required and is set to 40% by default.')
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
    options['auto_scaling_group'] = options['name'] + '-ASG'

    try:
        autoscale = boto.ec2.autoscale.connect_to_region('us-west-1')

        lc = LaunchConfiguration(name=options['name'] + '-LC',
            image_id=options['image'],
            key_name=options['key'],
            security_groups=[options['group']],
            instance_type=options['type'])
        autoscale.create_launch_configuration(lc)

        asg = AutoScalingGroup(name=options['auto_scaling_group'],
            launch_config=lc,
            availability_zones=[options['zone']],
            load_balancers=[options['load_balancer']],
            min_size=options['min'],
            max_size=options['max'])
        autoscale.create_auto_scaling_group(asg)

        pu = ScalingPolicy(name=options['name'] + '-SP-UP',
            as_name=name=options['auto_scaling_group'],
            scaling_adjustment=1,
            adjustment_type='ChangeInCapacity')
        autoscale.create_scaling_policy(pu)

        cloudwatch = boto.ec2.cloudwatch.connect_to_region('us-west-1')

        ah = MetricAlarm(name=options['name'] + '-MA-CPU-HIGH',
            alarm_actions=[pu],
            metric='CPUUtilization',
            namespace='AWS/EC2',
            statistic='Average',
            dimensions={'AutoScalingGroupName': options['auto_scaling_group']},
            period=300,
            evaluation_periods=1,
            threshold=int(options['max_threshold']),
            comparison='>')
        cloudwatch.create_alarm(ah)

        pd = ScalingPolicy(name=options['name'] + '-SP-DOWN',
            as_name=name=options['auto_scaling_group'],
            scaling_adjustment=-1,
            adjustment_type='ChangeInCapacity')
        autoscale.create_scaling_policy(pd)

        al = MetricAlarm(name=options['name'] + '-MA-CPU-LOW',
            alarm_actions=[pd],
            metric='CPUUtilization',
            namespace='AWS/EC2',
            statistic='Average',
            dimensions={'AutoScalingGroupName': options['auto_scaling_group']},
            period=300,
            evaluation_periods=1,
            threshold=int(options['min_threshold']),
            comparison='<')
        cloudwatch.create_alarm(al)
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
