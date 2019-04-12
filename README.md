# cfn-sphere
A CLI tool intended to simplify AWS CloudFormation handling.

[![Build Status](https://travis-ci.org/cfn-sphere/cfn-sphere.svg?branch=master)](https://travis-ci.org/cfn-sphere/cfn-sphere)

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

## Usage

    $ cf --help
    Usage: cf [OPTIONS] COMMAND [ARGS]...
    
      This tool manages AWS CloudFormation templates and stacks by providing an
      application scope and useful tooling.
    
    Options:
      --version  Show the version and exit.
      --help     Show this message and exit.
    
    Commands:
      convert            Convert JSON to YAML or vice versa
      decrypt            Decrypt a given ciphertext with AWS Key
      delete             Delete all stacks in a stack configuration
      encrypt            Encrypt a given string with AWS Key
      render_template    Render template as it would be used to create or update a stack
      sync               Sync AWS resources with stack configuration file
      validate_template  Validate template with CloudFormation API

## Getting Started

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
                dockerImageName: myapp
                appVersion: 1

### 2. Write your CloudFormation templates
Write your templates and configure them in your stacks.yml

### 3. Sync it
A simple command synchronizes your definition with reality!

    cf sync myapp-test.yml

#### 3.1 Update Stack with CLI Parameter
To update parameters of a stack defined within myapp-test.yml without having to modify the templates, simply use the `--parameter` or `-p` flag.

    cf sync --parameter "test-stack.dockerImageName=mytestapp" --parameter "test-stack.appVersion=234" myapp-test.yml

### 4. Go further

Read here to see what cfn-sphere can do for you. There are a lot of things that can help you: 
**https://github.com/cfn-sphere/cfn-sphere/wiki**

## Config Reference

See the wiki to see what you can do in a stack configuration: [StackConfig Reference](https://github.com/cfn-sphere/cfn-sphere/wiki/StackConfig-Reference)

## Template Reference

Cfn-Sphere supports native cloudformation templates written in JSON or YAML, located in local filesystem or s3. There are some improvements like simplified intrinsic functions one can use. See the reference for details: [Template Reference](https://github.com/cfn-sphere/cfn-sphere/wiki/Template-Reference)

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

## Contribution

* Create an issue to discuss the problem and track changes for future releases
* Create a pull request with your changes (as small as possible to ease code reviews)

## License

Copyright Marco Hoyer

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
