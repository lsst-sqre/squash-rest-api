"""Initialize SQuaSH API test suite."""

import unittest

from .tests import TestAPI

suite = unittest.TestLoader().loadTestsFromTestCase(TestAPI)
