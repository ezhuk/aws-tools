#!/usr/bin/env python
# Copyright (c) 2013 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Shuts down AWS Auto Scaling.

This allows for easy shutdown of previously created AWS Auto Scaling
configuration.

Usage:
    ./shutdown_auto_scaling.py <options>
"""

import boto.ec2.autoscale
import boto.ec2.cloudwatch
import optparse
import sys
import time


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog <options>')
    parser.add_option('-n', '--name', dest='name',
        help='The name of the configuration to shutdown (e.g., TEST).')
    (opts, args) = parser.parse_args()

    if len(args) != 0:
        parser.print_help()
        return 1

    if opts.name is None:
        parser.print_help()
        return 1

    try:
        autoscale = boto.connect_autoscale()

        group_name = opts.name + '-ASG'
        groups = autoscale.get_all_groups(names=[group_name])
        if len(groups) != 1:
            raise Error('could not find \'{0}\''.format(group_name))

        group = groups[0]
        group.min_size = 0
        group.max_size = 0
        group.desired_capacity = 0
        group.update()

        group.shutdown_instances()
        while True:
            group = autoscale.get_all_groups(names=[group_name])[0]
            if not group.instances:
                break
            time.sleep(1)

        autoscale.delete_policy(opts.name + '-SP-UP')
        autoscale.delete_policy(opts.name + '-SP-DOWN')
        autoscale.delete_auto_scaling_group(group_name)
        autoscale.delete_launch_configuration(opts.name + '-LC')

        cloudwatch = boto.connect_cloudwatch()

        cloudwatch.delete_alarms([opts.name + '-MA-CPU-HIGH', \
            opts.name + '-MA-CPU-LOW'])
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
