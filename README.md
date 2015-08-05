# cfn-sphere
A CLI tool intended to simplify AWS CloudFormation handling.

## Features
- a "stack of stacks" model to group multiple cfn stacks
- cross referencing parameters between stacks
- automatic stack dependency resolution including circular dependency detection
- write cfn templates in YAML or JSON

## HowTo
### Build

Install:

* python >= 2.6
* virtualenv
* pybuilder

Execute:

	   source my-virtualenv/bin/activate
	   pyb


### Install

ToDo


### Getting Started Guide

#### 1. Create Application Description
Create a YAML file containing a region and some stacks in myapp-test.yml f.e.:

	region: eu-west-1
	stacks:
  		test2-vpc:
    		template: vpc.yml
  		test2-stack:
    		template: app.yml
    		parameters:
      			vpcID: "ref::test2-vpc.id"
      			
#### 2. Write your CloudFormation templates
Write your templates and configure them in your myapp-test.yml.

#### 3. Sync it
A simple command synchronizes your definition with reality!

	cf sync myapp-test.yml