#!/usr/bin/env bash
set -x

docker run -it -v "$(pwd):/cfn" -v "$HOME/.aws:/root/.aws" --entrypoint /cfn/bin/execute_integration_tests.sh python:2.7
