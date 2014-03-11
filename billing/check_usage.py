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
import boto.route53
import boto.s3
import boto.sns
import boto.sqs
import csv
import itertools
import optparse
import re
import sys
import time


class Error(Exception):
    pass


def get_ec2_usage():
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


def get_as_usage():
    autoscale = boto.connect_autoscale()
    print '{0} Auto Scaling Groups\n' \
        '{1} Launch Configurations\n' \
        '{2} Auto Scaling Policies' \
        .format(len(autoscale.get_all_groups()), \
            len(autoscale.get_all_launch_configurations()), \
            len(autoscale.get_all_policies()))


def get_sns_usage():
    sns = boto.connect_sns()
    print '{0} Topics\n' \
        '{1} Subscriptions' \
        .format(len(sns.get_all_topics()), \
            len(sns.get_all_subscriptions()))


def get_sqs_usage():
    sqs = boto.connect_sqs()
    print '{0} Queues'.format(len(sqs.get_all_queues()))


def get_cw_usage():
    cw = boto.connect_cloudwatch()
    print '{0} Alarms'.format(len(cw.describe_alarms()))


def get_r53_usage():
    r53 = boto.connect_route53()
    print '{0} Hosted Zones'.format(len(r53.get_all_hosted_zones()))


def get_elb_usage():
    elb = boto.connect_elb()
    print '{0} Elastic Load Balancers' \
        .format(len(elb.get_all_load_balancers()))


def get_s3_usage():
    s3 = boto.connect_s3()
    buckets = s3.get_all_buckets()
    res = sum([k.size for k in itertools.chain.from_iterable( \
        [b.get_all_keys() for b in buckets])])
    print '{0:.3f} GB in {1} S3 Buckets' \
        .format(res / float(1024 * 1024 * 1024), \
                len(buckets))


def get_aws_cost(bucket_name, time_period):
    s3 = boto.connect_s3()
    bucket = s3.lookup(bucket_name)
    if bucket is None:
        raise Error('could not find \'{0}\''.format(bucket_name))

    period = time_period if time_period is not None \
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
        get_ec2_usage()
        get_as_usage()
        get_sns_usage()
        get_sqs_usage()
        get_cw_usage()
        get_r53_usage()
        get_elb_usage()
        get_s3_usage()

        get_aws_cost(opts.bucket, opts.period)
    except (Error, Exception), err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
