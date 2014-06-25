#!/usr/bin/env python
# Copyright (c) 2014 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Checks EC2 Instance status.

Displays the current status of one or more EC2 Instances.

Usage:
    ./check_instance_status.py <options>
"""

import boto.ec2
import itertools
import optparse
import sys


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog [options]')
    parser.add_option('-i', '--instance', dest='instances', action='append',
        help='One or more EC2 Instances to check the status for.')
    (opts, args) = parser.parse_args()

    if 0 != len(args) or opts.instances is None:
        parser.print_help()
        return 1

    try:
        c = boto.connect_ec2()
        instances = list(itertools.chain.from_iterable(r.instances
            for r in c.get_all_reservations()))
        if not instances:
            raise Error('could not find \'{0}\''.format(opts.instances))

        for i in instances:
            print '{0}: {1}'.format(i.id, i.state)
    except (Error, Exception), err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1


if __name__ == '__main__':
    sys.exit(main())

