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

import boto.beanstalk
import boto.cloudfront
import boto.cloudsearch2
import boto.cloudtrail
import boto.datapipeline
import boto.dynamodb2
import boto.ec2
import boto.ec2.autoscale
import boto.ec2.cloudwatch
import boto.elasticache
import boto.elastictranscoder
import boto.emr
import boto.glacier
import boto.iam
import boto.kinesis
import boto.opsworks
import boto.rds2
import boto.redshift
import boto.route53
import boto.s3
import boto.ses
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


class InstanceState(object):
    """Represents the state of an instance.
    """
    PENDING = 0
    RUNNING = 16
    SHUTTING_DOWN = 32
    TERMINATED = 48
    STOPPING = 64
    STOPPED = 80


def connect_to_regions(service, regions):
    if regions is not None:
        return [service.connect_to_region(r.name) for r in service.regions()
            if r.name in regions]
    else:
        return [service.connect_to_region(r.name) for r in service.regions()
            if not r.name.startswith(('us-gov-', 'cn-'))]


def print_items(items, labels):
    if 1 == len(labels):
        return '{0} {1}{2}'.format(items, labels[0], 's'[1==items:])
    else:
        return '{0} {1}'.format(items, labels[1!=items])


def flatten(x):
    return itertools.chain.from_iterable(x)


def get_ec2_usage(regions):
    cs = connect_to_regions(boto.ec2, regions)
    instances = list(flatten(x.instances for c in cs
        for x in c.get_all_reservations()))
    running = sum(InstanceState.RUNNING == i.state_code
        for i in instances)

    volumes = list(flatten(c.get_all_volumes() for c in cs))
    size = sum(v.size for v in volumes)

    snapshots = sum(len(c.get_all_snapshots(owner=['self'])) for c in cs)
    images = sum(len(c.get_all_images(owners=['self'])) for c in cs)
    addresses = len(list(flatten(c.get_all_addresses() for c in cs)))
    groups = sum(len(c.get_all_security_groups()) for c in cs)
    key_pairs = sum(len(c.get_all_key_pairs()) for c in cs)
    tags = sum(len(c.get_all_tags()) for c in cs)

    print '{0}{1}\n' \
        '{2} EC2 Reserved Instance(s)\n' \
        '{3} EC2 Spot Instance Request(s)\n' \
        '{4}{5}\n' \
        '{6}\n' \
        '{7}\n' \
        '{8} Network Interface(s)\n' \
        '{9}\n' \
        '{10}\n' \
        '{11}\n' \
        '{12}' \
        .format(print_items(len(instances), ['EC2 Instance']),
            ' [{0} running]'.format(running) if 0 != running else '',
            sum(len(c.get_all_reserved_instances()) for c in cs),
            sum(len(c.get_all_spot_instance_requests()) for c in cs),
            print_items(len(volumes), ['EBS Volume']),
            ' [{0} GB]'.format(size) if 0 != size else '',
            print_items(snapshots, ['EBS Snapshot']),
            print_items(images, ['Amazon Machine Image']),
            sum(len(c.get_all_network_interfaces()) for c in cs),
            print_items(addresses, ['Elastic IP Address',
                'Elastic IP Addresses']),
            print_items(groups, ['Security Group']),
            print_items(key_pairs, ['Key Pair']),
            print_items(tags, ['Tag']))


def get_autoscale_usage(regions):
    cs = connect_to_regions(boto.ec2.autoscale, regions)
    groups = sum(len(c.get_all_groups()) for c in cs)
    instances = len(list(flatten(c.get_all_autoscaling_instances()
        for c in cs)))
    configs = sum(len(c.get_all_launch_configurations()) for c in cs)
    policies = sum(len(c.get_all_policies()) for c in cs)
    print '{0}\n' \
        '{1}\n' \
        '{2}\n' \
        '{3}' \
        .format(print_items(groups, ['Auto Scaling Group']),
            print_items(instances, ['Auto Scaling Instance']),
            print_items(configs, ['Auto Scaling Launch Configuration']),
            print_items(policies, ['Auto Scaling Policy',
                'Auto Scaling Policies']))


def get_elb_usage(regions):
    cs = connect_to_regions(boto.ec2.elb, regions)
    balancers = list(flatten(c.get_all_load_balancers() for c in cs))
    print '{0} [{1} instance(s)]' \
        .format(print_items(len(balancers), ['Elastic Load Balancer']),
            sum(b.instances for b in balancers))


