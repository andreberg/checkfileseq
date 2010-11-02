#!/usr/local/bin/python2.7
# encoding: utf-8
'''
checkfileseq.py

Created by André Berg on 2010-10-23.
Copyright (c) 2010 Berg Media. All rights reserved.
'''

import sys
import os
import re
import locale

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from operator import itemgetter

DEBUG = 0
TESTRUN = 1

# SPLITPAT is used to be consistent internally but is overridable by the user – in main() – through a command line switch.
SPLITPAT = [
    re.compile('''^     # reverse order:
    (?P<seqnum>\d+)     # the sequence number
    (?P<filename>.+)$   # the file name
    ''', re.VERBOSE), 
    re.compile('''^     # normal order:
    (?!\d)              # make sure file name doesn't start with a number
    (?P<filename>.+?)   # the file name
    (?P<seqnum>\d+)$    # the sequence number
    ''', re.VERBOSE)
]
if sys.platform == 'darwin':
    FILEEXCLUDES = [
        ".DS_Store", 
        ".Spotlight-V100", 
        ".Trashes", 
        ".com.apple.timemachine.supported", 
        ".fseventsd", 
        ".syncinfo", 
        ".TemporaryItems", 
        "Desktop DF", 
        "Desktop DB"
    ]
elif sys.platform in ['win32', 'cygwin']:
    FILEEXCLUDES = [
        "thumbs.db",
        "desktop.ini"
    ]
else:
    # Unix-like systems
    # sorry, don't know too much about those special system files there
    FILEEXCLUDES = []

PROGRAM_NAME = "checkfileseq"
PROGRAM_VERSION = "v0.2"
PROGRAM_BUILD_DATE = "2010-10-31"
PROGRAM_VERSION_MESSAGE = '%%(prog)s %s (%s)' % (PROGRAM_VERSION, PROGRAM_BUILD_DATE)
PROGRAM_SHORTDESC = '''checkfileseq — scan directories for file sequences with missing files.'''
PROGRAM_LICENSE = u'''%s

Copyright 2010 André Berg (Berg Media)
Licensed under the MIT License\nwww.opensource.org/licenses/mit-PROGRAM_LICENSE.php
''' % PROGRAM_SHORTDESC

class Error(Exception):
    ''' Generic exception to raise and log different fatal errors. '''
    def __init__(self, msg):
        super(Error).__init__(type(self))
        self.msg = msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

