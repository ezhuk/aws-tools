#!/usr/bin/env python
#
# Copyright (c) 2013 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

import optparse
import subprocess
import sys
import time


def create_policy(load_balancer, policy_name):
    proc = subprocess.Popen(['aws',
        'elb',
        'create-load-balancer-policy',
        '--load-balancer-name', load_balancer,
        '--policy-name', policy_name,
        '--policy-type-name', 'SSLNegotiationPolicyType',
        '--policy-attributes', '['
            '{"AttributeName":"Protocol-SSLv2","AttributeValue":"false"},'
            '{"AttributeName":"Protocol-TLSv1","AttributeValue":"true"},'
            '{"AttributeName":"Protocol-SSLv3","AttributeValue":"true"},'
            '{"AttributeName":"Protocol-TLSv1.1","AttributeValue":"true"},'
            '{"AttributeName":"Protocol-TLSv1.2","AttributeValue":"true"},'
            '{"AttributeName":"DHE-RSA-AES128-GCM-SHA256","AttributeValue":"true"},'
            '{"AttributeName":"DHE-RSA-AES256-GCM-SHA384","AttributeValue":"true"},'
            '{"AttributeName":"AES128-GCM-SHA256","AttributeValue":"true"},'
            '{"AttributeName":"AES256-GCM-SHA384","AttributeValue":"true"},'
            '{"AttributeName":"AES128-SHA","AttributeValue":"true"},'
            '{"AttributeName":"AES256-SHA","AttributeValue":"true"},'
            '{"AttributeName":"DHE-RSA-AES128-SHA","AttributeValue":"true"},'
            '{"AttributeName":"DHE-RSA-AES256-SHA","AttributeValue":"true"},'
            '{"AttributeName":"RC4-MD5","AttributeValue":"false"},'
            '{"AttributeName":"DES-CBC3-SHA","AttributeValue":"false"}'
        ']'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        return 1

    return 0

def set_policy(load_balancer, policy_name):
    proc = subprocess.Popen(['aws',
        'elb',
        'set-load-balancer-policies-of-listener',
        '--load-balancer-name', load_balancer,
        '--load-balancer-port', '443',
        '--policy-names', policy_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        return 1

    return 0

def main():
    parser = optparse.OptionParser('Usage: %prog <load_balancer> [options]')
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        return 1

    load_balancer = args[0]
    policy_name = 'SSLNegotiationPolicy-' + load_balancer + '-' + time.strftime('%Y%m%d%H%M%S', time.gmtime())

    if create_policy(load_balancer, policy_name):
        print '[ERROR] could not create \'{0}\' for \'{1}\''.format(policy_name, load_balancer)
        return 1

    if set_policy(load_balancer, policy_name):
        print '[ERROR] could not set \'{0}\' for \'{1}\''.format(policy_name, load_balancer)
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
