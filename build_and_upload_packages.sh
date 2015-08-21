#!/bin/bash
set -e

pyb

cd target/dist/* &&

# deb
fpm \
  --no-python-fix-name \
  --python-install-lib '/usr/lib/python2.7/dist-packages' \
  --python-install-bin '/usr/bin' --no-python-dependencies \
  --depends python --depends python-boto --depends python-click --depends python-networkx --depends python-decorator --depends python-ordereddict --depends python-yaml -s python -t deb setup.py

# rpm
fpm \
  --no-python-fix-name \
  --python-install-lib '/usr/lib/python2.6/site-packages' \
  --python-install-bin '/usr/bin' --no-python-dependencies \
  --depends python --depends python-boto --depends python-click --depends python-networkx --depends python-ordereddict --depends python-yaml -s python -t rpm setup.py

# upload deb and rpm
package_cloud push marco-hoyer/cfn-sphere/scientific/6 *.rpm
package_cloud push marco-hoyer/cfn-sphere/debian/wheezy *.deb
package_cloud push marco-hoyer/cfn-sphere/debian/jessie *.deb
package_cloud push marco-hoyer/cfn-sphere/ubuntu/trusty *.deb

# upload package to pypi
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

python setup.py sdist upload
