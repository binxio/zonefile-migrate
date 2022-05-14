import unittest
import doctest
from aws_route53_migrate import zone_to_cfn

# is not called...
def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    test = doctest.DocTestSuite(zone_to_cfn)
    suite.addTest(test)
    return suite
