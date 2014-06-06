#!/usr/bin/env python
# Copyright (c) 2014 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Checks AWS EBS Snapshot status.

This script displays the current status of one or more AWS EBS snapshots.

Usage:
    ./check_snapshot_status.py [options]
"""

import boto.ec2
import optparse
import sys
import time


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog [options]')
    parser.add_option('-s', '--snapshot', dest='snapshots', action='append',
        help='The snapshot ID(s) to check status for. This option is required.')
    (opts, args) = parser.parse_args()

    if 0 != len(args) or opts.snapshots is None:
        parser.print_help()
        return 1

    try:
        ec2 = boto.connect_ec2()

        while True:
            snapshots = ec2.get_all_snapshots(snapshot_ids=opts.snapshots)
            if not snapshots:
                raise Error('could not find \'{0}\''.format(opts.snapshots))

            for snap in snapshots:
                print '{0}: [{1}{2}] {3}'.format(snap.id,
                    '#' * 4 * (int(snap.progress.strip('%')) / 10),
                    ' ' * 4 * ((100 - int(snap.progress.strip('%'))) / 10),
                    snap.progress)

            if all(snap.status != 'pending' for snap in snapshots):
                break

            size = len(snapshots)
            if (1 < size):
                sys.stdout.write('\x1b[1A' * size)

            time.sleep(3)
    except (Error, Exception), err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

