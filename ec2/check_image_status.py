#!/usr/bin/env python
# Copyright (c) 2014 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Checks AMI status.

Displays the current status of one or more AMIs.

Usage:
    ./check_image_status.py <options>
"""

import boto.ec2
import optparse
import sys


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog [options]')
    parser.add_option('-i', '--image', dest='images', action='append',
        help='One or more AMI IDs to check the status for.')
    (opts, args) = parser.parse_args()

    if 0 != len(args) or opts.images is None:
        parser.print_help()
        return 1

    try:
        c = boto.connect_ec2()
        images = c.get_all_images(image_ids=opts.images)
        if not images:
            raise Error('could not find \'{0}\''.format(opts.images))

        for i in images:
            print '{0}: {1}'.format(i.id, i.state)
    except (Error, Exception), err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

