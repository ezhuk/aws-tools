#!/usr/bin/env python
# Copyright (c) 2014 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Checks AWS usage.

TODO

Usage:
    ./check_usage.py [options]
"""

import boto.s3
import optparse
import re
import sys
import time


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog [options]')
    parser.add_option('-b', '--bucket', dest="bucket",
        help='The name of the S3 bucket that holds billing reports.')
    (opts, args) = parser.parse_args()

    if len(args) != 0 or \
       opts.bucket is None:
        parser.print_help()
        return 1

    try:
        s3 = boto.connect_s3()

        bucket = s3.lookup(opts.bucket)
        if bucket is None:
            raise Error('could not find \'{0}\''.format(opts.bucket))

        for key in bucket.list():
            p = re.match(r'(\w+)-aws-billing-csv-{0}.csv' \
                .format(time.strftime('%Y-%m', time.gmtime())), key.name)
            if p:
                print key.name

    except (Error, Exception), err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
