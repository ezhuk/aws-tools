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

import json
import optparse
import subprocess
import sys


class Error(Exception):
    pass


def create_topic(name):
    """Creates a new SNS topic.

    Since billing metrics and alarms are enabled for us-east-1 region,
    the topic needs to be created there as well.

    Args:
        name: Name of the topic to create.

    Returns:
        ARN of the newly created topic on success.
    """
    proc = subprocess.Popen(['aws',
        '--region', 'us-east-1',
        'sns',
        'create-topic',
        '--name', name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        raise Error('could not create \'{0}\''.format(name))

    doc = json.loads(out)
    return doc['TopicArn']


def create_subscription(topic, endpoint):
    """Creates a new SNS subscription.

    Subscribes an endpoint to the specified topic. It actually prepares
    to subscribe an endpoint and sends an email with a confirmation
    token which the endpoint owner must use to confirm a subscription.

    Args:
        topic: ARN of the topic to subscribe to.
        endpoint: An email address that will be receiving notifications.

    Returns:
        The status code that is set to 0 on success.
    """
    proc = subprocess.Popen(['aws',
        '--region', 'us-east-1',
        'sns',
        'subscribe',
        '--topic-arn', topic,
        '--protocol', 'email',
        '--notification-endpoint', endpoint],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        raise Error('could not create subscription')

    return 0


def create_metric_alarm(topic, threshold):
    """Creates a new metric alarm.

    The alarm is set to be triggered whenever the estimated monthly
    charges exceed the specified threshold for a duration of 6 hours.

    Args:
        topic: ARN of the topic to send notifications to.
        threshold: The dollar amount that is used to trigger an alert.

    Returns:
        The status code that is set to 0 on success and 1 otherwise.
    """
    proc = subprocess.Popen(['aws',
        '--region', 'us-east-1',
        'cloudwatch',
        'put-metric-alarm',
        '--alarm-name', 'BillingAlarm-{0}'.format(threshold),
        '--alarm-description', 'Estimated Monthly Charges',
        '--alarm-actions', topic,
        '--metric-name', 'EstimatedCharges',
        '--namespace', 'AWS/Billing',
        '--statistic', 'Maximum',
        '--dimensions', '[{"Name":"Currency","Value":"USD"}]',
        '--period', '21600',
        '--evaluation-periods', '1',
        '--threshold', threshold,
        '--comparison-operator', 'GreaterThanOrEqualToThreshold'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        print err
        raise Error('could not create alarm')

    return 0


def main():
    parser = optparse.OptionParser('Usage: %prog <options>')
    parser.add_option('-e', '--email', dest='email',
        help='The email address to send notifications to whenever an '
             'alert is triggered.')
    parser.add_option('-t', '--threshold', dest='threshold',
        help='The dollar amount of estimated monthly charges which, '
             'when exceeded, causes an alert to be triggered.')
    (opts, args) = parser.parse_args()

    if opts.email is None or \
       opts.threshold is None:
        parser.print_help()
        return 1

    try:
        topic = create_topic('BillingNotifications')
        subscription = create_subscription(topic, opts.email)
        raw_input('Please confirm email subscription. Press [ENTER] when done...')
        create_metric_alarm(topic, opts.threshold)
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
