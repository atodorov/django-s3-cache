#!/usr/bin/env python

import os
import sys
import unittest

dirname = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dirname, ".."))

class TestOne(unittest.TestCase):
    def test_simple(self):
        self.assertTrue(1 == 1)

if __name__ == '__main__':
    unittest.main()
