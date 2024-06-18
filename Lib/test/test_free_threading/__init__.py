import os

from test import support


@support.skipUnless(support.Py_GIL_DISABLED, "GIL enabled")
def load_tests(*args):
    return support.load_package_tests(os.path.dirname(__file__), *args)
