#!/bin/bash
set -e

# set build number to 0 if not run on circle ci
export CIRCLE_BUILD_NUM=${CIRCLE_BUILD_NUM:-0}

pyb

cd target/dist/* &&

# deb
fpm \
  --iteration $CIRCLE_BUILD_NUM \
  --no-python-fix-name \
  --python-install-lib '/usr/lib/python2.7/dist-packages' \
  --python-install-bin '/usr/bin' --no-python-dependencies \
  --depends 'python>=2.7' --depends python-boto --depends python-click --depends python-networkx --depends python-ordereddict --depends python-yaml -s python -t deb setup.py

# rpm
fpm \
  --iteration $CIRCLE_BUILD_NUM \
  --no-python-fix-name \
  --python-install-lib '/usr/lib/python2.7/site-packages' \
  --python-install-bin '/usr/bin' --no-python-dependencies \
  --depends 'python>=2.7' --depends python-boto --depends python-click --depends python-networkx --depends python-ordereddict --depends python-yaml -s python -t rpm setup.py

#pypi
if [ -n "$PYPI_USER" ] && [ -n "$PYPI_PASSWORD" ]; then
    echo "Generating pypi auth config"
    cat > ~/.pypirc << EOF
[distutils]
index-servers =
    pypi

[pypi]
username:$PYPI_USER
password:$PYPI_PASSWORD
EOF
fi

python setup.py sdist upload || exit 0

# upload
package_cloud push marco-hoyer/cfn-sphere/scientific/6 *.rpm
package_cloud push marco-hoyer/cfn-sphere/debian/wheezy *.deb
package_cloud push marco-hoyer/cfn-sphere/debian/jessie *.deb
package_cloud push marco-hoyer/cfn-sphere/debian/precise *.deb