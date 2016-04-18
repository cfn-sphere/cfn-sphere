from cfn_sphere.exceptions import CfnSphereException

try:
    from unittest2 import TestCase
    from mock import Mock, MagicMock, patch
except ImportError:
    from unittest import TestCase
    from unittest.mock import Mock, MagicMock, patch

from cfn_sphere.resolver.file import FileResolver


class FileResolverTests(TestCase):
    @patch("cfn_sphere.resolver.file.codecs.open")
    def test_read_raises_cfn_sphere_exception_on_io_error(self, open_mock):
        open_mock.side_effect = IOError()

        with self.assertRaises(CfnSphereException):
            FileResolver.read("foo")
