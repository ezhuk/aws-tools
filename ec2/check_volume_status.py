#!/usr/bin/env python
# Copyright (c) 2014 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Checks EBS Volume status.

Displays the current status of one or more EBS Volumes.

Usage:
    ./check_volume_status.py <options>
"""

import boto.ec2
import optparse
import sys


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog [options]')
    parser.add_option('-v', '--volume', dest='volumes', action='append',
        help='One or more EBS Volumes to check the status for.')
    (opts, args) = parser.parse_args()

    if 0 != len(args) or opts.volumes is None:
        parser.print_help()
        return 1

    try:
        c = boto.connect_ec2()
        volumes = c.get_all_volumes(volume_ids=opts.volumes)
        if not volumes:
            raise Error('could not find \'{0}\''.format(opts.volumes))

        for v in volumes:
            print '{0}: {1}'.format(v.id, v.status)
    except (Error, Exception), err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

