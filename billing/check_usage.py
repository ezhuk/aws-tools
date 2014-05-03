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

import boto.cloudfront
import boto.dynamodb2
import boto.ec2
import boto.ec2.autoscale
import boto.ec2.cloudwatch
import boto.elasticache
import boto.emr
import boto.glacier
import boto.iam
import boto.kinesis
import boto.opsworks
import boto.rds2
import boto.redshift
import boto.route53
import boto.s3
import boto.sns
import boto.sdb
import boto.sqs
import boto.vpc
import csv
import itertools
import optparse
import re
import sys
import time

from boto.ec2.cloudwatch import MetricAlarm


class Error(Exception):
    pass


def connect_to_regions(service, regions):
    if regions is not None:
        return [service.connect_to_region(r.name) for r in service.regions() \
            if r.name in regions]
    else:
        return [service.connect_to_region(r.name) for r in service.regions() \
            if not (r.name.startswith('cn-') or r.name.startswith('us-gov-'))]


def get_ec2_usage(regions):
    cs = connect_to_regions(boto.ec2, regions)
    instances = list(itertools.chain.from_iterable([x.instances \
        for c in cs for x in c.get_all_reservations()]))
    running = sum(16 == i.state_code for i in instances)
    volumes = list(itertools.chain.from_iterable([c.get_all_volumes() \
        for c in cs]))
    size = sum(v.size for v in volumes)
    addresses = list(itertools.chain.from_iterable([c.get_all_addresses() \
        for c in cs]))
    unassigned = sum(a.instance_id is None for a in addresses)
    print '{0} EC2 Instance(s){1}\n' \
        '{2} EC2 Reserved Instance(s)\n' \
        '{3} EC2 Spot Instance Request(s)\n' \
        '{4} EBS Volume(s){5}\n' \
        '{6} EBS Snapshot(s)\n' \
        '{7} Amazon Machine Image(s)\n' \
        '{8} Network Interface(s)\n' \
        '{9} Elastic IP Address(es){10}\n' \
        '{11} Security Group(s)\n' \
        '{12} Key Pair(s)\n' \
        '{13} Tag(s)' \
        .format(len(instances), \
            '[{0} running]'.format(running) if 0 != running else '', \
            sum(len(c.get_all_reserved_instances()) for c in cs), \
            sum(len(c.get_all_spot_instance_requests()) for c in cs), \
            len(volumes), \
            '[{0} GB]'.format(size) if 0 != size else '', \
            sum(len(c.get_all_snapshots(owner=['self'])) for c in cs), \
            sum(len(c.get_all_images(owners=['self'])) for c in cs), \
            sum(len(c.get_all_network_interfaces()) for c in cs), \
            len(addresses), \
            '[{0} unassigned]'.format(unassigned) if 0 != unassigned else '', \
            sum(len(c.get_all_security_groups()) for c in cs), \
            sum(len(c.get_all_key_pairs()) for c in cs), \
            sum(len(c.get_all_tags()) for c in cs))


def get_autoscale_usage(regions):
    cs = connect_to_regions(boto.ec2.autoscale, regions)
    print '{0} Auto Scaling Group(s)\n' \
        '{1} Auto Scaling Launch Configuration(s)\n' \
        '{2} Auto Scaling Policie(s)' \
        .format(sum(len(c.get_all_groups()) for c in cs), \
            sum(len(c.get_all_launch_configurations()) for c in cs), \
            sum(len(c.get_all_policies()) for c in cs))


def get_elb_usage(regions):
    cs = connect_to_regions(boto.ec2.elb, regions)
    print '{0} Elastic Load Balancer(s)' \
        .format(sum(len(c.get_all_load_balancers()) for c in cs))


def get_vpc_usage(regions):
    cs = connect_to_regions(boto.vpc, regions)
    vpcs = list(itertools.chain.from_iterable([c.get_all_vpcs() for c in cs]))
    print '{0} Virtual Private Cloud(s) [{1} default]\n' \
        '{2} Internet Gateway(s)\n' \
        '{3} Customer Gateway(s)\n' \
        '{4} VPN Gateway(s)\n' \
        '{5} Subnet(s)' \
        .format(len(vpcs), \
            sum(v.is_default for v in vpcs), \
            sum(len(c.get_all_internet_gateways()) for c in cs), \
            sum(len(c.get_all_customer_gateways()) for c in cs), \
            sum(len(c.get_all_vpn_gateways()) for c in cs), \
            sum(len(c.get_all_subnets()) for c in cs))


