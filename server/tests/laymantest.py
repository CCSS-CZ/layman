import unittest

from filemantest import FileManTestCase
from client import ClientTestCase

def suite():
   suite = unittest.TestLoader().loadTestsFromTestCase(FileManTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
   suite = unittest.TestLoader().loadTestsFromTestCase(ClientTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
   pass

if __name__=="__main__":
    suite()
