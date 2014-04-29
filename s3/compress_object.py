#!/usr/bin/env python
# Copyright (c) 2014 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Compresses an S3 object.

A simple tool to streamline compression of one or more S3 objects. Note
that a full path to an S3 object is required (e.g., s3://foo/bar).

Usage:
    ./compress_object.py <args>
"""

import boto.s3
import optparse
import sys


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog <args>...')
    (opts, args) = parser.parse_args()

    if 0 == len(args):
        parser.print_help()
        return 1

    try:
        s3 = boto.connect_s3()

        # TODO
    except (Error, Exception), err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
