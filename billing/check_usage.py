#!/usr/bin/env python
# Copyright (c) 2014 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Checks AWS usage.

This script retrieves and displays an estimated total statement amount for
the specified billing period.

Usage:
    ./check_usage.py [options]
"""

import boto.ec2
import boto.s3
import csv
import optparse
import re
import sys
import time


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog [options]')
    parser.add_option('-b', '--bucket', dest='bucket',
        help='The name of the S3 bucket that holds billing reports. This '
             'option is required.')
    parser.add_option('-p', '--period', dest='period',
        help='The billing period to check the usage for (e.g., \'2014-02\' '
             'without quotes). Defaults to the current billing period if '
             'not specified.')
    (opts, args) = parser.parse_args()

    if len(args) != 0 or \
       opts.bucket is None:
        parser.print_help()
        return 1

    try:
        ec2 = boto.connect_ec2()

        print '{0} Elastic IP Addresses\n' \
            '{1} Instances\n' \
            '{2} Reserved Instances\n' \
            '{3} Spot Instance Requests\n' \
            '{4} Volumes\n' \
            '{5} Snapshots\n' \
            '{6} Images\n' \
            '{7} Security Groups\n' \
            '{8} Key Pairs' \
            .format(len(ec2.get_all_addresses()), \
                    len(ec2.get_all_reservations()), \
                    len(ec2.get_all_reserved_instances()), \
                    len(ec2.get_all_spot_instance_requests()), \
                    len(ec2.get_all_volumes()), \
                    len(ec2.get_all_snapshots(owner=['self'])), \
                    len(ec2.get_all_images(owners=['self'])), \
                    len(ec2.get_all_security_groups()), \
                    len(ec2.get_all_key_pairs()))

        s3 = boto.connect_s3()

        bucket = s3.lookup(opts.bucket)
        if bucket is None:
            raise Error('could not find \'{0}\''.format(opts.bucket))

        period = opts.period if opts.period is not None \
            else time.strftime('%Y-%m', time.gmtime())

        data = ''
        for key in bucket.list():
            p = re.match(r'(\w+)-aws-billing-csv-{0}.csv' \
                .format(period), key.name)
            if p:
                data = key.get_contents_as_string()
                break
        if not data:
            raise Error('could not find billing data for this month')

        doc = csv.reader(data.rstrip('\n').split('\n'), delimiter=',')
        for row in doc:
            if row[3] == 'StatementTotal':
                print 'Cost: {0} {1}\nCredit: {2} {3}\nTotal: {4} {5}' \
                    .format(row[24], row[23], \
                            row[25], row[23], \
                            row[28], row[23])
    except (Error, Exception), err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
