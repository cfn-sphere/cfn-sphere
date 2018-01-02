#!/usr/bin/env bash
set -x

cd /cfn
pip install pybuilder
pyb install_dependencies
pyb -X run_integration_tests