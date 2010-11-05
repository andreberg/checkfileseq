# encoding: utf-8
# pylint: disable=C0103
'''
Created on 01.11.2010

@author: andre
'''
import unittest
#from checkfileseq import *
from checkfileseq import FileSequenceChecker

def printmissing(missingdict):
    ''' 
    human-readable printout of the missing directory 
    returned by FileSequenceChecker.processdir()
    '''
    for _dir, _filelist in missingdict.iteritems():
        print "in %s" % _dir
        for _file in _filelist:
            print _file

class TestFileSequenceCheckerSplitPattern(unittest.TestCase):
    ''' test cases for the split pattern '''
    
    def setUp(self):
        self.fsc1 = FileSequenceChecker()
        self.fsc2 = FileSequenceChecker(10, 20, True)
        self.spat1 = ur'^(?P<filename>\w+?)(?P<seqnum>)(?!\W+)$'
        self.spat2 = ur'^.*?(?P<seqnum>.*?)(?P<filename>\w+?).*?$'
        self.spat1template = ur"%(filename)s%(seqnum)s"
        self.spat2template = ur"%(seqnum)s%(filename)s"
        self.badspat1 = ur'.*$'
        self.badspat2 = r''
        self.filenames = [
            u'1 Name20.png',
            u'01 Name20.png',
            u'01-Name20.png',
            u'01Name20.png',
            u'01Name-20.png',
            u'01Name-20',
            u'01Name',
            u'Name20.01.png',
            u'Name20.01.part01',
            u'Name20.01.001',
            u'Name.01.001',
            u'Name.01001',
            u'-Name.01001',
            u'-Name.01001.png',
            u'-Name001.png',
            u'-N0name001-png'
        ]
        
    def testSetsplitpatternWithNormalInput(self): #IGNORE:C0103
        ''' test changing the split pattern after creation with non-bogus input '''
        self.fsc1.setsplitpattern(self.spat1, self.spat1template)
        self.assertEquals(self.fsc1.splitpat, self.spat1)
        self.fsc2.setsplitpattern(self.spat2, self.spat2template)
        self.assertEqual(self.fsc2.splitpat, self.spat2)
        
    def testReset(self):
        ''' test passing None to setsplitpat in order to reset its to the default state'''
        fsc = FileSequenceChecker()
        fsc.setsplitpattern(self.spat1, self.spat1template)
        fsc.setsplitpattern(None)
        self.assertEqual(fsc.SPLITPAT, fsc.splitpat, 'fsc.splitpat should be reset to FileSequenceChecker.SPLITPAT when fsc.setsplitpattern is called with None as arg')
        
    def testSetsplitpatternWithWrongInput(self): #IGNORE:C0103
        ''' test changing the split pattern after creation with non-bogus but wrong input '''
        self.assertRaises(ValueError, self.fsc1.setsplitpattern, self.badspat1, self.spat1template)
        self.assertRaises(ValueError, self.fsc1.setsplitpattern, self.badspat2, self.spat2template)
        self.assertRaises(ValueError, self.fsc1.setsplitpattern, self.badspat1)
        
    def testDefaultSplitPatternMatches(self):
        ''' test that the default split patterns actually match what they should '''
        for name in self.filenames:
            _fsc = FileSequenceChecker()
            result = _fsc.splitfilename(name)
            self.assertIsNotNone(result)


