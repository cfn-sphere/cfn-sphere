# cfn-sphere
A CLI tool intended to simplify AWS CloudFormation handling.

[![Build Status](https://travis-ci.org/cfn-sphere/cfn-sphere.svg?branch=master)](https://travis-ci.org/cfn-sphere/cfn-sphere) (master) | 
[![Build Status](https://travis-ci.org/cfn-sphere/cfn-sphere.svg?branch=stable)](https://travis-ci.org/cfn-sphere/cfn-sphere) (stable)

## Features
- cfn templates in yml or json
- build for human interaction and automation (run 'cf sync stacks.yml' triggered by a git push if you dare ;-)
- a source of truth defining cloudformation stacks with their template and parameters
- cross referencing parameters between stacks (use a stack output as parameter for another stack)
- automatic stack dependency resolution including circular dependency detection
- helper features easing the use of cfn functions like Fn::Join, Ref or Fn::GetAtt
- easy user-data definition for https://github.com/zalando-stups/taupage

## Install

### As python artifact:

**This might be the easiest solution for you**

    pip install cfn-sphere

### Debian / Ubuntu Packages:

**.deb packages are untested right now! Use Python artifacts instead!**

Install repo gpg key and required package:

    curl https://packagecloud.io/gpg.key | apt-key add -
    apt-get install -y apt-transport-https

Put a file named /etc/apt.sources.list.d/cfn-sphere.list with the following content if your distro version is wheezy:

    deb https://packagecloud.io/marco-hoyer/cfn-sphere/debian/ wheezy main
    deb-src https://packagecloud.io/marco-hoyer/cfn-sphere/debian/ wheezy main

Install package:

    sudo apt-get install cfn-sphere

### RHEL6 RPM:

    sudo yum install pygpgme

Put a file named /etc/yum.repos.d/cfn-sphere.repo with the following content:

    [cfn-sphere]
    name=cfn-sphere
    baseurl=https://packagecloud.io/marco-hoyer/cfn-sphere/el/6/$basearch
    repo_gpgcheck=1
    gpgcheck=0
    enabled=1
    gpgkey=https://packagecloud.io/gpg.key
    sslverify=1
    sslcacert=/etc/pki/tls/certs/ca-bundle.crt

Install package:

    sudo yum install cfn-sphere


## Build

Requirements:

* python >= 2.6
* virtualenv
* pybuilder

Execute:

    git clone https://github.com/marco-hoyer/cfn-sphere.git
    cd cfn-sphere
    virtualenv .venv --python=python2.7
    source .venv/bin/activate
    pip install pybuilder
    pyb install_dependencies
    pyb


## Getting Started Guide

### 1. Create Stacks Config
Create a YAML file containing a region and some stacks in a stacks.yml file f.e.:

    region: eu-west-1
    stacks:
        test-vpc:
            template: vpc.yml
        test-stack:
            template: app.yml
            parameters:
                vpcID: "|ref|test-vpc.id"

### 2. Write your CloudFormation templates
Write your templates and configure them in your stacks.yml

### 3. Sync it
A simple command synchronizes your definition with reality!

    cf sync myapp-test.yml
