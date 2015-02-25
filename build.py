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
def initialize(project):
    project.depends_on("boto")
    project.depends_on("pyyaml")
    project.depends_on("networkx")

@init
def set_properties(project):
    pass
