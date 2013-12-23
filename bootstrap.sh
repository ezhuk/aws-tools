#!/bin/bash

# Update system.
sudo yum -q clean all
sudo yum -q makecache
sudo yum -q -y update
