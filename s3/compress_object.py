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
import gzip
import optparse
import os
import sys


class Error(Exception):
    pass


def compress_file(name, out):
    """Compresses an existing file..
    """
    with open(name, 'rb') as i, gzip.open(out, 'wb') as o:
        o.writelines(i)


def upload_file(bucket, key, name):
    """Uploads an existing file to S3.
    """
    with bucket.new_key(key) as k:
        k.set_contents_from_filename(name)


def main():
    parser = optparse.OptionParser('Usage: %prog <args>...')
    (opts, args) = parser.parse_args()

    if 0 == len(args):
        parser.print_help()
        return 1

    try:
        s3 = boto.connect_s3()

        for a in args:
            if not a.startswith('s3://'):
                raise Error('unsupported object path!')
            parts = a[5:].split('/')
            b = parts[0]
            k = '/'.join(parts[1:]) if 1 < len(parts) else ''

            bucket = s3.get_bucket(b)
            key = bucket.get_key(k)
            _, name = os.path.split(key.name)
            key.get_contents_to_filename(name)

            out = name + '.gz'
            compress_file(name, out)
            os.remove(name)

            upload_file(bucket, key.name + '.gz', out)
            os.remove(out)
    except (Error, Exception), err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