class TestFileSequenceCheckerOutput(unittest.TestCase):
    ''' test cases with unittest data to verify known output '''
    
    def setUp(self):
        
        self.dirs = {
            'mixed': u'data/mixed_order',
            'normal': u'data/normal_order',
            'reverse': u'data/reverse_order'
        }
        
        self.known_output_for_mixed_order = \
        {u'data/mixed_order': [
            u"2 Write30.png",
            u"4 Write30.png",
            u"5 Write30.png",
            u"-N0name002-png",
            u"-N0name003-png",
            u"Andre\u0301-003.png",
            u"Andre\u0301-004.png",
            u"Andre\u0301-005.png",
            u"Andre\u0301-006.png",
            u"Andre\u0301-007.png",
            u"Andre\u0301-008.png",
            u"Andre\u0301-009.png",
            u"Andre\u0301-010.png",
            u"Andre\u0301-013.png",
            u"Andre\u0301-014.png",
            u"Andre\u0301-002 02.png",
            u"Andre\u0301-002 03.png",
            u"Andre\u0301-002 04.png",
            u"Andre\u0301-002 05.png",
            u"Andre\u0301-002 06.png",
            u"Andre\u0301-002 07.png",
            u"Andre\u0301-002 08.png",
            u"Andre\u0301-002 09.png",
            u"Andre\u0301-002 10.png",
            u"Andre\u0301-002 11.png",
            u"Andre\u0301-002 12.png",
            u"Andre\u0301-002 13.png",
            u"Andre\u0301-002 14.png",
            u"Andre\u0301-002 15.png",
            u"Andre\u0301-002 16.png",
            u"Andre\u0301-002 17.png",
            u"Andre\u0301-002 18.png",
            u"Andre\u0301-002 19.png",
            u"Name20.02.png",
            u"Name20.03.png",
            u"Name20.04.png",
            u"Name20.05.png",
            u"Write30 6.png",
            u"Write30 8.png",
            u"Write30 9.png",
            u"Write30 10.png"
        ]}
        
        self.known_restricted_output_for_mixed_order = \
        {u'data/mixed_order': [
            u"2 Write30.png",
            u"4 Write30.png",
            u"5 Write30.png",
            u"-N0name002-png",
            u"-N0name003-png",
            u"Andre\u0301-003.png",
            u"Andre\u0301-004.png",
            u"Andre\u0301-005.png",
            u"Andre\u0301-006.png",
            u"Andre\u0301-007.png",
            u"Andre\u0301-008.png",
            u"Andre\u0301-009.png",
            u"Andre\u0301-010.png",
            u"Andre\u0301-002 02.png",
            u"Andre\u0301-002 03.png",
            u"Andre\u0301-002 04.png",
            u"Andre\u0301-002 05.png",
            u"Andre\u0301-002 06.png",
            u"Andre\u0301-002 07.png",
            u"Andre\u0301-002 08.png",
            u"Andre\u0301-002 09.png",
            u"Andre\u0301-002 10.png",
            u"Name20.02.png",
            u"Name20.03.png",
            u"Name20.04.png",
            u"Name20.05.png",
            u"Write30 6.png",
            u"Write30 8.png",
            u"Write30 9.png",
            u"Write30 10.png"
        ]}
        
        self.known_output_for_normal_order = \
        {u"data/normal_order": [
            u"Andre\u0301-003.png",
            u"Andre\u0301-004.png",
            u"Andre\u0301-005.png",
            u"Andre\u0301-006.png",
            u"Andre\u0301-007.png",
            u"Andre\u0301-008.png",
            u"Andre\u0301-009.png",
            u"Andre\u0301-010.png",
            u"Andre\u0301-002 02.png",
            u"Andre\u0301-002 03.png",
            u"Andre\u0301-002 04.png",
            u"Andre\u0301-002 05.png",
            u"Andre\u0301-002 06.png",
            u"Andre\u0301-002 07.png",
            u"Andre\u0301-002 08.png",
            u"Andre\u0301-002 09.png",
            u"Andre\u0301-002 10.png",
            u"Andre\u0301-002 11.png",
            u"Andre\u0301-002 12.png",
            u"Andre\u0301-002 13.png",
            u"Andre\u0301-002 14.png",
            u"Andre\u0301-002 15.png",
            u"Andre\u0301-002 16.png",
            u"Andre\u0301-002 17.png",
            u"Andre\u0301-002 18.png",
            u"Andre\u0301-002 19.png",
            u"Version 1.0 - Write Icon 01.r3.png",
            u"Version 1.0 - Write Icon 01.r4.png",
            u"Version 1.0 - Write Icon 01.r5.png",
            u"Version 1.0 - Write Icon 01.r6.png",
            u"Version 1.0 - Write Icon 01.r7.png",
            u"Write30 6.png",
            u"Write30 8.png",
            u"Write30 9.png",
            u"Write30 10.png",
            u"line.004.bmp",
            u"line.005.bmp",
            u"line.006.bmp",
            u"line.007.bmp",
            u"line.008.bmp",
            u"line.009.bmp",
            u"re\u0301sume\u0301.v01.03.png",
            u"re\u0301sume\u0301.v01.04.png",
            u"re\u0301sume\u0301.v01.05.png",
            u"re\u0301sume\u0301.v01.06.png",
            u"re\u0301sume\u0301.v01.07.png",
            u"re\u0301sume\u0301.v01.08.png",
            u"re\u0301sume\u0301.v01.09.png",
            u"re\u0301sume\u0301.v01.10.png",
            u"re\u0301sume\u0301.v01.11.png",
            u"re\u0301sume\u0301.v01.12.png",
            u"re\u0301sume\u0301.v01.13.png",
            u"re\u0301sume\u0301.v01.14.png",
            u"re\u0301sume\u0301.v01.15.png",
            u"re\u0301sume\u0301.v01.16.png",
            u"re\u0301sume\u0301.v01.17.png",
            u"re\u0301sume\u0301.v01.18.png",
            u"re\u0301sume\u0301.v01.19.png",
            u"re\u0301sume\u0301.v01.20.png",
            u"re\u0301sume\u0301.v01.21.png"
        ]}
        
        self.known_restricted_output_for_normal_order = \
        {u"data/normal_order": [
            u"Andre\u0301-003.png",
            u"Andre\u0301-004.png",
            u"Andre\u0301-005.png",
            u"Andre\u0301-006.png",
            u"Andre\u0301-007.png",
            u"Andre\u0301-008.png",
            u"Andre\u0301-009.png",
            u"Andre\u0301-010.png",
            u"Andre\u0301-002 02.png",
            u"Andre\u0301-002 03.png",
            u"Andre\u0301-002 04.png",
            u"Andre\u0301-002 05.png",
            u"Andre\u0301-002 06.png",
            u"Andre\u0301-002 07.png",
            u"Andre\u0301-002 08.png",
            u"Andre\u0301-002 09.png",
            u"Andre\u0301-002 10.png",
            u"Version 1.0 - Write Icon 01.r3.png",
            u"Version 1.0 - Write Icon 01.r4.png",
            u"Version 1.0 - Write Icon 01.r5.png",
            u"Version 1.0 - Write Icon 01.r6.png",
            u"Version 1.0 - Write Icon 01.r7.png",
            u"Write30 6.png",
            u"Write30 8.png",
            u"Write30 9.png",
            u"Write30 10.png",
            u"line.004.bmp",
            u"line.005.bmp",
            u"line.006.bmp",
            u"line.007.bmp",
            u"line.008.bmp",
            u"line.009.bmp",
            u"re\u0301sume\u0301.v01.03.png",
            u"re\u0301sume\u0301.v01.04.png",
            u"re\u0301sume\u0301.v01.05.png",
            u"re\u0301sume\u0301.v01.06.png",
            u"re\u0301sume\u0301.v01.07.png",
            u"re\u0301sume\u0301.v01.08.png",
            u"re\u0301sume\u0301.v01.09.png",
            u"re\u0301sume\u0301.v01.10.png"
        ]}
        
        self.known_output_for_reverse_order = \
        {u"data/reverse_order": [
            u"2 Write30.png",
            u"4 Write30.png",
            u"5 Write30.png",
            u"v13_Write.png",
            u"v14_Write.png",
            u"r101_Write30.png",
            u"r102_Write30.png",
            u"r103_Write30.png",
            u"r104_Write30.png"
        ]}
        
        self.known_restricted_output_for_reverse_order = \
        {u"data/reverse_order": [
            u"2 Write30.png",
            u"4 Write30.png",
            u"5 Write30.png"
        ]}

    
    def testKnownOutputForMixedOrder(self):
        ''' test known output for mixed order data '''
        fsc = FileSequenceChecker()
        output = fsc.processdir(self.dirs['mixed'])
        #printmissing(output)
        #printmissing(self.known_output_for_mixed_order)
        self.assertEquals(output, self.known_output_for_mixed_order)
        
    def testKnownOutputForNormalOrder(self):
        ''' test known output for normal order data '''
        fsc = FileSequenceChecker()
        output = fsc.processdir(self.dirs['normal'])
        #printmissing(output)
        #printmissing(self.known_output_for_normal_order)
        self.assertEquals(output, self.known_output_for_normal_order)
        
    def testKnownOutputForReversedOrder(self):
        ''' test known output for reverse order data '''
        fsc = FileSequenceChecker()
        output = fsc.processdir(self.dirs['reverse'])
        #printmissing(output)
        #printmissing(self.known_output_for_reverse_order)
        self.assertEquals(output, self.known_output_for_reverse_order)
        
    def testRestrictedOutputForMixedOrder(self):
        ''' test range restricted known output for mixed order data '''
        fsc = FileSequenceChecker(start=0, end=10)
        output = fsc.processdir(self.dirs['mixed'])
        #printmissing(output)
        #printmissing(self.known_output_for_mixed_order)
        self.assertEquals(output, self.known_restricted_output_for_mixed_order)
        
    def testRestrictedOutputForNormalOrder(self):
        ''' test range restricted known output for normal order data '''
        fsc = FileSequenceChecker(start=0, end=10)
        output = fsc.processdir(self.dirs['normal'])
        #printmissing(output)
        #printmissing(self.known_output_for_normal_order)
        self.assertEquals(output, self.known_restricted_output_for_normal_order)
        
    def testRestrictedOutputForReversedOrder(self):
        ''' test range restricted known output for reverse order data '''
        fsc = FileSequenceChecker(start=0, end=10)
        output = fsc.processdir(self.dirs['reverse'])
        #printmissing(output)
        #printmissing(self.known_output_for_reverse_order)
        self.assertEquals(output, self.known_restricted_output_for_reverse_order)
        
    def testGetitem(self):
        ''' test __getitem__ based notation for the missing results '''
        fsc = FileSequenceChecker(recursive=True)
        self.assertIsNone(fsc[self.dirs['mixed']], "should be None when processdir wasn't run yet.")
        fsc.processdir(self.dirs['mixed'])
        self.assertIsNotNone(fsc[self.dirs['mixed']])
        

