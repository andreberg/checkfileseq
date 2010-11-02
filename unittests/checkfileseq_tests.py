'''
Created on 01.11.2010

@author: andre
'''
import unittest
#from checkfileseq import *
import checkfileseq
from checkfileseq import FileSequenceChecker

class Test(unittest.TestCase):


    def setUp(self):
        self.fsc1 = FileSequenceChecker()


    def tearDown(self):
        pass


    def testCreation(self):
        ''' test creation of FileSequenceChecker with various options. '''
        self.assertIsNotNone(self.fsc1, "self.fsc1 should not be None")
        self.assertEquals(self.fsc1.start, None, "self.fsc1.start should equal None upon creation.")
        self.assertEquals(self.fsc1.end, None, "self.fsc1.end should equal None upon creation.")
        self.assertEquals(self.fsc1.recursive, False, "self.fsc1.recursive should equal False upon creation.")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()