def get_route53_usage():
    r53 = boto.connect_route53()
    zones = r53.get_zones()
    records = sum(len(z.get_records()) for z in zones)
    print '{0} Route53 Hosted Zone(s) [{1} record(s)]' \
        .format(len(zones), records)


def get_s3_usage():
    s3 = boto.connect_s3()
    buckets = s3.get_all_buckets()
    res = sum([k.size for k in itertools.chain.from_iterable( \
        [b.get_all_keys() for b in buckets])])
    print '{0} S3 Bucket(s) [{1:.3f} GB]' \
        .format(len(buckets), res / float(1024 * 1024 * 1024))


def get_glacier_usage():
    gc = boto.connect_glacier()
    print '{0} Glacier Vault(s)' \
        .format(len(gc.list_vaults()))


def get_cloudfront_usage():
    cf = boto.connect_cloudfront()
    ds = cf.get_all_distributions()
    os = len(list(itertools.chain.from_iterable( \
        [x.get_distribution().get_objects() for x in ds])))
    print '{0} CloudFront Distribution(s){1}' \
        .format(len(ds), ' [{0} object(s)]'.format(os) if 0 != os else '')


def get_sdb_usage(regions):
    cs = connect_to_regions(boto.sdb, regions)
    print '{0} SimpleDB Domain(s)' \
        .format(sum(len(c.get_all_domains()) for c in cs))


def get_rds_usage(regions):
    cs = connect_to_regions(boto.rds2, regions)
    print '{0} RDS Instance(s)\n' \
        '{1} RDS Reserved Instance(s)\n' \
        '{2} RDS Snapshot(s)' \
        .format(sum(len(c.describe_db_instances() \
                ['DescribeDBInstancesResponse'] \
                ['DescribeDBInstancesResult'] \
                ['DBInstances']) for c in cs),
            sum(len(c.describe_reserved_db_instances() \
                ['DescribeReservedDBInstancesResponse'] \
                ['DescribeReservedDBInstancesResult'] \
                ['ReservedDBInstances']) for c in cs),
            sum(len(c.describe_db_snapshots() \
                ['DescribeDBSnapshotsResponse'] \
                ['DescribeDBSnapshotsResult'] \
                ['DBSnapshots']) for c in cs))


def get_dynamodb_usage(regions):
    cs = connect_to_regions(boto.dynamodb2, regions)
    print '{0} DynamoDB Table(s)' \
        .format(sum(len(c.list_tables() \
                ['TableNames']) for c in cs))


def get_elasticache_usage(regions):
    cs = connect_to_regions(boto.elasticache, regions)
    clusters = list(itertools.chain.from_iterable( \
        [c.describe_cache_clusters() \
            ['DescribeCacheClustersResponse'] \
            ['DescribeCacheClustersResult'] \
            ['CacheClusters'] for c in cs]))
    print '{0} ElastiCache Cluster(s)' \
        .format(len(clusters))


def get_redshift_usage(regions):
    cs = connect_to_regions(boto.redshift, regions)
    clusters = list(itertools.chain.from_iterable( \
        [c.describe_clusters() \
            ['DescribeClustersResponse'] \
            ['DescribeClustersResult'] \
            ['Clusters'] for c in cs]))
    print '{0} Redshift Cluster(s)' \
        .format(len(clusters))


def get_emr_usage(regions):
    cs = connect_to_regions(boto.emr, regions)
    clusters = list(itertools.chain.from_iterable( \
        [[c.describe_cluster(s.id)] for c in cs \
        for s in c.list_clusters().clusters]))
    print '{0} EMR Cluster(s)' \
        .format(len(clusters))


def get_kinesis_usage(regions):
    cs = connect_to_regions(boto.kinesis, regions)
    streams = list(itertools.chain.from_iterable( \
        [c.list_streams()['StreamNames'] for c in cs]))
    shards = sum(len(c.describe_stream(s) \
        ['StreamDescription'] \
        ['Shards']) for c in cs for s in streams)
    print '{0} Kinesis Stream(s){1}' \
        .format(len(streams), \
            '[{0} shard(s)]'.format(shards) if 0 != shards else '')