class FileSequenceChecker(object):
    '''
    Class for checking (recursively) a directory with file sequences for missing files.
    
    Modus Operandi
    --------------
    
    Processing happens in three steps:
    
    1. Generate self.dircontents dict by splitting each file name 
       into a name and sequence number part while generating lists 
       for each file sequence present in the dir. 
       We sort these lists in a natural way, first by sequence number, 
       then by file name. This step is also responsible for including 
       or excluding files based on criteria such as command line args 
       (--include/--exclude) and/or FILEEXCLUDES. 
       
       For each directory a file name list is saved, containing tuples 
       which are made of 4 parts:
       
       1. file name, 
       2. sequence number, 
       3. file extension (incl. dot), and 
       4. order 
       
       The order ('normal' or 'reverse') specifies which comes first: 
       file name or sequence number. 
       
       The order must be stored explicitly to be able to print missing 
       file names in a way directly relating to the first file in the 
       sequence. 
       
       It is also worth noting that self.start and self.end do NOT play 
       an important role here. The constraint to files within a particular 
       start and end point from a file sequence is employed and verified 
       only during self.comparefile().
       
    2. Iterate over self.dircontents and and pass from the file name lists 
       tuples representing the current file name parts and the next file name 
       parts from a file sequence to self.comparefile(). 
       
       By comparing both sequence numbers we can determine if files are 
       missing and how many. If files are missing we construct the correct 
       missing file names and add them to lists which are finally added to 
       self.missing, keyed under the path to the currently processed directory.
       
    3. When self.processdir() completes we return self.missing so that the
       caller can process further each dir path with missing files.


    Implementation Notes
    --------------------
    
    As this class has 'Sequence' in its name a strong case was made in the 
    beginning for making it into an iterable object, which for example would 
    then support syntax facilities such as slice notation. 
    
    This approach would have required to split the responsibilities of 
    FileSequenceChecker into at least two classes: 
    a FileSequence object that has information only about the validity 
    of the paths making up one particular file sequence and also stores 
    cross-referenced information about the parts that make up each file 
    name in that sequence, and a DirectoryParser object that builds a 
    list of file sequence candidates for processing later on.
    
    For each encountered file sequence from this previously created, and 
    thus pre-filtered directory list one FileSequence object is created and 
    iterated upon. This iterating cycle would then perform calulation of all 
    missing file names as per current code in self.comparefile(). 
    The pre-filtered list is essentially created the same way as from 
    self.preparedircontents().
    
    While this approach has some elegance to it, from a GTD perspective 
    of creating a command line tool for a very specific purpose, the 
    'divide et impera' approach was abandoned in favour of a one-class-fits-all 
    approach. 
    
    This was also helped by the fact that it became apparent pretty early 
    that there would not be much need for things like slice notation and 
    most internal micro problems could be handled by utilizing standard 
    Python types.    
    '''
    def __init__(self, start=None, end=None, recursive=False):
        self.start = start
        self.end = end
        self.lastfilebarename = u''
        self.nextseqnum = -1
        self.seqnumwidth = -1 # used for %.*s format specifiers in place of the star
        self.splitpat = SPLITPAT
        self.missing = {} # will contain lists with missing sequence numbers keyed by path to the directory containing the files
        self.dircontents = {} # will contain sorted sequence file lists keyed by filepath of the containing directory.
        self.missingfiles = []
        self.fileexcludes = FILEEXCLUDES
        self.excludepat = None
        self.includepat = None
        self.recursive = recursive
    def __repr__(self):
        if self.start:
            start = "start = %s " % str(self.start)
        else:
            start = ""
        if self.end:
            end = "end = %s " % str(self.end)
        else:
            end = ""
        if self.lastfilebarename != u'':
            lastfilebarename = "lastfilebarename = %s " % self.lastfilebarename
        else:
            lastfilebarename = self.lastfilebarename
        if self.nextseqnum != -1:
            nextseqnum = "nextseqnum = %s " % str(self.nextseqnum)
        else:
            nextseqnum = ""
        if self.splitpat != SPLITPAT:
            splitpat = "splitpat = %s " % self.splitpat
        else:
            splitpat = ""
        if self.fileexcludes != FILEEXCLUDES:
            fileexcludes = "fileexcludes = %s " % self.fileexcludes
        else:
            fileexcludes = ""
        if self.excludepat:
            excludepat = "excludepat = %s " % self.excludepat
        else:
            excludepat = ""
        if self.includepat:
            includepat = "includepat = %s " % self.includepat
        else:
            includepat = ""
        if self.missing and len(self.missing) > 0:
            numdirs = len(self.missing.keys())
            numfiles = 0
            for files in self.missing.values():
                numfiles += len(files)
            missing = "missing = %i dir(s)/%i file(s) " % (numdirs, numfiles)
        else:
            missing = ""
        if self.seqnumwidth != -1:
            seqnumwidth = "seqnumwidth = %i " % self.seqnumwidth
        else:
            seqnumwidth = ""
        srepr = "%s " % super(FileSequenceChecker, self).__repr__()
        return "%s%s%s%s%s%s%s%s%s%s%s" % (srepr, start, end, splitpat, fileexcludes, missing, lastfilebarename, nextseqnum, seqnumwidth, excludepat, includepat)
    def __str__(self):
        return repr(self)
    def __unicode__(self):
        return u'%s' % str(self)
    def setfileexcludes(self, files):
        '''
        Set a list of filenames to exclude right away from the 
        sequence number checks. 
        
        Often these are hidden or system files, like .DS_Store 
        on a Mac or thumbs.db on a Windows PC for example.
        '''
        self.fileexcludes = files
    def setexcludepattern(self, pattern):
        '''
        Paths matching this pattern will be excluded from being evaluated,
        e.g. not included in the prepared directory contents.
        
        Note: self.excludepat has precedence over self.includepat.
        '''
        self.excludepat = pattern
    def setincludepattern(self, pattern):
        ''' Only paths matching this regex pattern will be evaluated. '''
        self.includepat = pattern
    def setsplitpattern(self, pattern):
        '''
        Set the regex pattern that will split the filename into name and 
        sequence number parts. 
        
        Must contain two groups: 'filename' and 'seqnum'.
        
        Raises
            Error if pattern doesn't contain both groups.
        '''
        if not re.search(ur'\?P<filename>', pattern):
            if DEBUG: print u"Warning: pattern doesn't include a 'filename' group!"
            raise Error("Error: pattern doesn't include a 'filename' group!")
        if not re.search(ur'\?P<seqnum>', pattern):
            if DEBUG: print u"Warning: pattern doesn't include a 'seqnum' group!"
            raise Error("Error: pattern doesn't include a 'seqnum' group!")
        # chop off quotation marks if present
        firstchar = pattern[0]
        if firstchar == '"' or firstchar == "'":
            pattern = pattern[1:]
        lastchar = pattern[-1]
        if lastchar == '"' or lastchar == "'":
            pattern = pattern[:-1]
        self.splitpat = u'%s' % pattern
    def reset(self):
        ''' Reset the comparance variables to their initial state. '''
        self.lastfilebarename = u''
        self.nextseqnum = -1
        self.seqnumwidth = -1
        self.missingfiles = []
    def splitfilename(self, filename):
        ''' 
        Using self.splitpat split the filename into filename and 
        seqnum part.
        
        self.splitpat can be of type list or of type unicode raw string.
        The list form should contain unicode raw string patterns in reverse 
        order of likely occurrence. The direct unicode raw string pattern 
        form is there to facilitate to ability for the command line user 
        to supply a pattern in a command line argument. 
        
        Internally the list form is the default and will see each pattern 
        used to perform a match so that more file sequence naming cases 
        can be covered – especially when multiple differently named file 
        sequences co-exist in the same directory.
        
        Returns 
            Dict with three entries: a file name, a sequence number and 
            an order, where reverse order is seqnum then filename and 
            normal order is filename then seqnum.
        
        Returns 
            None if no match could be made so that the enclosing loop 
            can continue.
        '''
        if isinstance(self.splitpat, unicode):
            # infer ordering from whichever group name comes first
            fi = re.finditer(ur'(filename|seqnum)', self.splitpat)
            i = 0
            d = {}
            for m in fi:
                d[i] = m.group(0)
                i += 1
            if d[0] == 'filename' and d[1] == 'seqnum':
                order = 'normal'
            elif d[0] == 'seqnum' and d[1] == 'filename':
                order = 'reverse'
            else:
                raise Error("Error: order for split pattern is undefined!")
            match = re.match(self.splitpat, filename)
            if match:
                if len(match.group('filename')) == 0:
                    if DEBUG: print u"%s: filename group is empty. Continuing..." % filename
                elif len(match.group('seqnum')) == 0:
                    if DEBUG: print u"%s: seqnum group is empty. Continuing..." % filename
                else:
                    return {'filename':match.group('filename'), 'seqnum': match.group('seqnum'), 'order': order}
            return None
        elif isinstance(self.splitpat, list):
            i = 0
            for pattern in self.splitpat:
                match = re.match(pattern, filename)
                if match:
                    if i == 0:
                        result = {'filename':match.group('filename'), 'seqnum':match.group('seqnum'), 'order':'reverse'}
                        if DEBUG: print "Setting reverse split order for %s%s" % (result['seqnum'], result['filename'])
                    elif i == 1:
                        if DEBUG: print "Setting normal split order"
                        result = {'filename':match.group('filename'), 'seqnum':match.group('seqnum'), 'order':'normal'}
                    return result
                i += 1
            return None
        else:
            raise Error("Error: self.splitpat is not of type unicode or list.")
    def preparedircontents(self, inpath, verbose=0):
        '''
        Prepare self.dircontents to contain directory contents in 
        naturally sorted lists.
        
        Given a filepath: get the directory contents, split each file 
        into filename and sequence number using self.splitpat and put 
        each directory and it's contents as a list (sorted by numerical 
        value of the sequence number) into self.dircontents, keyed by 
        the directory's filepath.
        '''
        if not os.path.exists(inpath):
            raise Error(u"Error: inpath (%s) doesn't exist!" % inpath)
        if os.path.isdir(inpath):
            for root, _dirs, files in os.walk(inpath):
                sortedfiles = []
                for f in files:
                    filepath = os.path.join(root, f)
                    if not os.path.exists(filepath):
                        raise Error(u"Error: filepath (%s) doesn't exist!" % filepath)
                    if f in self.fileexcludes:
                        continue
                    if self.excludepat and re.search(self.excludepat, filepath):
                        if verbose > 0: print u"Excluding %s" % filepath
                        continue
                    if self.includepat and not re.search(self.includepat, filepath):
                        if verbose > 0: print u"Not including %s" % filepath
                        continue
                    filename, fileext = os.path.splitext(f)
                    nameparts = self.splitfilename(filename)
                    if nameparts:
                        filebarename = nameparts['filename']
                        seqnum = nameparts['seqnum']
                        order = nameparts['order']
                        filenameparts = (filebarename, seqnum, fileext, order)
                        sortedfiles.append(filenameparts)
                        if DEBUG: print u"Matched groups = %s" % str(filenameparts)
                    else:
                        if DEBUG: print u"Result for splitting '%s' with given regex pattern(s) is None. Continuing..." % filename
                        self.reset()
                        continue
                def seqnum_compare(x, y):
                    ''' Compare int value of two sequence numbers. '''
                    return int(x, 10) - int(y, 10)
                def filename_compare(x, y):
                    ''' Compare two file names alphabetically and locale compliant. '''
                    return cmp(locale.strxfrm(x), locale.strxfrm(y))
                sortedfiles = sorted(sortedfiles, key=itemgetter(1), cmp=seqnum_compare) # sort by seqnum
                sortedfiles = sorted(sortedfiles, key=itemgetter(0), cmp=filename_compare) # sort by filename
                self.dircontents[root] = sortedfiles
                if not self.recursive:
                    return
        else:
            raise Error(u"Error: inpath (%s) is not a directory!" % inpath)
    def comparefile(self, dir, curfilenameparts, nextfilenameparts, verbose=0): # IGNORE:W0622
        '''
        Compare one file with the next file in the sequence.
        
        This method is called during processing of the loop which 
        iterates over the file sequences.
        
        Compares self.lastfilebarename and self.nextseqnum to the 
        current filebarename and iseqnum (determined inside this method) 
        and if the nextseqnum is smaller than iseqnum + 1, calulcates 
        the range of the missing files and appends it as list<string> 
        to self.missing.
        
        Returns 
            False if enclosing caller loop should break.
            
        Returns 
            True if enclosing caller loop should continue.
        '''
        filebarename = curfilenameparts[0]
        seqnum = curfilenameparts[1]
        fileext = curfilenameparts[2]
        order = curfilenameparts[3]
        nextfilebarename = nextfilenameparts[0]
        _nextseqnum = nextfilenameparts[1]
        _nextfileext = nextfilenameparts[2]
        _nextorder = nextfilenameparts[3]
        try:
            # Try converting all the numerical strings that we absolutely need as numbers
            iseqnum = int(seqnum, 10)
            if self.start: 
                start = int(self.start, 10)
            if self.end: 
                end = int(self.end, 10)
        except Exception, e: # IGNORE:W0703
            if DEBUG or verbose > 0: print e
            self.reset()
            return True
        if self.start and iseqnum < start:
            if DEBUG or verbose > 0: print "iseqnum (%i) less than start (%i). Continuing..." % (iseqnum, start)
            return True
        if self.end and iseqnum >= end:
            if DEBUG or verbose > 0: print "iseqnum (%i) greater than or equal to end (%i). Stopping iteration..." % (iseqnum, end)
            # If self.end is reached for a file sequence reset state and return True 
            # so that we may continue afresh with the next file sequence from the directory.
            self.reset()
            return True
        if order == 'reverse':
            filename = u"%s%s" % (seqnum, filebarename)
        else:
            filename = u"%s%s" % (filebarename, seqnum) 
        fullfilename = u"%s%s" % (filename, fileext) # (filebarename, seqnum, fileext)
        filepath = os.path.join(dir, fullfilename) 
        if verbose > 0:
            print u"Processing '%s'" % filepath
        if self.seqnumwidth < 0:
            self.seqnumwidth = len(seqnum)
        if DEBUG:                
            print "filename = %s" % filename
            print "filebarename = %s" % filebarename
            print "seqnum = %s" % seqnum
            print "iseqnum = %i" % iseqnum
            print "order = %s" % order
        if self.lastfilebarename == u'':
            # lastfilebarename is empty, which means we are at the beginning of a new file sequence.
            # increment iseqnum into nextseqnum and continue interating.
            self.lastfilebarename = filebarename
            self.nextseqnum = iseqnum + 1
            if self.end and self.nextseqnum > end:
                if DEBUG or verbose > 0: print "self.nextseqnum (%i) greater than end (%i). Stopping iteration..." % (self.nextseqnum, end)
                return False
            else:
                return True
        if self.lastfilebarename == filebarename:
            # Test if the lastfilebarename is not empty 
            # to see if we need to continue checking 
            # this particular file sequence. If the current
            # filebarename doesn't match the lastfilebarename
            # the file sequence has no sucessor so reset
            # comparance variables and continue. 
            if self.nextseqnum > 0 and iseqnum != self.nextseqnum:
                for i in xrange(self.nextseqnum, iseqnum):
                    # Calculate the missing sequence from the diff of iseqnum and self.nextseqnum
                    # iseqnum was just converted to int from seqnum of the last encountered filename
                    # and self.nextseqnum has the next number stored that the last round expected 
                    # to find next so self.nextseqnum, even though named with "next" in it will be 
                    # a lower number
                    if self.end and i > end:
                        return False
                    if order == 'reverse':
                        missingfilename = u"%0.*d%s%s" % (self.seqnumwidth, i, filebarename, fileext)
                    else:
                        missingfilename = u"%s%0.*d%s" % (filebarename, self.seqnumwidth, i, fileext)
                    if DEBUG or verbose > 0: print u"Missing %s" % missingfilename
                    if self.missing.has_key(dir):
                        self.missing[dir].append(missingfilename)
                    else:
                        self.missing[dir] = []
                        self.missing[dir].append(missingfilename)
                # Since we just handled a missing range, adjust the nextseqnum to start after 
                # the end of the missing range
                self.nextseqnum = iseqnum + 1
            else:
                # No missing sequence found. 
                # Continue iterating over the current file sequence based on file bare name.
                self.nextseqnum += 1
            if nextfilebarename != filebarename:
                # Next file(bare)name is not the same as the current,
                # indicating that a new file sequence is beginning.
                self.reset()
            return True
        else:
            self.reset()
        return True
    def processdir(self, inpath, verbose=0):
        ''' Given a root folder, iterate through a sorted file list of the folder's contents. '''
        self.preparedircontents(inpath, verbose)
        if len(self.dircontents) > 0:
            for adir, files in self.dircontents.items():
                if not os.path.exists(adir):
                    # check again to be sure the path did not turn invalid since the last time we checked
                    raise Error(u"Error: dir (%s) doesn't exist!" % adir)
                def pairs(lst):
                    ''' Iterate through a list in pairs. '''
                    i = iter(lst)
                    first = prev = i.next()
                    for item in i:
                        yield prev, item
                        prev = item
                    yield item, first
                for curfile, nextfile in pairs(files):
                    result = self.comparefile(adir, curfile, nextfile, verbose)
                    if result == False:
                        break
                    elif result == True:
                        continue
                    else:
                        break
        else:
            if DEBUG: print "Nothing missing."
        return self.missing


