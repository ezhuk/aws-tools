#!/usr/bin/env python
# Copyright (c) 2014 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Deregisters all instances from the AWS Elastic Load Balancer (ELB).

A simple script to deregister all currently registered EC2 instances from
the load balancer.

Usage:
    ./deregister_all_instances.py [options]
"""

import boto.ec2.elb
import optparse
import sys


class Error(Exception):
    pass


def main():
    parser = optparse.OptionParser('Usage: %prog [options]')
    parser.add_option('-l', '--load-balancer', dest='lb', help='')
    (opts, args) = parser.parse_args()

    if 0 != len(args):
        parser.print_help()
        return 1

    try:
        elb = boto.connect_elb()
        lb = elb.get_all_load_balancers([opts.lb])
        elb.deregister_instances(opts.lb, [i.id for i in lb.instances])
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