def get_vpc_usage(regions):
    cs = connect_to_regions(boto.vpc, regions)
    vpcs = list(flatten(c.get_all_vpcs() for c in cs))
    print '{0} [{1} default]\n' \
        '{2} Internet Gateway(s)\n' \
        '{3} Customer Gateway(s)\n' \
        '{4} VPN Gateway(s)\n' \
        '{5} Subnet(s)' \
        .format(print_items(len(vpcs), ['Virtual Private Cloud']),
            sum(v.is_default for v in vpcs),
            sum(len(c.get_all_internet_gateways()) for c in cs),
            sum(len(c.get_all_customer_gateways()) for c in cs),
            sum(len(c.get_all_vpn_gateways()) for c in cs),
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
    res = sum(k.size for k in flatten(b.get_all_keys() for b in buckets))
    print '{0} S3 Bucket(s) [{1:.3f} GB]' \
        .format(len(buckets), res / float(1024 * 1024 * 1024))


def get_glacier_usage(regions):
    cs = connect_to_regions(boto.glacier, regions)
    vaults = list(flatten(c.list_vaults() for c in cs))
    size = sum(v.size_in_bytes for v in vaults)
    print print_items(len(vaults), ['Glacier Vault'])
    print '{0}{1}' \
        .format(print_items(sum(v.number_of_archives for v in vaults),
                ['Glacier Archive']),
            ' [{0} GB]'.format(size / float(1024 * 1024 * 1024))
                if 0 != size else '')


def get_cloudfront_usage():
    c = boto.connect_cloudfront()
    distrs = c.get_all_distributions()
    objects = len(list(flatten(d.get_distribution().get_objects()
        for d in distrs)))
    print '{0}{1}' \
        .format(print_items(len(distrs), ['CloudFront Distribution']),
            ' [{0}]'.format(print_items(objects, ['object']))
                if 0 != objects else '')


def get_sdb_usage(regions):
    cs = connect_to_regions(boto.sdb, regions)
    domains = sum(len(c.get_all_domains()) for c in cs)
    print print_items(domains, ['SimpleDB Domain'])


def get_rds_usage(regions):
    cs = connect_to_regions(boto.rds2, regions)
    instances = list(flatten(c.describe_db_instances()
        ['DescribeDBInstancesResponse']
        ['DescribeDBInstancesResult']
        ['DBInstances'] for c in cs))
    available = sum(i['DBInstanceStatus'] == 'available' for i in instances)
    print '{0}{1}' \
        .format(print_items(len(instances), ['RDS Instance']),
            ' [{0} available]'.format(available) if 0 != available else '')
    print print_items(sum(len(c.describe_reserved_db_instances()
        ['DescribeReservedDBInstancesResponse']
        ['DescribeReservedDBInstancesResult']
        ['ReservedDBInstances']) for c in cs), ['RDS Reserved Instance'])
    print print_items(sum(len(c.describe_db_snapshots()
        ['DescribeDBSnapshotsResponse']
        ['DescribeDBSnapshotsResult']
        ['DBSnapshots']) for c in cs), ['RDS Snapshot'])


def get_dynamodb_usage(regions):
    cs = connect_to_regions(boto.dynamodb2, regions)
    tables = list(flatten([boto.dynamodb2.table.Table(t)] for c in cs
            for t in c.list_tables()['TableNames']))
    items = sum(t.count() for t in tables)
    print '{0}{1}' \
        .format(print_items(len(tables), ['DynamoDB Table']),
            ' [{0}]'.format(print_items(items, ['item']))
            if 0 != items else '')


def get_elasticache_usage(regions):
    cs = connect_to_regions(boto.elasticache, regions)
    clusters = list(flatten(c.describe_cache_clusters()
        ['DescribeCacheClustersResponse']
        ['DescribeCacheClustersResult']
        ['CacheClusters'] for c in cs))
    print print_items(len(clusters), ['ElastiCache Cluster'])


def get_redshift_usage(regions):
    cs = connect_to_regions(boto.redshift, regions)
    clusters = list(flatten(c.describe_clusters()
        ['DescribeClustersResponse']
        ['DescribeClustersResult']
        ['Clusters'] for c in cs))
    print print_items(len(clusters), ['Redshift Cluster'])


def get_datapipeline_usage(regions):
    cs = connect_to_regions(boto.datapipeline, regions)
    pipelines = list(flatten(c.list_pipelines()['pipelineIdList']
        for c in cs))
    print print_items(len(pipelines), ['Data Pipeline'])


def get_emr_usage(regions):
    cs = connect_to_regions(boto.emr, regions)
    clusters = list(flatten([c.describe_cluster(s.id)] for c in cs
        for s in c.list_clusters().clusters))
    print print_items(len(clusters), ['EMR Cluster'])


def get_kinesis_usage(regions):
    cs = connect_to_regions(boto.kinesis, regions)
    streams = list(flatten(c.list_streams()['StreamNames'] for c in cs))
    shards = sum(len(c.describe_stream(s)
        ['StreamDescription']
        ['Shards']) for c in cs for s in streams)
    print '{0}{1}' \
        .format(print_items(len(streams), ['Kinesis Stream']),
            ' [{0}]'.format(print_items(shards, ['shard']))
            if 0 != shards else '')


def get_cloudsearch_usage(regions):
    cs = connect_to_regions(boto.cloudsearch2, regions)
    domains = list(flatten(c.list_domain_names()
        ['ListDomainNamesResponse']
        ['ListDomainNamesResult']
        ['DomainNames'] for c in cs))
    print print_items(len(domains), ['CloudSearch Domain'])


def get_elastictranscoder_usage(regions):
    cs = connect_to_regions(boto.elastictranscoder, regions)
    pipelines = list(flatten(c.list_pipelines()['Pipelines'] for c in cs))
    jobs = list(flatten(c.list_jobs_by_status('Progressing')
        ['Jobs'] for c in cs))
    print print_items(len(pipelines), ['Elastic Transcoder Pipeline'])
    print print_items(len(jobs), ['Elastic Transcoder Job'])


def get_ses_usage(regions):
    cs = connect_to_regions(boto.ses, regions)
    print print_items(len(list(flatten(c.list_identities()
        ['ListIdentitiesResponse']
        ['ListIdentitiesResult']
        ['Identities'] for c in cs))), ['SES Identity', 'SES Identities'])


def get_sns_usage(regions):
    cs = connect_to_regions(boto.sns, regions)
    print print_items(sum(len(c.get_all_topics()
        ['ListTopicsResponse']
        ['ListTopicsResult']
        ['Topics']) for c in cs), ['SNS Topic'])
    print print_items(sum(len(c.get_all_subscriptions()
        ['ListSubscriptionsResponse']
        ['ListSubscriptionsResult']
        ['Subscriptions']) for c in cs), ['SNS Subscription'])
    print print_items(sum(len(c.list_platform_applications()
        ['ListPlatformApplicationsResponse']
        ['ListPlatformApplicationsResult']
        ['PlatformApplications']) for c in cs), ['SNS Platform Application'])


def get_sqs_usage(regions):
    cs = connect_to_regions(boto.sqs, regions)
    queues = list(flatten(c.get_all_queues() for c in cs))
    messages = sum(q.count() for q in queues)
    print '{0}{1}' \
        .format(print_items(len(queues), ['SQS Queue']),
            ' [{0}]'.format(print_items(messages, ['message']))
                if 0 != messages else '')


def get_iam_usage(regions):
    cs = connect_to_regions(boto.iam, regions)
    users = list(flatten(c.get_all_users()
        ['list_users_response']
        ['list_users_result']
        ['users'] for c in cs))
    groups = list(flatten(c.get_all_groups()
        ['list_groups_response']
        ['list_groups_result']
        ['groups'] for c in cs))
    print print_items(len(users), ['IAM User'])
    print print_items(len(groups), ['IAM Group'])


def get_beanstalk_usage(regions):
    cs = connect_to_regions(boto.beanstalk, regions)
    apps = list(flatten(c.describe_applications()
        ['DescribeApplicationsResponse']
        ['DescribeApplicationsResult']
        ['Applications'] for c in cs))
    print print_items(len(apps), ['Elastic Beanstalk Application'])


def get_cloudtrail_usage(regions):
    cs = connect_to_regions(boto.cloudtrail, regions)
    trails = list(flatten(c.describe_trails()
        ['trailList'] for c in cs))
    print print_items(len(trails), ['CloudTrail Trail'])


def get_cloudwatch_usage(regions):
    cs = connect_to_regions(boto.ec2.cloudwatch, regions)
    alarms = list(flatten(c.describe_alarms() for c in cs))
    triggered = sum(a.state_value == MetricAlarm.ALARM for a in alarms)
    print '{0}{1}' \
        .format(print_items(len(alarms), ['CloudWatch Alarm']),
            ' [{0} triggered]'.format(triggered) if 0 != triggered else '')


def get_opsworks_usage():
    ow = boto.connect_opsworks()
    print print_items(len(ow.describe_stacks()['Stacks']), ['OpsWorks Stack'])


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
            total.extend([['Cost', float(row[24]), row[23]],
                ['Credit', float(row[25]), row[23]],
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
        get_glacier_usage(opts.regions)
        get_cloudfront_usage()

        get_sdb_usage(opts.regions)
        get_rds_usage(opts.regions)
        get_dynamodb_usage(opts.regions)
        get_elasticache_usage(opts.regions)
        get_redshift_usage(opts.regions)

        get_datapipeline_usage(opts.regions)
        get_emr_usage(opts.regions)
        get_kinesis_usage(opts.regions)

        get_cloudsearch_usage(opts.regions)
        get_elastictranscoder_usage(opts.regions)
        get_ses_usage(opts.regions)
        get_sns_usage(opts.regions)
        get_sqs_usage(opts.regions)

        get_beanstalk_usage(opts.regions)
        get_cloudtrail_usage(opts.regions)
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
