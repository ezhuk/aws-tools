#!/usr/bin/env python
# Copyright (c) 2013 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Confirms subscription to a topic.

This is used to confirm a subscription of an HTTP endpoint to a topic
created on AWS Simple Notification Service (SNS). It is supposed to
run on the endpoint that is being subscribed.

Usage:
    ./confirm_subscription.py [options]
"""

import BaseHTTPServer
import json
import optparse
import SimpleHTTPServer
import SocketServer
import sys
import urllib2
from xml.etree import ElementTree


class Error(Exception):
    pass


class Server(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """Use the ThreadingMixIn to handle requests in multiple threads.
    """
    pass


class RequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """Handles confirmation requests from AWS SNS.
    """
    # Use HTTP/1.1 by default. The caveat is that the Content-Length
    # header must be specified in all responses.
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        try:
            message_type = self.headers.getheader('x-amz-sns-message-type')
            if message_type != 'SubscriptionConfirmation':
                raise Error('unsupported message type \'{0}\''.format(message_type))

            size = int(self.headers.getheader('content-length'))
            doc = json.loads(self.rfile.read(size))

            response = urllib2.urlopen(doc['SubscribeURL'])
            xml = ElementTree.XML(response.read())
            arn = xml.find('ConfirmSubscriptionResult/SubscriptionArn')
            print arn.text
        except (Error, urllib2.HTTPError), err:
            self.send_response(404)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-Length', '0')
        self.end_headers()


def main():
    parser = optparse.OptionParser('Usage: %prog [options]')
    parser.add_option('-p', '--port', dest='port', default=8080,
        help='The port number to listen on. This option is not required '
             'and is set to 8080 by default.')
    (opts, args) = parser.parse_args()

    try:
        server = Server(('', opts.port), RequestHandler)
        server.serve_forever()
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