class TestFileSequenceCheckerCreation(unittest.TestCase):
    ''' test cases for FileSequenceChecer creation with default and non-default arguments '''
    
    def testDefaultCreation(self):
        ''' test creation of FileSequenceChecker with various options. '''
        fsc = FileSequenceChecker()
        self.assertIsNotNone(fsc, "fsc should not be None")
        self.assertEquals(fsc.start, None, "fsc.start should equal None upon creation.")
        self.assertEquals(fsc.end, None, "fsc.end should equal None upon creation.")
        self.assertEquals(fsc.recursive, False, "fsc.recursive should equal False upon creation.")

    def testNonDefaultCreation(self):
        ''' test creation with non-default values '''
        fsc = FileSequenceChecker(start=10, end=20, recursive=True)
        self.assertIsNotNone(fsc, "fsc should not be None")
        self.assertEquals(fsc.start, 10, "fsc.start should equal 10 upon creation.")
        self.assertEquals(fsc.end, 20, "fsc.end should equal 20 upon creation.")
        self.assertEquals(fsc.recursive, True, "fsc.recursive should equal True upon creation.")
        fsc2 = FileSequenceChecker(end=10)
        self.assertEquals(fsc2.start, None, "fsc2.start should equal None upon creation if only end specified.")
        fsc3 = FileSequenceChecker(start=10)
        self.assertEquals(fsc3.end, None, "fsc3.end should equal None upon creation if only start specified.")

        

class TestFileSequenceCheckerBogusCreation(unittest.TestCase):
    ''' test cases for creating the FileSequenceChecker with bogus arguments '''
    
    def testNegativeValues(self):
        ''' test creation with negative range values '''
        self.assertRaises(ValueError, FileSequenceChecker, start=-10, end=10)
        self.assertRaises(ValueError, FileSequenceChecker, start=1, end=-10)

    def testInvalidRangeValues(self):
        ''' test creation with invalid range values '''
        self.assertRaises(ValueError, FileSequenceChecker, start=10, end=10)
        self.assertRaises(ValueError, FileSequenceChecker, start=10, end=9)
        
    def testInvalidRecursiveValues(self):
        ''' test creation with invalid recursive values '''
        self.assertRaises(ValueError, FileSequenceChecker, recursive=None)
        self.assertRaises(ValueError, FileSequenceChecker, recursive=dict())
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()