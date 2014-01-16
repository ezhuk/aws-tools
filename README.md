# AWS Tools

This is a set of auxiliary tools for Amazon Web Services (AWS).

## What's included

#### configure_auto_scaling.py

Configures AWS Auto Scaling to automatically manage system capacity based on
an average CPU usage. It takes care of setting up launch configuration, auto
scaling group, scaling policies and metric alarms to automatically add a new
EC2 instance when the average CPU utilization exceeds 60% over any 5 minutes
period and shutdown an instance when it goes below 40%.

```bash
./configure_auto_scaling.py TEST \
    --image ami-a43909e1 \
    --type t1.micro \
    --key MyKeyPair \
    --group MySecurityGroup \
    --min 2 \
    --max 8 \
    --zone us-west-1a \
    --load-balancer MyLoadBalancer
```

#### haproxy_autoscale.py

Keeps track of EC2 instances behind [HAProxy](http://haproxy.1wt.eu/) used as
a load balancer and updates its configuration if they change. This allows to
automatically direct traffic to currently running instances and remove the ones
that are no longer used.

This tool is supposed to be run periodically (e.g., every minute or so) and
can be configured as a cron job as follows:

```bash
*/1 * * * * user /usr/sbin/haproxy_autoscale.py --group MySecurityGroup
```

#### configure_ssl_policy.py

Configures certain [recommended](https://wiki.mozilla.org/Security/Server_Side_TLS)
server-side TLS settings for the default HTTPS listener on an Elastic Load
Balancer (ELB). Even though ELB supports latest TLS versions and recommended
ciphers they are not enabled by default for some reasons.


This script enables the most recent and more secure TLS v1.2 and v1.1 versions
and strong ciphers. Since ELB does not seem to support ECDHE at this time, forward
secrecy is provided by the DHE suite which can be disabled if performance is of
concern.

```bash
./configure_ssl_policy.py MyLoadBalancer
```

## License

Licensed under the [MIT license](LICENSE).
