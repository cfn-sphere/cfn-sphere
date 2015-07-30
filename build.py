from pybuilder.core import use_plugin, init

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.integrationtest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.coverage")
use_plugin("python.distutils")


name = "cfn-sphere"
default_task = "publish"

@init
def set_properties(project):
    project.build_depends_on("unittest2")
    project.build_depends_on("mock")
    project.depends_on("click")
    project.depends_on("boto")
    project.depends_on("pyyaml")
    project.depends_on("networkx")
    project.depends_on('ordereddict')
    project.set_property('coverage_break_build', False)
    project.set_property('install_dependencies_upgrade', True)
    #project.set_property('install_dependencies_index_url', 'http://devppp01.rz.is:5000/dev/dev')

@init(environments='teamcity')
def set_properties_for_teamcity_builds(project):
    import os
    project.set_property('teamcity_output', True)
    project.version = '%s-%s' % (project.version, os.environ.get('BUILD_NUMBER', 0))
    project.default_task = ['clean', 'install_build_dependencies', 'publish']
    project.set_property('install_dependencies_index_url', os.environ.get('PYPIPROXY_URL'))
    project.get_property('distutils_commands').append('bdist_rpm')

