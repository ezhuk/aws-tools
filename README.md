# AWS Tools

This is a set of auxiliary tools for Amazon Web Services (AWS).

## What's included

### 1. Auto Scaling

#### configure_auto_scaling.py

Configures AWS Auto Scaling to automatically manage system capacity based on
an average CPU usage. It takes care of setting up new launch configuration
and auto scaling group, scaling policies and metric alarms to automatically
provision or shutdown one or more EC2 instances if an average CPU utilization
exceeds the maximum threshold or goes below the minimum threshold respectively.

```
Usage:
    configure_auto_scaling [options]

Options:
    -n NAME, --name=NAME  The name of this configuration (e.g., TEST).
    -i IMAGE, --image=IMAGE
                        The Amazon  Machine  Image (AMI) ID that will be used
                        to launch EC2 instances. The most recent Amazon Linux
                        AMI 2013.09.2 (ami-a43909e1) is used by default.
    -t TYPE, --type=TYPE  The type of the Amazon EC2 instance. If not specified,
                        micro instance (t1.micro) type will be used.
    -k KEY, --key=KEY     The name of the key pair to use when creating EC2
                        instances. This options is required.
    -g GROUP, --group=GROUP
                        Security group that will be used when creating EC2
                        instances. This option is required.
    -m MIN, --min=MIN     The minimum number of EC2 instances in the auto
                        scaling group. If not specified, 2 will be used.
    -M MAX, --max=MAX     The maximum size of the auto scaling group. By default
                        it is set to 4.
    -z ZONES, --zone=ZONES
                        The availability zone for the auto scaling group. This
                        option is required.
    -l LBS, --load-balancer=LBS
                        The name of an existing AWS load balancer to use, if
                        any.
    --min-threshold=MIN_THRESHOLD
                        The minimum CPU utilization threshold that triggers an
                        alarm. This option is not required and is set to 40%
                        by default.
    --max-threshold=MAX_THRESHOLD
                        The maximum CPU utilization threshold that triggers an
                        alarm. This option is not required and is set to 60%
                        by default.
    -a ADJUSTMENT, --adjustment=ADJUSTMENT
                        The number of EC2 instances by which to scale up or
                        down. This is set to 1 by default.
    -p PERIOD, --period=PERIOD
                        The evaluation period in seconds. This is optional and
                        is set to 300 seconds by default.
    -h, --help          Show this help message and exit

Example:
./configure_auto_scaling.py \
    --name TEST \
    --image ami-a43909e1 \
    --type t1.micro \
    --key MyKeyPair \
    --group MySecurityGroup \
    --min 2 \
    --max 8 \
    --min-threshold 30 \
    --max-threshold 70 \
    --adjustment 2 \
    --zone us-west-1a \
    --load-balancer MyLoadBalancer
```

#### haproxy_autoscale.py

