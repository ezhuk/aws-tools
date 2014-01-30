#!/usr/bin/env python
# Copyright (c) 2013 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Configures billing alert.

A tool that allows to set up a billing alert to keep track of monthly
usage charges across AWS services. An email notification will be sent
to the specified email address whenever the estimated monthly charges
exceed the specified threshold for a duration of six hours.

Usage:
    ./configure_billing_alert.py <options>
"""

import boto.ec2.cloudwatch
import boto.sns
import json
import optparse
import subprocess
import sys

from boto.ec2.cloudwatch import MetricAlarm


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog <options>')
    parser.add_option('-e', '--email', dest='email',
        help='The email address to send notifications to whenever an '
             'alert is triggered.')
    parser.add_option('-t', '--threshold', dest='threshold',
        help='The dollar amount of estimated monthly charges which, '
             'when exceeded, causes an alert to be triggered.')
    (opts, args) = parser.parse_args()

    if len(args) != 0:
        parser.print_help()
        return 1

    if opts.email is None or \
       opts.threshold is None:
        parser.print_help()
        return 1

    try:
        sns = boto.connect_sns()

        topic = sns.create_topic('BillingNotifications') \
            ['CreateTopicResponse']['CreateTopicResult']['TopicArn']

        res = sns.subscribe(topic, 'email', opts.email) \
            ['SubscribeResponse']['SubscribeResult']['SubscriptionArn']
        if res == 'pending confirmation':
            raw_input('Please confirm subscription. Press [ENTER] when done...')

        cloudwatch = boto.connect_cloudwatch()

        alarm = MetricAlarm(name='BillingAlarm-{0}'.format(opts.threshold),
            description='Estimated Monthly Charges',
            alarm_actions=[topic],
            metric='EstimatedCharges',
            namespace='AWS/Billing',
            statistic='Maximum',
            dimensions={'Currency':'USD'},
            period=21600,
            evaluation_periods=1,
            threshold=int(opts.threshold),
            comparison='>=')
        cloudwatch.create_alarm(alarm)
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
