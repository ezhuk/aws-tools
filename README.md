# AWS Tools

This is a set of auxiliary tools for Amazon Web Services (AWS).

## What's included

### 1. Auto Scaling

#### configure_auto_scaling.py

Configures AWS Auto Scaling to automatically manage system capacity based on
an average CPU usage. It takes care of setting up a new launch configuration
and an auto scaling group, scaling policies and metric alarms to automatically
provision or shutdown one or more EC2 instances if an average CPU utilization
exceeds the maximum threshold or goes below the minimum threshold respectively.

```bash
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

Keeps track of EC2 instances behind [HAProxy](http://haproxy.1wt.eu/) that are
associated with one or more security groups and updates its configuration if
they change. This allows to automatically direct traffic to the currently
running instances and remove the ones that are no longer used.

This tool is supposed to be run periodically (e.g., every minute or so) and
can be configured as a cron job as follows:

```bash
*/1 * * * * user /usr/sbin/haproxy_autoscale.py --group MySecurityGroup
```

#### shutdown_auto_scaling.py

Gracefully shuts down a previously created Auto Scaling configuration. This
script also deletes scaling policies, metric alarms and launch configuration
associated with the specified Auto Scaling group.

```bash
./shutdown_auto_scaling.py --name TEST
```

### 2. Billing

#### check_usage.py

Retrieves AWS usage information for the specified billing period and displays
estimated total charges (including credits, if any). Note that for this to work,
receiving monthly billing reports must be enabled in account preferences.

```bash
./check_usage.py --bucket MyBucket
```

#### configure_billing_alert.py

Sets up a billing alert to keep track of monthly charges across AWS services so
that an email notification gets sent to the specified email address whenever the
estimated monthly charges exceed the specified threshold. Note that metric data
monitoring must be enabled in billing preferences prior to configuring this alert.

```bash
./configure_billing_alert.py \
    --email name@example.com \
    --name BillingAlert-1000 \
    --threshold 1000
```

### 3. Elastic Compute Cloud

#### check_snapshot_status.py

Checks the current status of one or more existing AWS Elastic Block Store (EBS)
snapshots and displays progress bar(s) with percentage of completion.

```bash
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

```bash
./configure_ssl_policy.py --load-balancer MyLoadBalancer
```

### 5. Simple Storage Service

#### compress_object.py

Compresses one or more files stored on Amazon S3. The way it works is that the script
downloads the specified object onto a local filesystem, compresses it using gzip and
then uploads it back on S3. Note that a full path to an S3 object is required.

```bash
./compress_object.py s3://foo/bar
```

### 6. Simple Notification Service

#### confirm_subscription.py

Confirms an HTTP(S) endpoint subscription to an Amazon Simple Notification Service
(SNS) topic by visiting the URL specified in the confirmation request from SNS.
It is supposed to run on the endpoint that is going to be subscribed.

```bash
./confirm_subscription.py --port 8080
```

## License

Licensed under the [MIT license](LICENSE).
