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

## Documentation
https://github.com/cfn-sphere/cfn-sphere/wiki

## Install

### As python artifact:

    pip install cfn-sphere

## Build

Requirements:

* python >= 2.6
* virtualenv
* pybuilder

Execute:

    git clone https://github.com/cfn-sphere/cfn-sphere.git
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
