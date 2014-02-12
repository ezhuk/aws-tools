#!/usr/bin/env python
# Copyright (c) 2014 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Checks AWS EBS Snapshot status.

This script displays the current status of an AWS EBS snapshot.

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
    parser.add_option('-s', '--snapshot', dest='snapshot', help='The snapshot'
        'ID to check status for. This option is required.')
    (opts, args) = parser.parse_args()

    if len(args) != 0:
        parser.print_help()
        return 1

    if opts.snapshot is None:
        parser.print_help()
        return 1

    try:
        ec2 = boto.connect_ec2()

        while True:
            snapshot = ec2.get_all_snapshots(snapshot_ids=[opts.snapshot])[0]
            if not snapshot:
                raise Error('could not find \'{0}\''.format(opts.snapshot))

            print '\r{0}: [{1}{2}] {3}'.format(snapshot.id, \
                '#' * 4 * (int(snapshot.progress.strip('%')) / 10), \
                ' ' * 4 * ((100 - int(snapshot.progress.strip('%'))) / 10), \
                snapshot.progress)

            if snapshot.status != 'pending':
                break

            time.sleep(3)

    except (Error, Exception), err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
