#!/bin/bash
set -e

# set build number to 0 if not run on circle ci
export CIRCLE_BUILD_NUM=${CIRCLE_BUILD_NUM:-0}

pyb

cd target/dist/* &&

fpm \
  --iteration $CIRCLE_BUILD_NUM \
  --python-install-lib '/usr/lib/python2.7/site-packages' \
  --python-install-bin '/usr/bin' --no-python-dependencies \
  --depends 'python>=2.7' --depends python-boto --depends python-click --depends python-networkx --depends python-ordereddict --depends python-yaml -s python -t deb setup.py

fpm \
  --iteration $CIRCLE_BUILD_NUM \
  --python-install-lib '/usr/lib/python2.7/dist-packages' \
  --python-install-bin '/usr/bin' --no-python-dependencies \
  --depends 'python>=2.7' --depends python-boto --depends python-click --depends python-networkx --depends python-ordereddict --depends python-yaml -s python -t rpm setup.py

package_cloud push marco-hoyer/cfn-sphere/scientific/6 *.rpm
package_cloud push marco-hoyer/cfn-sphere/debian/wheezy *.deb
package_cloud push marco-hoyer/cfn-sphere/debian/jessie *.deb
