#!/usr/bin/env python
# Copyright (c) 2014 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Deletes messages from a queue.

A simple script to purge all messages from the given SQS queue.

Usage:
    ./delete_messages.py <options>
"""

import boto.sqs
import optparse
import sys


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog <options>')
    parser.add_option('-q', '--queue', dest='queue', help='The SQS queue '
        'to delete messages from.')
    (opts, args) = parser.parse_args()

    if 0 != len(args) or opts.queue is None:
        parser.print_help()
        return 1

    try:
        c = boto.connect_sqs()
        queue = c.get_queue(opts.queue)
        queue.clear()
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

