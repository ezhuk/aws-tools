#!/usr/bin/env python
# Copyright (c) 2013 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Configures AWS Elastic Load Balancer (ELB) SSL settings.

A tool to properly configure SSL settings for AWS load balancers. Even
though ELB supports TLS v1.2 and v1.1 protocols and certain recommended
ciphers, they are not enabled by default.

This script creates a new SSL policy with the correct TLS versions and
ciphers enabled and applies it to the default HTTPS listener (port 443)
on the load balancer.

Usage:
    ./configure_ssl_policy <load_balancer>
"""

import json
import optparse
import subprocess
import sys
import time


class Error(Exception):
    pass


class Policy(object):
    def __init__(self, load_balancer):
        self.type = 'SSLNegotiationPolicyType'
        # Append the current timestamp to the policy name to make sure
        # it is somewhat unique and keep track of when changes are made.
        self.name = 'SSLNegotiationPolicy-{0}-{1}' \
            .format(load_balancer, time.strftime('%Y%m%d%H%M%S', time.gmtime()))
        self.load_balancer = load_balancer
        # Policy attributes specifying SSL/TLS protocols and ciphers.
        self.attributes = {
            'Protocol-SSLv2': False,
            'Protocol-SSLv3': True,
            'Protocol-TLSv1': True,
            'Protocol-TLSv1.1': True,
            'Protocol-TLSv1.2': True,
            'DHE-RSA-AES128-GCM-SHA256': True,
            'DHE-RSA-AES256-GCM-SHA384': True,
            'AES128-GCM-SHA256': True,
            'AES256-GCM-SHA384': True,
            'AES128-SHA': True,
            'AES256-SHA': True,
            'DHE-RSA-AES128-SHA': True,
            'DHE-RSA-AES256-SHA': True,
            'RC4-MD5': False,
            'DES-CBC3-SHA': False
        }

def create_policy(policy):
    """Creates a new SSL policy for the specified load balancer.

    Enables the most recent and more secure TLS v1.2 and v1.1 protocols
    and strong ciphersuite by default. Since AWS ELB does not seem to
    support ECDHE ciphers at this time, forward secrecy is provided by
    the DHE suite.

    Args:
        policy: The policy object.

    Returns:
        The status code that is set to 0 on success.
    """
    proc = subprocess.Popen(['aws',
        'elb',
        'create-load-balancer-policy',
        '--load-balancer-name', policy.load_balancer,
        '--policy-name', policy.name,
        '--policy-type-name', policy.type,
        '--policy-attributes', json.dumps([
            {"AttributeName":k,"AttributeValue":v}
            for k, v in policy.attributes.iteritems()])],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        raise Error('could not create \'{0}\''.format(policy.name))

    return 0


def set_policy(policy):
    """Sets the SSL policy.

    Enables a policy for the default HTTPS listener (port 443) on the
    specified load balancer.

    Args:
        policy: The policy object.

    Returns:
        The status code that is set to 0 on success.
    """
    proc = subprocess.Popen(['aws',
        'elb',
        'set-load-balancer-policies-of-listener',
        '--load-balancer-name', policy.load_balancer,
        '--load-balancer-port', '443',
        '--policy-names', policy.name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        raise Error('could not set \'{0}\''.format(policy.name))

    return 0


def main():
    parser = optparse.OptionParser('Usage: %prog <load_balancer> [options]')
    (options, args) = parser.parse_args()

    # Make sure the load balancer name is specified.
    if len(args) != 1:
        parser.print_help()
        return 1

    try:
        policy = Policy(args[0])

        create_policy(policy)
        set_policy(policy)
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
