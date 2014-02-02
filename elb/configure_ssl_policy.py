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
    ./configure_ssl_policy.py <load_balancer>
"""

import boto.ec2.elb
import json
import optparse
import sys
import time


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog <load_balancer> [options]')
    (opts, args) = parser.parse_args()

    # Make sure the load balancer name is specified.
    if len(args) != 1:
        parser.print_help()
        return 1

    try:
        elb = boto.connect_elb()

        policy_attributes = {
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

        policy = elb.create_lb_policy(args[0],
            'SSLNegotiationPolicy-{0}-{1}' \
                .format(load_balancer, time.strftime('%Y%m%d%H%M%S', time.gmtime())),
            'SSLNegotiationPolicyType',
            policy_attributes)

        elb.set_lb_policies_of_listener(args[0], 443, [policy])
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
