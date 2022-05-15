import unittest
import doctest
from zonefile_migrate import to_cloudformation


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    test = doctest.DocTestSuite(to_cloudformation)
    suite.addTest(test)
    return suite
