#!/usr/bin/env python

from pybuilder.core import use_plugin, init, Author

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.integrationtest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.coverage")
use_plugin("python.distutils")
use_plugin('copy_resources')
use_plugin('filter_resources')

name = "cfn-sphere"

authors = [Author('Marco Hoyer', 'marco_hoyer@gmx.de')]
description = "cfn-sphere - A CLI tool intended to simplify AWS CloudFormation handling."
license = 'APACHE LICENSE, VERSION 2.0'
summary = 'cfn-sphere AWS CloudFormation management cli'
url = 'https://github.com/cfn-sphere/cfn-sphere'
version = '1.0.0'

default_task = ['clean', 'analyze', 'package']


@init
def set_properties(project):
    project.build_depends_on("unittest2")
    project.build_depends_on("mock")
    project.build_depends_on("moto")
    project.depends_on('six')
    project.depends_on("click")
    project.depends_on("boto3", version=">=1.4.1")
    project.depends_on("pyyaml")
    project.depends_on("networkx")
    project.depends_on('prettytable')
    project.depends_on('gitpython')
    project.depends_on('jmespath')
    project.set_property('integrationtest_inherit_environment', True)
    project.set_property('coverage_break_build', False)
    project.set_property('install_dependencies_upgrade', True)

    project.set_property('copy_resources_target', '$dir_dist')

    project.get_property('filter_resources_glob').extend(['**/cfn_sphere/__init__.py'])
    project.set_property('distutils_console_scripts', ['cf=cfn_sphere.cli:main'])

    project.set_property('distutils_classifiers', [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: System :: Systems Administration'
    ])


@init(environments='teamcity')
def set_properties_for_teamcity_builds(project):
    import os

    project.set_property('teamcity_output', True)
    project.version = '%s-%s' % (project.version, os.environ.get('BUILD_NUMBER', 0))
    project.default_task = ['clean', 'install_build_dependencies', 'publish']
    project.set_property('install_dependencies_index_url', os.environ.get('PYPIPROXY_URL'))
    project.get_property('distutils_commands').append('bdist_rpm')
