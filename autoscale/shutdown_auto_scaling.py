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

import autoscale_settings as s


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog <options>')
    parser.add_option('-n', '--name', dest='name',
        help='The name of the configuration to shutdown (e.g., TEST).')
    (opts, args) = parser.parse_args()

    if 0 != len(args) or opts.name is None:
        parser.print_help()
        return 1

    try:
        c = boto.connect_autoscale()

        group_name = opts.name + s.GROUP_SUFFIX
        gs = c.get_all_groups(names=[group_name])
        if len(gs) != 1:
            raise Error('could not find \'{0}\''.format(group_name))

        g = gs[0]
        g.min_size = 0
        g.max_size = 0
        g.desired_capacity = 0
        g.update()

        g.shutdown_instances()
        while True:
            g = c.get_all_groups(names=[group_name])[0]
            if not g.instances:
                break
            time.sleep(1)

        c.delete_policy(opts.name + s.POLICY_UP_SUFFIX)
        c.delete_policy(opts.name + s.POLICY_DOWN_SUFFIX)
        c.delete_auto_scaling_group(group_name)
        c.delete_launch_configuration(opts.name + s.LAUNCH_CONFIG_SUFFIX)

        cw = boto.connect_cloudwatch()
        cw.delete_alarms([opts.name + s.ALARM_HIGH_SUFFIX,
            opts.name + s.ALARM_LOW_SUFFIX])
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

