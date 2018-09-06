#!/usr/bin/env python
import sys
from unittest import TextTestRunner
from tests import suite

runner = TextTestRunner(verbosity=2)
ret = not runner.run(suite).wasSuccessful()
sys.exit(ret)
