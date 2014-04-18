#!/usr/bin/env python
# Copyright (c) 2013 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Configures AWS Elastic Load Balancer (ELB) SSL settings.

A tool to configure SSL settings for AWS load balancers. It creates a new
SSL policy with the correct TLS versions and ciphers enabled and applies
it to the default HTTPS listener (port 443) on the load balancer.

Usage:
    ./configure_ssl_policy.py [options]
"""

import boto.ec2.elb
import optparse
import sys
import time


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog [options]')
    parser.add_option('-l', '--load-balancer', dest='lbs', action='append',
        help='A list of AWS load balancers to configure the policy on. '
             'This option is required.')
    (opts, args) = parser.parse_args()

    if len(args) != 0 or \
       opts.lbs is None:
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
            'Server-Defined-Cipher-Order': True,
            'ECDHE-ECDSA-AES128-GCM-SHA256': True,
            'ECDHE-RSA-AES128-GCM-SHA256': True,
            'ECDHE-ECDSA-AES128-SHA256': True,
            'ECDHE-RSA-AES128-SHA256': True,
            'ECDHE-ECDSA-AES128-SHA': True,
            'ECDHE-RSA-AES128-SHA': True,
            'ECDHE-RSA-AES256-SHA': True,
            'AES128-SHA256': True,
            'AES128-SHA': True,
            'AES256-SHA256': True,
            'AES256-SHA': True,
            'ECDHE-RSA-RC4-SHA': True,
            'RC4-SHA': True
        }

        for lb in opts.lbs:
            policy = elb.create_lb_policy(lb,
                'SSLNegotiationPolicy-{0}-{1}' \
                    .format(lb, time.strftime('%Y%m%d%H%M%S', time.gmtime())),
                'SSLNegotiationPolicyType',
                policy_attributes)

            elb.set_lb_policies_of_listener(lb, 443, [policy])
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