def get_sns_usage(regions):
    cs = connect_to_regions(boto.sns, regions)
    print '{0} SNS Topic(s)\n' \
        '{1} SNS Subscription(s)\n' \
        '{2} SNS Platform Application(s)' \
        .format(sum(len(c.get_all_topics() \
                ['ListTopicsResponse'] \
                ['ListTopicsResult'] \
                ['Topics']) for c in cs),
            sum(len(c.get_all_subscriptions() \
                ['ListSubscriptionsResponse'] \
                ['ListSubscriptionsResult'] \
                ['Subscriptions']) for c in cs), \
            sum(len(c.list_platform_applications() \
                ['ListPlatformApplicationsResponse'] \
                ['ListPlatformApplicationsResult'] \
                ['PlatformApplications']) for c in cs))


def get_sqs_usage(regions):
    cs = connect_to_regions(boto.sqs, regions)
    queues = list(itertools.chain.from_iterable( \
        [c.get_all_queues() for c in cs]))
    messages = sum(q.count() for q in queues)
    print '{0} SQS Queue(s){1}' \
        .format(len(queues), \
            '[{0} message(s)]'.format(messages) if 0 != messages else '')


def get_iam_usage(regions):
    cs = connect_to_regions(boto.iam, regions)
    users = list(itertools.chain.from_iterable([c.get_all_users() \
        ['list_users_response'] \
        ['list_users_result'] \
        ['users'] for c in cs]))
    groups = list(itertools.chain.from_iterable([c.get_all_groups() \
        ['list_groups_response'] \
        ['list_groups_result'] \
        ['groups'] for c in cs]))
    print '{0} IAM User(s)\n' \
        '{1} IAM Group(s)' \
        .format(len(users), len(groups))


def get_cloudwatch_usage(regions):
    cs = connect_to_regions(boto.ec2.cloudwatch, regions)
    alarms = list(itertools.chain.from_iterable( \
        [c.describe_alarms() for c in cs]))
    triggered = sum(a.state_value == MetricAlarm.ALARM for a in alarms)
    print '{0} CloudWatch Alarm(s){1}' \
        .format(len(alarms), \
            '[{0} triggered]'.format(triggered) if 0 != triggered else '')


def get_opsworks_usage():
    ow = boto.connect_opsworks()
    print '{0} OpsWorks Stack(s)' \
        .format(len(ow.describe_stacks()['Stacks']))


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

    cost = dict()
    total = list()

    doc = csv.reader(data.rstrip('\n').split('\n'), delimiter=',')
    for row in doc:
        code = row[12]
        if code and code != 'ProductCode':
            value = float(row[28])
            if value >= 0:
                if not code in cost:
                    cost[code] = [row[13].split(' ', 1)[1], value, row[23]]
                else:
                    cost[code][1] += value
        if row[3] == 'StatementTotal':
            total.extend([['Cost', float(row[24]), row[23]], \
                ['Credit', float(row[25]), row[23]], \
                ['Total', float(row[28]), row[23]]])

    print '---'
    for k, v in cost.items():
        print '{0:<30} {1:>8.2f} {2}'.format(v[0], v[1], v[2])
    for v in total:
        print '{0:>29}: {1:>8.2f} {2}'.format(v[0], v[1], v[2])


def main():
    parser = optparse.OptionParser('Usage: %prog [options]')
    parser.add_option('-b', '--bucket', dest='bucket',
        help='The name of the S3 bucket that holds billing reports. This '
             'option is required.')
    parser.add_option('-p', '--period', dest='period',
        help='The billing period to check the usage for (e.g., \'2014-02\' '
             'without quotes). Defaults to the current billing period if '
             'not specified.')
    parser.add_option('-r', '--region', dest='regions', action='append',
        help='The name of the region to usage for.')
    (opts, args) = parser.parse_args()

    if len(args) != 0 or \
       opts.bucket is None:
        parser.print_help()
        return 1

    try:
        get_ec2_usage(opts.regions)
        get_autoscale_usage(opts.regions)
        get_elb_usage(opts.regions)
        get_vpc_usage(opts.regions)
        get_route53_usage()

        get_s3_usage()
        get_glacier_usage()
        get_cloudfront_usage()

        get_sdb_usage(opts.regions)
        get_rds_usage(opts.regions)
        get_dynamodb_usage(opts.regions)
        get_elasticache_usage(opts.regions)
        get_redshift_usage(opts.regions)

        get_emr_usage(opts.regions)
        get_kinesis_usage(opts.regions)

        get_sns_usage(opts.regions)
        get_sqs_usage(opts.regions)

        get_cloudwatch_usage(opts.regions)
        get_opsworks_usage()
        get_iam_usage(opts.regions)

        get_aws_cost(opts.bucket, opts.period)
    except (Error, Exception), err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
