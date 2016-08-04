# cfn-sphere
A CLI tool intended to simplify AWS CloudFormation handling.

[![Build Status](https://travis-ci.org/cfn-sphere/cfn-sphere.svg?branch=master)](https://travis-ci.org/cfn-sphere/cfn-sphere)

[![Code Health](https://landscape.io/github/cfn-sphere/cfn-sphere/master/landscape.svg?style=flat)](https://landscape.io/github/cfn-sphere/cfn-sphere/master)

## Features
- cfn templates in yml or json
- build for human interaction and automation (run 'cf sync stacks.yml' triggered by a git push if you dare ;-)
- a source of truth defining cloudformation stacks with their template and parameters
- cross referencing parameters between stacks (use a stack output as parameter for another stack)
- automatic stack dependency resolution including circular dependency detection
- helper features easing the use of cfn functions like Fn::Join, Ref or Fn::GetAtt
- easy user-data definition for https://github.com/zalando-stups/taupage
- allow stack parameter values updates in command line interface 
- encrypt/decrypt values with AWS KMS (https://aws.amazon.com/de/kms/)

## Documentation
**https://github.com/cfn-sphere/cfn-sphere/wiki**

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
            template-url: vpc.yml
        test-stack:
            template-url: app.yml
            parameters:
                vpcID: "|ref|test-vpc.id"

### 2. Write your CloudFormation templates
Write your templates and configure them in your stacks.yml

### 3. Sync it
A simple command synchronizes your definition with reality!

    cf sync myapp-test.yml

#### 3.1 Update Stack with CLI Parameter
To update parameters of a stack without having to modify the templates, simply use the `--parameter` or `-p` flag.

    cf sync --parameter "test-stack.vpcID=vpc-123" --parameter "test-stack.subnetID=subnet-234" myapp-test.yml

## Contribution

* Create an issue to discuss the problem and track changes for future releases
* Create a pull request with your changes (as small as possible to ease code reviews)

## License

Copyright 2015,2016 Marco Hoyer

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.

