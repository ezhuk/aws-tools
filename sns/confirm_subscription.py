#!/usr/bin/env python
# Copyright (c) 2013 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Confirms subscription to a topic.

This is used to confirm a subscription of an HTTP(S) endpoint to a topic
created on AWS Simple Notification Service (SNS). It is supposed to run
on the endpoint that is being subscribed.

Usage:
    ./confirm_subscription.py [options]
"""

import BaseHTTPServer
import json
import optparse
import SimpleHTTPServer
import SocketServer
import ssl
import sys
import urllib2

from xml.etree import ElementTree


class Error(Exception):
    pass


class Defaults(object):
    """Default settings.
    """
    PORT = 8080


class MessageType(object):
    """Represents SNS message type.
    """
    CONFIRMATION = 'SubscriptionConfirmation'
    NOTIFICATION = 'Notification'


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
            size = int(self.headers.getheader('content-length'))
            doc = json.loads(self.rfile.read(size))

            message_type = self.headers.getheader('x-amz-sns-message-type')
            if MessageType.CONFIRMATION == message_type:
                _handle_confirmation(doc)
            elif MessageType.NOTIFICATION == message_type:
                _handle_notification(doc)
            else:
                raise Error('unsupported message type \'{0}\''
                    .format(message_type))
        except (Error, Exception), err:
            self.send_response(404)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        self.send_response(403)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def _handle_confirmation(self, data):
        response = urllib2.urlopen(data['SubscribeURL'])
        xml = ElementTree.XML(response.read())
        arn = xml.find('ConfirmSubscriptionResult/SubscriptionArn')
        print arn.text

    def _handle_notification(self, data):
        print 'Subject: \'{0}\'\nMessage: \'{1}\'\nTime: \'{2}\'' \
            .format(data['Subject'], data['Message'], data['Timestamp'])


def main():
    parser = optparse.OptionParser('Usage: %prog [options]')
    parser.add_option('-p', '--port', dest='port', default=Defaults.PORT,
        help='The port number to listen on. This option is not required and '
             'is set to 8080 by default.')
    parser.add_option('-s', '--ssl', dest='ssl', action='store_true',
        help='Enable SSL/TLS. This option is not required.')
    parser.add_option('-k', '--key', dest='key',
        help='A private key file to be used when SSL is enabled.')
    parser.add_option('-c', '--cert', dest='cert',
        help='A certificate file to be used when SSL is enabled.')
    (opts, args) = parser.parse_args()

    if (0 != len(args) or
        (opts.ssl and (opts.cert is None or opts.key is None))):
        parser.print_help()
        return 1

    try:
        server = Server(('', int(opts.port)), RequestHandler)
        if opts.ssl:
            server.socket = ssl.wrap_socket(server.socket,
                server_side=True,
                ssl_version=ssl.PROTOCOL_TLSv1,
                certfile=opts.cert,
                keyfile=opts.key)
        server.serve_forever()
    except Error, err:
        sys.stderr.write('[ERROR] {0}\n'.format(err))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

