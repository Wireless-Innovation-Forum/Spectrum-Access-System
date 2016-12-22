import unittest

if __name__ == '__main__':
  tests = unittest.TestLoader().discover('testcases', '*_testcase.py')
  unittest.TextTestRunner().run(tests)
