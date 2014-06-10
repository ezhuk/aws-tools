#!/usr/bin/env python
# Copyright (c) 2014 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Cancels scheduled actions.

Allows to cancel all scheduled actions for the specified auto scaling group.

Usage:
    ./cancel_scheduled_actions.py <options>
"""

import boto.ec2.autoscale
import optparse
import sys


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog <options>')
    parser.add_option('-g', '--group', dest='group', help='The auto scaling '
        'group to cancel scheduled actions for (e.g., TEST).')
    (opts, args) = parser.parse_args()

    if 0 != len(args) or opts.group is None:
        parser.print_help()
        return 1

    try:
        c = boto.connect_autoscale()
        actions = c.get_all_scheduled_actions(as_group=opts.group)
        for a in actions:
            c.delete_scheduled_action(a, opts.group)
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