def main(argv=None): # IGNORE:C0111
    if argv is None:
        argv = sys.argv
    try:
        # Setup option parser
        parser = ArgumentParser(description=PROGRAM_LICENSE, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-r", "--recursive", dest="recurse", action="store_true", help="recurse into subfolders [default: %(default)s]")
        parser.add_argument("-f", "--from", dest="rangestart", help="only process files with sequence number greater than NUM  [default: %(default)s]", metavar="NUM")
        parser.add_argument("-t", "--to", dest="rangeend", help="only process files with sequence number less than or equal to NUM [default: %(default)s]", metavar="NUM")
        parser.add_argument("-s", "--splitpat", dest="splitpat", help="regex pattern used for splitting a filename into a name part and a sequence number part. Must contain two groups: 'filename' and 'seqnum'. Note: If you have multiple file sequence in the same dir you should leave this at the default as it covers almost all cases.", metavar="RE")
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument("-i", "--include", dest="include", help="only include paths matching this regex pattern. Note: exclude is given preference over include. [default: %(default)s]", metavar="RE" )
        parser.add_argument("-e", "--exclude", dest="exclude", help="exclude paths matching this regex pattern. [default: %(default)s]", metavar="RE" )
        parser.add_argument('-V', '--version', action='version', version=PROGRAM_VERSION_MESSAGE)
        parser.add_argument(dest="paths", help="paths to folder(s) with file sequence(s) [default: %(default)s]", metavar="path", nargs='+')
        
        # Process options
        args = parser.parse_args()
        paths = args.paths
        verbose = args.verbose
        rangestart = args.rangestart
        rangeend = args.rangeend
        splitpat = args.splitpat
        recurse = args.recurse
        inpat = args.include
        expat = args.exclude
        
        if verbose > 0:
            print "Verbose mode on"
            if recurse:
                print "Recursive mode on"
            else:
                print "Recursive mode off"
        
        if inpat and expat and inpat == expat:
            raise Error(u"Error: include and exclude pattern are equal! Nothing will be processed.")
        
        missing = {}

        for inpath in paths:
            fsc = FileSequenceChecker(rangestart, rangeend, recurse)
            if splitpat:
                fsc.setsplitpattern(unicode(splitpat))
            fsc.setincludepattern(inpat)
            fsc.setexcludepattern(expat)
            missing = fsc.processdir(inpath, verbose)
        raise KeyboardInterrupt
    except KeyboardInterrupt:
        if len(missing) > 0:
            for containingdir, missingfiles in missing.items():
                print u"In %s:" % containingdir
                for missingfile in missingfiles:
                    print u"  Missing %s" % missingfile
    except Exception, e:
        if DEBUG or TESTRUN:
            raise(e)
        print >> sys.stderr, sys.argv[0].split(u"/")[-1] + u": " + unicode(e).decode('unicode_escape')
        print >> sys.stderr, "\t for help use --help"
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-v")
        sys.argv.append("-r")
        #sys.argv.append(u"/Users/andre/test/pics")
        #sys.argv.append("-h")
        #sys.argv.append("/Volumes/Bibliothek/Footage/Compositing for Film and Video Bonus Material/HiDef_Video/Karate_Fight")
        #sys.argv.append("/Volumes/Bibliothek/Footage/Compositing for Film and Video Bonus Material/Film_Scans/Duck")
        sys.argv.append("/Users/andre/test/pics/dir2")
        #sys.argv.append("/Users/andre/test/sort")
    if TESTRUN:
        #sys.argv.append("/Volumes/Bibliothek/Footage/Compositing for Film and Video Bonus Material/HiDef_Video/Closeup_Girl_Clean_Plate")
        #sys.argv.append("/Bibliothek/Footage/Warping_TIF")
        #sys.argv.append("-v")
        #sys.argv.append("-r")
        #sys.argv.append("/Users/andre/test/pics/dir2")
        #sys.argv.append("/Users/andre/test/sort")
        #sys.argv.append("--from=3")
        #sys.argv.append("3")
        #sys.argv.append("--to=15")
        #sys.argv.append("7")
        #sys.argv.append("--splitpat='^(?!\d)(?P<filename>.+?)(?P<seqnum>\d+)$'")
        sys.argv.append("/Users/andre/test/sort/")
    #sys.argv.append("-h")
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)