Keeps track of EC2 instances behind [HAProxy](http://haproxy.1wt.eu/) used as
a load balancer that are associated with one or more security groups and updates
its configuration if they change. This allows to automatically direct traffic
to the currently running instances and remove the ones that are no longer used.

This tool is supposed to be run periodically (e.g., every minute or so) and
can be configured as a cron job as follows:

```
Usage:
    haproxy_autoscale.py [options]

Options:
    -c CONFIG, --config=CONFIG
                        HAProxy configuration file to use.
    -g GROUPS, --group=GROUPS
                        The ID of a security group.
    -h, --help          Show this help message and exit

Example:
*/1 * * * * user /usr/sbin/haproxy_autoscale.py --group MySecurityGroup
```

#### shutdown_auto_scaling.py

Gracefully shuts down previously created Auto Scaling configuration. This script
also deletes scaling policies, metric alarms and launch configuration associated
with the specified Auto Scaling group.

```
Usage:
    shutdown_auto_scaling.py [options]

Options:
    -n NAME, --name=NAME  The name of the configuration to shutdown (e.g., TEST).
    -h, --help            Show this help message and exit

Example:
./shutdown_auto_scaling.py --name TEST
```

### 2. Billing

#### check_usage.py

Retrieves AWS usage information for the specified billing period and displays
estimated total charges (including credits, if any). Note that for this to work,
receiving monthly billing reports must be enabled in account preferences.

```
Usage:
    check_usage.py [options]

Options:
    -b BUCKET, --bucket=BUCKET
                        The name of the S3 bucket that holds billing reports.
                        This option is required.
    -p PERIOD, --period=PERIOD
                        The billing period to check the usage for (e.g.,
                        '2014-02' without quotes). Defaults to the current
                        billing period if not specified.
    -h, --help          Show this help message and exit

Example:
./check_usage.py --bucket MyBucket
```

#### configure_billing_alert.py

Sets up a billing alert to keep track of monthly charges across AWS services so
that an email notification gets sent to the specified email address whenever the
estimated monthly charges exceed the specified threshold. Note that metric data
monitoring must be enabled in billing preferences prior to configuring this alert.

```
Usage:
    configure_billing_alert.py [options]

Options:
    -e EMAIL, --email=EMAIL
                        The email address to send notifications to whenever an
                        alert is triggered.
    -n NAME, --name=NAME  The name of the alarm (e.g., BillingAlarm-1000).
    -t THRESHOLD, --threshold=THRESHOLD
                        The dollar amount of estimated monthly charges which,
                        when exceeded, causes an alert to be triggered.
    -p PERIOD, --period=PERIOD
                        The period in seconds over which the estimated monthly
                        charges statistic is applied.
    -h, --help          Show this help message and exit

Example:
./configure_billing_alert.py \
    --email name@example.com \
    --name BillingAlert-1000 \
    --threshold 1000
```

### 3. Elastic Compute Cloud

#### check_snapshot_status.py

Checks the current status of one or more existing AWS Elastic Block Store (EBS)
snapshots and displays progress bar(s) with percentage of completion.

```
Usage:
    check_snapshot_status.py [options]

Options:
    -s SNAPSHOTS, --snapshot=SNAPSHOTS
                        The snapshot ID(s) to check status for. This option is
                        required.
    -h, --help          Show this help message and exit

Example:
./check_snapshot_status.py --snapshot snap-012345ab
```

### 4. Elastic Load Balancing

#### configure_ssl_policy.py

Configures certain [recommended](https://wiki.mozilla.org/Security/Server_Side_TLS)
server-side TLS settings for the default HTTPS listener on an Elastic Load
Balancer (ELB). Even though ELB supports latest TLS versions and recommended
ciphers they are not enabled by default for some reasons.

This script enables the most recent and more secure TLS v1.2 and v1.1 versions, strong
ciphers, including ECDHE to enable forward secrecy, and order preferences.

```
Usage:
    configure_ssl_policy.py [options]

Options:
    -l LBS, --load-balancer=LBS
                        A list of AWS load balancers to configure the policy
                        on. This option is required.
    -h, --help          Show this help message and exit

Example:
./configure_ssl_policy.py --load-balancer MyLoadBalancer
```

### 5. Simple Notification Service

#### confirm_subscription.py

Confirms an HTTP(S) endpoint subscription to an Amazon Simple Notification Service
(SNS) topic by visiting the URL specified in the confirmation request from SNS.
It is supposed to run on the endpoint that is going to be subscribed.

```
Usage:
    confirm_subscription.py [options]

Options:
    -p PORT, --port=PORT  The port number to listen on. This option is not
                          required and is set to 8080 by default.
    -s, --ssl             Enable SSL/TLS. This option is not required.
    -k KEY, --key=KEY     A private key file to be used when SSL is enabled.
    -c CERT, --cert=CERT  A certificate file to be used when SSL is enabled.
    -h, --help            Show this help message and exit

Example:
./confirm_subscription.py --port 8080
```

## License

Licensed under the [MIT license](LICENSE).
