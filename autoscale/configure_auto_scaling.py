#!/usr/bin/env python
# Copyright (c) 2013 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Configures AWS Auto Scaling.

This script is intended to simplify the process of setting up AWS Auto
Scaling to automatically manage system capacity based on average CPU
usage of running instances.

Usage:
    ./configure_auto_scaling.py [options]
"""

import boto.ec2.autoscale
import boto.ec2.cloudwatch
import optparse
import sys

from boto.ec2.autoscale import LaunchConfiguration
from boto.ec2.autoscale import AutoScalingGroup
from boto.ec2.autoscale import ScalingPolicy
from boto.ec2.cloudwatch import MetricAlarm

import autoscale_settings as s


class Error(Exception):
    pass


class Defaults(object):
    """Default settings.
    """
    IMAGE = 'ami-a8d3d4ed'
    TYPE = 't1.micro'
    MIN_INSTANCES = 2
    MAX_INSTANCES = 4
    MIN_THRESHOLD = 40
    MAX_THRESHOLD = 60
    ADJUSTMENT = 1
    PERIOD = 300


def _create_launch_configuration(c, opts):
    lc = LaunchConfiguration(name=opts.name + s.LAUNCH_CONFIG_SUFFIX,
            image_id=opts.image,
            key_name=opts.key,
            security_groups=[opts.group],
            instance_type=opts.type)
    c.create_launch_configuration(lc)
    return lc


def _create_autoscaling_group(c, lc, opts):
    g = AutoScalingGroup(name=opts.name + s.GROUP_SUFFIX,
            launch_config=lc,
            availability_zones=opts.zones,
            load_balancers=opts.lbs,
            min_size=opts.min,
            max_size=opts.max)
    c.create_auto_scaling_group(g)
    return g


def main():
    parser = optparse.OptionParser('Usage: %prog [options]')
    parser.add_option('-n', '--name', dest='name',
        help='The name of this configuration (e.g., TEST).')
    parser.add_option('-i', '--image', dest='image', default=Defaults.IMAGE,
        help='The Amazon  Machine  Image (AMI) ID that will be used to launch '
             'EC2 instances. The most recent Amazon Linux AMI 2013.09.2 (ami-'
             'a43909e1) is used by default.')
    parser.add_option('-t', '--type', dest='type', default=Defaults.TYPE,
        help='The type of the Amazon EC2 instance. If not specified, micro '
             'instance (t1.micro) type will be used.')
    parser.add_option('-k', '--key', dest='key',
        help='The name of the key pair to use when creating EC2 instances. '
             'This options is required.')
    parser.add_option('-g', '--group', dest='group',
        help='Security group that will be used when creating EC2 instances. '
             'This option is required.')
    parser.add_option('-m', '--min', dest='min', default=Defaults.MIN_INSTANCES,
        help='The minimum number of EC2 instances in the auto scaling group. '
             'By default it is set to 2.')
    parser.add_option('-M', '--max', dest='max', default=Defaults.MAX_INSTANCES,
        help='The maximum size of the auto scaling group. By default it is '
             'set to 4.')
    parser.add_option('-z', '--zone', dest='zones', action='append',
        help='The availability zone for the auto scaling group. This option '
             'is required.')
    parser.add_option('-l', '--load-balancer', dest='lbs', action='append',
        help='The name of an existing AWS load balancer to use, if any.')
    parser.add_option('--min-threshold', dest='min_threshold',
        default=Defaults.MIN_THRESHOLD, help='The minimum CPU utilization '
        'threshold that triggers an alarm. This option is not required and '
        'is set to 40% by default.')
    parser.add_option('--max-threshold', dest='max_threshold',
        default=Defaults.MAX_THRESHOLD, help='The maximum CPU utilization '
        'threshold that triggers an alarm. This option is not required and '
        'is set to 60% by default.')
    parser.add_option('-a', '--adjustment', dest='adjustment',
        default=Defaults.ADJUSTMENT, help='The number of EC2 instances by '
        'which to scale up or down. This is set to 1 by default.')
    parser.add_option('-p', '--period', dest='period', default=Defaults.PERIOD,
        help='The evaluation period in seconds. This is optional and is set '
             'to 300 seconds by default.')
    (opts, args) = parser.parse_args()

    if (0 != len(args) or
        opts.name is None or
        opts.key is None or
        opts.group is None or
        opts.zones is None):
        parser.print_help()
        return 1

    try:
        c = boto.connect_autoscale()

        lc = _create_launch_configuration(c, opts)
        g = _create_autoscaling_group(c, lc, opts)

        policy_up = ScalingPolicy(name=opts.name + s.POLICY_UP_SUFFIX,
            as_name=g.name,
            scaling_adjustment=opts.adjustment,
            adjustment_type='ChangeInCapacity')
        c.create_scaling_policy(policy_up)

        cloudwatch = boto.connect_cloudwatch()

        alarm_high = MetricAlarm(name=opts.name + s.ALARM_HIGH_SUFFIX,
            alarm_actions=[policy_up],
            metric='CPUUtilization',
            namespace='AWS/EC2',
            statistic='Average',
            dimensions={'AutoScalingGroupName': g.name},
            period=opts.period,
            evaluation_periods=1,
            threshold=int(opts.max_threshold),
            comparison='>')
        cloudwatch.create_alarm(alarm_high)

        policy_down = ScalingPolicy(name=opts.name + s.POLICY_DOWN_SUFFIX,
            as_name=g.name,
            scaling_adjustment=-opts.adjustment,
            adjustment_type='ChangeInCapacity')
        autoscale.create_scaling_policy(policy_down)

        alarm_low = MetricAlarm(name=opts.name + s.ALARM_LOW_SUFFIX,
            alarm_actions=[policy_down],
            metric='CPUUtilization',
            namespace='AWS/EC2',
            statistic='Average',
            dimensions={'AutoScalingGroupName': g.name},
            period=opts.period,
            evaluation_periods=1,
            threshold=int(opts.min_threshold),
            comparison='<')
        cloudwatch.create_alarm(alarm_low)
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

