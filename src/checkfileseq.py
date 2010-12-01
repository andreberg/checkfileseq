#!/usr/local/bin/python2.7
# encoding: utf-8
# pylint: disable=C0302
'''
checkfileseq -- scan directories for file sequences with missing files

checkfileseq is a command line tool for scanning directories that contain
file sequences (e.g. C{file.001.png, image.002.png, ... image.NNN.png}, etc.)
and determine if each file sequence present is complete. 

It defines one class L{FileSequenceChecker} which does all the processing.

@author:     André Berg
             
@copyright:  2010 Berg Media. All rights reserved.
             
@license:    Licensed under the Apache License, Version 2.0 (the "License");\n
             you may not use this file except in compliance with the License.
             You may obtain a copy of the License at
             
             U{http://www.apache.org/licenses/LICENSE-2.0}
             
             Unless required by applicable law or agreed to in writing, software
             distributed under the License is distributed on an B{"AS IS"} B{BASIS},
             B{WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND}, either express or implied.
             See the License for the specific language governing permissions and
             limitations under the License.

@deffield    updated: Updated
'''

import sys
import os
import re
import time

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from operator import itemgetter

__all__ = ['FileSequenceChecker', 'CLIError']
__version__ = 0.2
__date__ = '2010-11-06'
__updated__ = '2010-12-01'
__docformat__ = "epytext"

DEBUG = 0
TESTRUN = 0
PROFILE = 0 or (os.environ.has_key('BMProfileLevel') and os.environ['BMProfileLevel'] > 0)

class CLIError(Exception):
    ''' Generic CLI exception. Raised for logging different fatal errors. '''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg.decode('utf-8')
    def __str__(self):
        return self.msg.encode('utf-8')
    def __unicode__(self):
        return self.msg

class FileSequenceChecker(object):
    '''
    FileSequenceChecker
    ===================
    
    A class for (recursively) checking a directory with file sequences for missing files.
    
    Modus Operandi
    --------------
    
    Processing happens in three steps:
    
        1. Generate a directory contents dict by splitting each file name 
           into a name and sequence number part when generating lists 
           for each file sequence present in the dir. 
           We sort these lists in a natural way, first by sequence number, 
           then by file name. This step is also responsible for including 
           or excluding files based on criteria such as command line args 
           (C{--include/--exclude}) and/or L{FILEEXCLUDES}. 
           
           For each directory a file name list is saved, containing dicts
           with 5 keys:
           
               1. file name (C{filename}), 
               2. sequence number (C{seqnum}), 
               3. file extension (incl. dot) (C{fileext}), 
               4. order (C{order}),
               5. file name, 2nd part (optional) (C{filename2})
               
           The order (C{normal} or C{reverse}) specifies which comes first: 
           file name or sequence number. To explain why this is needed, let's
           first look at the final (optional) part:
           
           A fifth key, C{filename2}, may exist which contains the second file 
           name part. This part will be re-inserted again (placed according to
           the correct order) when constructing the missing file names as part 
           of creating the lists of missing files.
           
           The order must be stored explicitly to be able to construct missing 
           file names in a way directly relating to the part order found in the 
           first file of a sequence. 
           
           It may also be worth noting that L{self.start} and L{self.end} do 
           B{NOT} play an important role here. The constraining to files within 
           a particular start and end interval is utilized and verified later 
           within the comparing function.
           
        2. Iterate over the prepared directory contents and from each file name list
           pass dicts representing current file name parts and next file name parts 
           to a comparing function. 
           
           By comparing clues from both dictionaries we can determine if files are 
           missing and how many. Lists with missing file names are created on
           a per directory basis. Each list is then added to a dictionary, keyed 
           by path to the directory that's currently processed.
           
        3. L{self.processdir()} returns this dictionary, or an empty dictionary 
           if no there are no missing files, so that the caller can further do her
           own processing.
           
    Caveats
    -------
    
    Even after careful testing and development, there are still some caveats left.
    These are mostly coming from not being able to do everything automatically and 
    then hide it away as implementation detail, especially when faced with inherent
    ambiguities. 
    
    For example: certain file names are just not distuingishable enough to match one
    default regex pattern over the other. This is because from a regex based matching 
    perspective strings like C{v105-name} and C{name-v105} are just too similar. 
    Think about it: to match the first string you could say: match any lowercase letter 
    followed by a number. 
    
    But can you be sure that you will always need to match just one lowercase letter? 
    I would argue you can't. Then you say: match any lowercase letter any number of 
    times followed by a number. If you now compare this with the second string you 
    will find that this definition will match both strings. Of course you can mess
    around with "rooting" to different sides of the string (C{^} vs. C{$}) and also 
    impose a superficial ordering of less-likely to likely when applying different 
    patterns, but fundamentally there will always be a at least one case that is 
    too ambiguous compared to another case.
    
    Ambiguities like these are hard to resolve by automation. Any good API will defer 
    these decisions to the user of the class and thus delegate the choice to the one 
    who should know most about specific needs.
    
    In the case of the CLI that L{FileSequenceChecker} was originally made for, 
    command line arguments give the end user the ability to define a pattern and 
    a replacement template themselves, so as to cover these special cases. 

    Example Use
    -----------
    
    The following example recursively processes some directory 
    and only looks at files from a file sequence which have 
    sequence numbers within the range 0 through 10. 
    
        >>> somedir = 'unittests/data/reverse_order'
        >>> fsc = FileSequenceChecker(0, 10) 
        >>> missing = fsc.processdir(somedir)
        >>> if len(missing) > 0:
        ...     for containingdir, missingfiles in missing.items():
        ...         print u"In '%s':" % containingdir
        ...         for missingfile in missingfiles:
        ...             print u"  Missing %s" % missingfile
        In 'unittests/data/reverse_order':
          Missing 2 Write30.png
          Missing 4 Write30.png
          Missing 5 Write30.png

    A L{FileSequenceChecker} instance is key subscriptable.
    If the instance's C{missing} attribute (a dict with the 
    pathnames for dirs with missing files as keys) has an
    entry for a given path it will return a list of file
    names for all missing files under that path. E.g.:
        
        >>> print fsc[somedir]
        [u'2 Write30.png', u'4 Write30.png', u'5 Write30.png']
        
    You can also ask a L{FileSequenceChecker} instance for the 
    total amount of missing files detected:
    
        >>> print fsc.totalfiles
        3
    
    If you want to know how many dirs there were with missing 
    files:
    
        >>> print fsc.totaldirs
        1
    
    You can get the amount of time in fractional seconds that
    L{self.processdir()} took by calling C{fsc.lastexectime} and 
    it will return it as a C{float} value.
    
        
    Implementation Notes
    --------------------
    
    As this class has I{Sequence} in its name, a strong case was made 
    initially when designing the class, for making it into an iterable 
    object, which, for example, would then support Pythonic syntax 
    facilities such as slice notation among others. In other words:
    to treat the L{FileSequenceChecker} as a sequence-like proxy object 
    that would delegate all the functionality that's required for the
    problem domain of the CLI implementation to standard Python sequence
    objects like lists, tuples etc.  
    
    However, this approach would have required to split the responsibilities 
    of L{FileSequenceChecker} into at least two classes:
     
    a C{FileSequence} object that has information only about the validity 
    of the paths making up one particular file sequence and also stores 
    cross-referenced information about the parts that make up each file 
    name in that sequence, and a C{DirectoryParser} object that builds a 
    list of file sequence candidates for processing later on.
    
    For each encountered file sequence from this previously created, and 
    thus pre-filtered directory list, one C{FileSequence} object is created 
    and iterated upon. This iterating cycle would then perform calulation 
    of all missing file names in the same way as done currently in the 
    comparing function.
    
    While this approach has some elegance to it, from a I{getting-things-done} 
    perspective of creating a command line tool for a very specific purpose, 
    the I{'divide et impera'} approach was abandoned in favour of a 
    I{one-class-fits-all} design. 
    
    This was also helped by the fact that it became apparent pretty early 
    that there would not be much need for things like slice notation and 
    most internal micro problems could be handled by utilizing standard 
    Python types.
    
    @ivar start: only process files with sequence number values greater 
                 than this number
    @type start: C{int}
    @ivar end: only process files with sequence number values less than 
               or equal to this number 
    @type end: C{int}
    @ivar recursive: process sub directories
    @type recursive: C{bool}
    @ivar fullpaths: index missing file lists by absolute paths instead 
                     of relative paths
    @type fullpaths: C{bool}
    '''

    SPLITPAT = [ #: default split patterns
        {
            'pattern':
                re.compile(ur'''^   # reverse order: start with digit(s)
                (?=\d)              # make sure line begins with a number
                (?P<seqnum>\d+?)    # the sequence number
                (?P<filename>.+)    # the file name
                ''', re.VERBOSE),
            'order':
                'reverse'
        },
        {
            'pattern':
                re.compile(ur'''^   # reverse order 2: start with non-digit filename part, 
                                    # immediatly followed by digit(s) then more filename parts
                (?P<filename2>\D)   # a single non-number character: handles NNN-filename.png for example
                (?P<seqnum>\d+)     # the sequence number
                (?P<filename>.*?)   # the file name
                (?=\b)              # justify to end non-word boundary
                ''', re.VERBOSE),
            'order':
                'reverse'
        },
        {
            'pattern':
                re.compile(ur'''    # normal order:
                (?!\d)              # make sure file name doesn't start with a number
                (?P<filename>.+?)   # the file name
                (?P<seqnum>\d+)     # the sequence number
                (?P<filename2>\D*?) # second filename part (optional)
                $
                ''', re.VERBOSE),
            'order':
                'normal'
        }
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
            "Thumbs.db",
            "desktop.ini"
        ]
    else:
        # Unix-like systems
        # sorry, don't know too much about those special system files there
        FILEEXCLUDES = []
        
    __all__ = [
        "setfileexcludes", 
        "setincludepattern", 
        "setexcludepattern", 
        "setsplitpattern", 
        "processdir"
    ]
    
    def __init__(self, start=None, end=None, recursive=False, fullpaths=False):
        super(FileSequenceChecker, self).__init__()
        if isinstance(start, basestring):
            try:
                start = int(start.strip(), 10)
            except Exception:
                raise ValueError("E: start must be of type int or convertible to type int")
        elif isinstance(start, int) and start < 0:
            raise ValueError("E: invalid number: start must be positive")
        if isinstance(end, basestring):
            try:
                end = int(end.strip(), 10)
            except Exception:
                raise ValueError("E: end must be of type int or convertible to type int")
        elif isinstance(end, int) and end < 0:
            raise ValueError("E: invalid number: end must be positive")
        if isinstance(start, int) and isinstance(end, int):
            if start >= end:
                raise ValueError("E: invalid range: start is greater than or equal to end")          
        if not isinstance(recursive, (bool, int)):
            raise ValueError("E: 'recursive' must be of type bool/int")
        if not isinstance(fullpaths, (bool, int)):
            raise ValueError("E: 'fullpaths' must be of type bool/int")
        
        # public 
        self.start = start                  #: only process files with sequence number values greater than this number
        self.end = end                      #: only process files with sequence number values less than or equal to this number 
        self.recursive = bool(recursive)    #: process sub directories
        self.fullpaths = bool(fullpaths)    #: index missing file lists by absolute paths instead of relative paths
        
        # private
        self.lastfilebarename = ''          # the last file name, bare, that is without the sequence number part
        self.nextseqnum = -1                # the next sequence number to expect
        self.seqnumwidth = -1               # used for %.*s format specifiers in place of the star
        self.splitpat = self.SPLITPAT       # the pattern(s) to be used to split a file name into name and sequence number
        self.missing = {}                   # will hold a list of all the missing file names, keyed by path to the directory containing them.
        self.template = None                # a format string which must contain dict key-based replacement tokens for each named group of a custom splitpat. 
        self.dircontents = {}               # will contain sorted sequence file lists keyed by filepath of the containing directory.
        self.missingfiles = []              # holds a list of all missing files per one processed directory.
        self.fileexcludes = self.FILEEXCLUDES
        self.excludepat = None              # file names with paths matching this pattern will be excluded from being processed. overrides self.includepat. 
        self.includepat = None              # only file names with paths matching this pattern will be included in processing
        self.strictmatching = False         # if True uses re.match instead of re.search internally
        self.lastexectime = -1              # how long did the last call of processdir take
    def __str__(self):
        if isinstance(self.start, int):
            start = "start = %i " % self.start
        else:
            start = ""
        if isinstance(self.end, int):
            end = "end = %i " % self.end
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
        if self.splitpat != self.SPLITPAT:
            splitpat = "splitpat = %s " % self.splitpat
        else:
            splitpat = ""
        if self.fileexcludes != self.FILEEXCLUDES:
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
        if self.template:
            template = self.template
        else:
            template = ""
        if self.recursive:
            recursive = "recursive = True "
        else:
            recursive = ""
        if self.fullpaths:
            fullpaths = "fullpaths = True "
        else:
            fullpaths = ""
        srepr = "%s " % super(FileSequenceChecker, self).__repr__()
        return "%s%s%s%s%s%s%s%s%s%s%s%s%s%s" % \
                (srepr, start, end, splitpat, template, fileexcludes, missing, \
                 lastfilebarename, nextseqnum, seqnumwidth, excludepat, includepat, recursive, fullpaths)
    def __repr__(self):
        return "FileSequenceChecker(start=%s, end=%s, recursive=%s, fullpaths=%s)" % \
                (str(self.start), str(self.end), str(self.recursive), str(self.fullpaths)) 
    def __unicode__(self):
        return u'%s' % str(self)
    def __getitem__(self, key):
        if self.missing and self.missing.has_key(key):
            return self.missing[key]
        else:
            return None
    def __len__(self):
        numfiles = 0
        for files in self.missing.values():
            numfiles += len(files)
        return numfiles
    def __getattr__(self, attr):
        if attr == "totaldirs":
            return len(self.missing.keys())
        elif attr == "totalfiles":
            numfiles = 0
            for files in self.missing.values():
                numfiles += len(files)
            return numfiles
        elif attr == "totalprocessed":
            numprocessed = 0
            for files in self.dircontents.values():
                numprocessed += len(files)
            return numprocessed
        else:
            return None
    def setfileexcludes(self, filenames, extend=True):
        '''
        Set a list of file names to be excluded from being 
        evaluated.
        
        Often these are hidden or system files, like C{.DS_Store} 
        on a Mac or C{Thumbs.db} on a Windows PC for example.
        
        @param filenames: a list of file names
        @type filenames: C{list}
        @param extend: should the default list be extended 
                       or replaced?
        @type extend: C{bool}
        '''
        if extend: 
            self.fileexcludes.extend(filenames)
        else:
            self.fileexcludes = filenames
    def setexcludepattern(self, pattern):
        '''
        Paths matching this pattern will be excluded from being evaluated,
        e.g. not included in the prepared directory contents.
        
        @note: excluding has precedence over including.
        @param pattern: a regex pattern
        @type pattern: C{regex}
        '''
        self.excludepat = pattern
    def setincludepattern(self, pattern):
        ''' Only paths matching this regex pattern will be evaluated. '''
        self.includepat = pattern
    def setsplitpattern(self, pattern, template=None):
        '''
        Set the regex pattern that will split the file name into name and 
        sequence number parts. 
        
        Must contain two named groups: C{filename} and C{seqnum} where
        the first should match the file name part and the second should
        match the sequence number part. Can optionally contain a third
        named groupd C{filename2} for cases where the sequence number
        splits the filename in half.
        
        If a custom pattern is supplied as raw unicode string, template
        B{cannot} be C{None}.
        
        @note: will attempt to sanitize the pattern, for example by doing 
        things like chopping off single and double quotation marks 
        (if present) at the beginning and end of the pattern string.        
        @param pattern: a list of unicode regex patterns or a unicode 
                        string to be used as the regex pattern.
        @type pattern: C{list of unicode} or C{unicode} 
        @param template: format string with dict-based replacement tokens 
                         (e.g. C{%s(I{<key_name>})s}) that correspond to the 
                         named groups given in the pattern. Must not be C{None}
                         if pattern is of type C{unicode}!
        @type template: C{unicode}
        @raise ValueError: if the regex pattern doesn't contain one 
                           named regex group called C{filename} and 
                           one named group called C{seqnum}.
        '''
        def verifytemplate(pt, tp):
            ''' 
            Utility function for verifying that the format template contains
            replacement tokens for each named group of the pattern.
            
            @param pt: the regex pattern
            @type pt: C{regex}
            @param t: the template format string
            @type t: C{string}
            @raise ValueError: if a key is missing for a named group.
            @return: True if everything seems in order.
            @rtype: C{bool}
            ''' 
            fiter = re.finditer(ur'\?P<(.*?)>', pt)
            for i in fiter:
                key = i.group(1)
                if not re.search(ur"\b%s\b" % key, tp):
                    raise ValueError("E: key %s not found in template (%s)" % (key, tp))
            return True
        def sanitizepattern(pat):
            '''
            Utility function for sanitizing a regex pattern.
            
            @param pat: regex pattern
            @type pat: C{regex}
            @raise ValueError: if the pattern is an empty string, or
                               if the pattern doesn't contain a named 'filename' group, or
                               if the pattern doesn't contain a named 'seqnum' group.
            @note: if the pattern is wrapped in single or double quotes,
                   tries to chop them off so that the unquoted string remains. 
            @return: the sanitized pattern.
            @rtype: C{unicode}
            '''
            # chop off quotation marks if present
            if len(pat) == 0:
                raise ValueError("E: pattern string is empty")
            firstchar = pat[0]
            if firstchar == '"' or firstchar == "'":
                pat = pat[1:]
            lastchar = pat[-1]
            if lastchar == '"' or lastchar == "'":
                pat = pat[:-1]
            if not re.search(ur'\?P<filename>', pat):
                if DEBUG:
                    print "Warning: pattern doesn't include a 'filename' group!"
                raise ValueError("E: pattern doesn't include a 'filename' group!")
            if not re.search(ur'\?P<seqnum>', pat):
                if DEBUG:
                    print "Warning: pattern doesn't include a 'seqnum' group!"
                raise ValueError("E: pattern doesn't include a 'seqnum' group!")
            return '%s' % pat
        # reset splitpat to default if arg is None
        if pattern is None:
            self.splitpat = self.SPLITPAT
            return
        elif isinstance(pattern, (str, unicode)):
            if not template:
                raise ValueError("E: template must not be None when supplying pattern as unicode string")
            verifytemplate(pattern, template)
            self.splitpat = sanitizepattern(pattern)
        elif isinstance(pattern, dict):
            tmp = {}
            for k, v in pattern.iteritems():
                tmp[k] = sanitizepattern(v)
            self.splitpat = tmp
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
        
        C{self.splitpat} can be of type list or of type unicode raw string.
        The list form should contain unicode raw string patterns in reverse 
        order of likely occurrence. The direct unicode raw string pattern 
        form is there to facilitate to ability for the command line user 
        to supply a pattern in a command line argument. 
        
        Internally the list form is the default and will see each pattern 
        used to perform a match so that more file sequence naming cases 
        can be covered – especially when multiple differently named file 
        sequences co-exist in the same directory.
        
        @param filename: unicode string representing the file name
        @type filename: C{unicode}
        @return: dictionary with three entries: a file name (C{filename}), 
                 a sequence number (C{seqnum}) and an order (C{order}), 
                 where reverse order is seqnum then filename and normal 
                 order is filename then seqnum. 
        @note: May return C{None} if no match could be made so that an 
               enclosing loop can know when to continue.
        @rtype: C{dict} or C{None}
        @raise TypeError: if C{self.splitpat} is not of type C{unicode} or C{list}.
        @raise ValueError: When C{self.splitpat} is of type C{unicode} 
                           and an order can not be inferred by parsing 
                           the pattern and looking for what the ordering 
                           is between both named groups.
        '''
        
        _filename, _fileext = os.path.splitext(filename)
        #print "_filename = %s, _fileext = %s" % (_filename, _fileext)

        if len(_filename) == 0:
            _filename = _fileext
            _fileext = ""
        if not re.search(ur'\d+', _filename):
            # Take care of cases where numbers are found only in the fileext
            if not re.search(ur'\d+', _fileext):
                return
            else:
                _filename = "%s%s" % (_filename, _fileext)
                _fileext = ""
        
        filename = _filename
        fileext = _fileext
        
        #print "filename = %s, fileext = %s" % (filename, fileext)
        
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
                raise ValueError("E: order for split pattern is undefined!")
            if self.strictmatching:
                match = re.match(self.splitpat, filename)
            else:
                match = re.match(self.splitpat, filename)
            if match:
                if len(match.group('filename')) == 0:
                    if DEBUG: 
                        print "%s: filename group is empty. Continuing..." % filename
                elif len(match.group('seqnum')) == 0:
                    if DEBUG: 
                        print "%s: seqnum group is empty. Continuing..." % filename
                else:
                    result = {
                        'filename': match.group('filename'), 
                        'seqnum': match.group('seqnum'), 
                        'fileext': fileext, 
                        'order': order
                    }
                    if 'filename2' in match.groupdict():
                        result['filename2'] = match.group('filename2')
                    return result
            return None
        elif isinstance(self.splitpat, list):
            i = 1
            splen = len(self.splitpat)
            for d in self.splitpat:
                _pattern = d['pattern']
                _order = d['order']
                if DEBUG: 
                    print "Trying %s pattern %d of %d" % (_order, i, splen)
                if self.strictmatching:
                    match = re.match(_pattern, filename)
                else:
                    match = re.match(_pattern, filename)
                if match:
                    result = {
                        'filename': match.group('filename'), 
                        'seqnum': match.group('seqnum'), 
                        'fileext': fileext,
                        'order': _order
                    }
                    if match.groupdict().has_key('filename2'):
                        result['filename2'] = match.group('filename2')
                    if match.groupdict().has_key('filename3'):
                        print "groupdict().has_key('filename3')"
                    if DEBUG: 
                        print "Using pattern no. %d" % i
                    return result
                i += 1
            return None
        else:
            raise TypeError("split pattern is not of type unicode or list.")
    def preparedircontents(self, inpath, verbose=0):
        '''
        Prepare C{self.dircontents} to contain directory contents in 
        lists, sorted naturally-like: first by sequence number then
        alphabetically by file name.
        
        Given a filepath get the directory contents, split each file 
        into filename part(s) and a sequence number using C{self.splitpat}
        (either as pattern list or pattern itsel) and put each directory 
        and it's contents as a sorted list into C{self.dircontents}, 
        keyed by the directory's file path.
        
        @param inpath: a unicode file path string
        @type inpath: C{unicode}
        @param verbose: print informational messages to C{stdout}, like
                        when a file name is excluded because its file 
                        path matched the exclude pattern.
        @type verbose: C{int}
        @raise ValueError: if the C{inpath} doesn't exist or 
                           if C{inpath} is not a directory.
        '''
        # Paths could contain chars > 128 so try to use system's
        # default encoding if it is not ASCII. Otherwise use UTF-8.
        defaultencoding = sys.getdefaultencoding()
        if not isinstance(inpath, unicode):
            if defaultencoding == 'ascii':
                inpath = inpath.decode('utf-8')
            else:
                inpath = unicode(inpath, defaultencoding)
        if not os.path.exists(inpath):
            raise ValueError("E: path (%s) doesn't exist!" % inpath)
        if os.path.isdir(inpath):
            for root, _dirs, files in os.walk(inpath):
                sortedfiles = []
                for f in files:
                    thefile = f
                    filepath = os.path.join(root, thefile)
                    if not os.path.exists(filepath):
                        raise ValueError("E: path (%s) doesn't exist!" % filepath)
                    if thefile in self.fileexcludes:
                        continue
                    if self.excludepat and re.search(self.excludepat, filepath):
                        if verbose > 0: print "Excluding %s" % filepath
                        continue
                    if self.includepat and not re.search(self.includepat, filepath):
                        if verbose > 0: print "Not including %s" % filepath
                        continue
                    nameparts = self.splitfilename(thefile)
                    if nameparts:
                        sortedfiles.append(nameparts)
                        if DEBUG:
                            print "Matched groups = %s" % nameparts
                    else:
                        if DEBUG:
                            print("Result for splitting '%s' with given regex pattern(s) is None. Continuing..." % 
                                  thefile)
                        self.reset()
                        continue
                def seqnum_compare(x, y):
                    ''' Compare int value of two sequence numbers. '''
                    return int(x, 10) - int(y, 10)
                def filename_compare(x, y):
                    ''' Compare two file names alphabetically. '''
                    return cmp(x, y)
                sortedfiles = sorted(sortedfiles, key=itemgetter('seqnum'), cmp=seqnum_compare) # sort by seqnum
                sortedfiles = sorted(sortedfiles, key=itemgetter('filename'), cmp=filename_compare) # sort by filename
                self.dircontents[root] = sortedfiles
                if not self.recursive:
                    return
        else:
            raise ValueError("E: inpath (%s) is not a directory!" % inpath)
    def comparefile(self, dir, curfilenameparts, nextfilenameparts, verbose=0): # IGNORE:W0622
        '''
        Compare one file with the next file in the sequence.
        
        This method is called during processing of the loop which 
        iterates over all file sequences.
        
        Compares C{self.lastfilebarename} and C{self.nextseqnum} to the 
        current C{filebarename} and C{iseqnum} (int converted from seqnum) 
        and if C{self.nextseqnum} is smaller than C{iseqnum + 1}, calulcates 
        the range of the missing files and appends it as C{list} of C{unicode}
        to the C{self.missing} dictionary.
        
        @param dir: the path to the currently processed directory.
        @type dir: C{unicode}
        @param curfilenameparts: file name, sequence number, file 
                                 extension and order of the I{current}
                                 file.
        @type curfilenameparts: C{dict}
        @param nextfilenameparts: file name, sequence number, file 
                                  extension and order of the I{next}
                                  file.
        @type nextfilenameparts: C{dict}
        @param verbose: include verbose output.
        @type verbose: C{int}
        @note: I{current} and I{next} are not neccessarily referring
               to files from the same file sequence they may also be
               from different file sequences, signaling the current
               file will be the last of its sequence.
        @return: 
            False if enclosing caller loop should break.
            True if enclosing caller loop should continue.
        @rtype: C{bool}
        '''
        if curfilenameparts is None:
            if DEBUG or TESTRUN: 
                print "Warning: curfilenameparts is None"
            return True        
        if nextfilenameparts is None:
            if DEBUG or TESTRUN: 
                print "Warning: nextfilenameparts is None"
            return True
        filebarename = curfilenameparts['filename']
        if 'filename2' in curfilenameparts:
            filename2 = curfilenameparts['filename2']
        else:
            filename2 = ''
        seqnum = curfilenameparts['seqnum']
        fileext = curfilenameparts['fileext']
        order = curfilenameparts['order']
        nextfilebarename = nextfilenameparts['filename']
        _nextseqnum = nextfilenameparts['seqnum']
        _nextfileext = nextfilenameparts['fileext']
        _nextorder = nextfilenameparts['order']
        try:
            # Try converting all the numerical strings that we absolutely need as numbers
            iseqnum = int(seqnum, 10)
            if isinstance(self.start, int):
                start = self.start
            else:
                start = 0
            if isinstance(self.end, int):
                end = self.end
            else:
                end = 0
        except TypeError, e:
            if DEBUG or verbose > 0: 
                print e
            self.reset()
            return True
        except ValueError, e:
            raise e
        if start and iseqnum < start:
            if DEBUG or verbose > 0: 
                print "sequence number (%i) < start (%i). Continuing..." % (iseqnum, start)
            return True      
        if order == 'reverse':
            filename = "%s%s%s" % (filename2, seqnum, filebarename)
        else:
            filename = "%s%s%s" % (filebarename, seqnum, filename2) 
        fullfilename = "%s%s" % (filename, fileext) # (filebarename, seqnum, fileext)
        filepath = os.path.join(dir, fullfilename) 
        if verbose > 0:
            print "Processing '%s'" % filepath
        if self.seqnumwidth < 0:
            self.seqnumwidth = len(seqnum)
        if DEBUG:
            print "filename = %s" % filename
            print "filename2 = %s" % filename2
            print "filebarename = %s" % filebarename
            print "seqnum = %s" % seqnum
            print "iseqnum = %i" % iseqnum
            print "order = %s" % order
            print "nextfilenameparts = %s" % nextfilenameparts                 
        if self.lastfilebarename == '':
            # lastfilebarename is empty, which means we are at the beginning 
            # of a new file sequence. Increment iseqnum into nextseqnum and 
            # continue interating.
            self.lastfilebarename = filebarename
            self.nextseqnum = iseqnum + 1
            if end and self.nextseqnum > end:
                if DEBUG or verbose > 0: 
                    print("next sequence number (%i) would be > end (%i). Stopping iteration..." % 
                          (self.nextseqnum, end))
                self.reset()
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
                    if end and i > end:
                        # When nextseqnum is greater than end we still need
                        # to produce a missing file list up to end. That's why
                        # we break inside the loop so that we can reset down
                        # below when returning True to the enclosing iteration
                        # loop that will then start processing the next file
                        # sequence (if there is one).
                        break
                    if order == 'reverse':
                        partsdict = dict(
                            filename2=filename2,
                            seqnum="%0.*d" % (self.seqnumwidth, i), 
                            filebarename=filebarename, 
                            fileext=fileext
                        )
                        missingfilename = "%(filename2)s%(seqnum)s%(filebarename)s%(fileext)s" % partsdict
                    else:
                        partsdict = dict(
                            filename2=filename2,
                            seqnum="%0.*d" % (self.seqnumwidth, i), 
                            filebarename=filebarename, 
                            fileext=fileext
                        )
                        missingfilename = "%(filebarename)s%(seqnum)s%(filename2)s%(fileext)s" % partsdict
                    if DEBUG or verbose > 0: 
                        print "Missing %s" % missingfilename
                    if dir in self.missing:
                        self.missing[dir].append(missingfilename)
                    else:
                        self.missing[dir] = []
                        self.missing[dir].append(missingfilename)
                if end and iseqnum > end:
                    if DEBUG or verbose > 0: 
                        print("sequence number (%i) in next existing file name > end (%i). Stopping iteration..." % 
                              (iseqnum, end))
                    # If self.end is reached for a file sequence reset state and return True 
                    # so that we may continue afresh with the next file sequence from the directory.
                    self.reset()
                    return True
                # Since we just handled a missing range, adjust the nextseqnum 
                # to start after the end of the missing range
                self.nextseqnum = iseqnum + 1
            else:
                # No missing sequence found. 
                # Continue iterating over the current file sequence 
                # based on file bare name.
                self.nextseqnum += 1
            if nextfilebarename != filebarename:
                # Next file(bare)name is not the same as the current,
                # indicating that a new file sequence is beginning.
                self.reset()
            return True
        else:
            self.reset()
        return True
    def processdir(self, inpath, strict=False, verbose=0):
        ''' Main entry method: process the contents of a directory.
        
        @param inpath: the file path to a directory to process.
        @type inpath: C{unicode}
        @param strict: use re.match instead of re.search for splitting the file name
        @type strict: C{bool}
        @param verbose: print informational messages.
        @type verbose: C{int}
        @return: dictionary with missing files. Contains as keys,
                 paths to directories with missing files. 
                 Each path key contains as its value a list of 
                 missing unicode file names. If there are no
                 missing files, returns an empty dictionary.
        @rtype: C{dict}
        @raise ValueError: if the directory at C{inpath} doesn't 
                           exist.
        '''
        self.lastexectime = -1
        start = float(time.time())
        if not strict:
            self.strictmatching = False
        self.preparedircontents(inpath, verbose)
        if len(self.dircontents) > 0:
            for adir, files in self.dircontents.items():
                if self.fullpaths:
                    bdir = os.path.join(os.path.abspath(os.curdir), adir)
                else:
                    bdir = adir
                if not os.path.exists(adir):
                    # check again to be sure the path did not turn invalid since the last time we checked
                    raise ValueError("E: directory (%s) doesn't exist!" % bdir)
                def pairs(lst):
                    ''' Iterate through a list in pairs. '''
                    i = iter(lst)
                    first = prev = i.next()
                    item = None
                    for item in i:
                        yield prev, item
                        prev = item
                    if item:
                        yield item, first
                for curfile, nextfile in pairs(files):
                    result = self.comparefile(bdir, curfile, nextfile, verbose)
                    if result == False:
                        break
                    elif result == True:
                        continue
                    else:
                        break
        else:
            if DEBUG or verbose > 0: 
                print "Nothing missing."
        elapsed = float(time.time() - start)
        self.lastexectime = elapsed
        return self.missing


def main(argv=None):  # IGNORE:C0111
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)
        
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = '''checkfileseq -- scan directories for file sequences with missing files.'''
    program_license = u'''%s

    Created by André Berg on %s.
    Copyright 2010 Berg Media. All rights reserved.
    
    Licensed under the Apache License 2.0
    http://www.apache.org/licenses/LICENSE-2.0
    
    Distributed on an "AS IS" basis without warranties
    or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup option parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-p", "--pattern", dest="splitpat", help="regex pattern used for splitting a filename into a name part and a sequence number part. Must contain two named groups: 'filename' and 'seqnum'. Can optionally contain a 'filename2' group for cases where the filename is split in half by the sequence number. Note: You should only need to override the defaults for special cases.", metavar="RE")
        parser.add_argument("-m", "--template", dest="template", help="format string with dict-based replacement tokens (e.g. '%%s(<key_name>)s') that correspond to the named groups given in the custom splitpat. Important: this argument is mandatatory if a custom split pattern is specified.", metavar="STR")
        parser.add_argument("-r", "--recursive", dest="recurse", action="store_true", help="recurse into subfolders [default: %(default)s]")
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument("-f", "--from", dest="rangestart", help="only process files with sequence number greater than NUM  [default: %(default)s]", metavar="NUM")
        parser.add_argument("-t", "--to", dest="rangeend", help="only process files with sequence number less than or equal to NUM [default: %(default)s]", metavar="NUM")
        parser.add_argument("-i", "--include", dest="include", help="only include paths matching this regex pattern. Note: exclude is given preference over include. [default: %(default)s]", metavar="RE" )
        parser.add_argument("-e", "--exclude", dest="exclude", help="exclude paths matching this regex pattern. [default: %(default)s]", metavar="RE" )
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-s', '--strict', dest="strict", help="use re.match instead of re.search to match and split filenames exactly [default: %(default)s]", action="store_true")
        parser.add_argument(dest="paths", help="paths to folder(s) with file sequence(s) [default: %(default)s]", metavar="path", nargs='+')
        
        parser.set_defaults(verbose=0, strict=False)
        
        # Process options
        args = parser.parse_args()
        paths = args.paths
        verbose = args.verbose
        rangestart = args.rangestart
        rangeend = args.rangeend
        splitpat = args.splitpat
        template = args.template
        recurse = args.recurse
        inpat = args.include
        expat = args.exclude
        strict = args.strict
        argv0 = sys.argv[0].split(u"/")[-1]
        defaultencoding = sys.getdefaultencoding()
        
        if verbose > 0:
            print "Verbose mode on"
            if recurse:
                print "Recursive mode on"
            else:
                print "Recursive mode off"
            if strict:
                print "Using strict mode"
        
        if inpat and expat and inpat == expat:
            raise CLIError("include and exclude pattern are equal! Nothing will be processed.")
        
        if splitpat and not template:
            raise CLIError("custom split pattern specified but no custom template:\n"\
                            "%sdid you forget -m <string>|--template=<string>?" % ((len(argv0)+5) * " "))
        elif template and not splitpat:
            raise CLIError("custom template specified but no custom split pattern:\n"\
                            "%sdid you forget -p <regex>|--pattern=<regex>?" % ((len(argv0)+5) * " "))
        
        missing = {}

        for inpath in paths:
            if verbose > 0:
                fsc = FileSequenceChecker(rangestart, rangeend, recurse, True)
            else:
                fsc = FileSequenceChecker(rangestart, rangeend, recurse)
            if defaultencoding == 'ascii':
                if splitpat and template:
                    fsc.setsplitpattern(unicode(splitpat, 'utf-8'), 
                                        unicode(template, 'utf-8'))
                if inpat:
                    fsc.setincludepattern(unicode(inpat, 'utf-8'))
                if expat:
                    fsc.setexcludepattern(unicode(expat, 'utf-8'))
            else:
                if splitpat and template:
                    fsc.setsplitpattern(unicode(splitpat, defaultencoding), 
                                        unicode(template, defaultencoding))
                if inpat:
                    fsc.setincludepattern(unicode(inpat, defaultencoding))
                if expat:
                    fsc.setexcludepattern(unicode(expat, defaultencoding))
            missing = fsc.processdir(inpath, strict, verbose)
        raise KeyboardInterrupt
    except KeyboardInterrupt:
        exectime = fsc.lastexectime
        if exectime > 0:
            if len(missing) > 0:
                for containingdir, missingfiles in missing.items():
                    print "In %s:" % containingdir
                    for missingfile in missingfiles:
                        print "  Missing %s" % missingfile
                if fsc.totalfiles == 1:
                    tfplural = ""
                else:
                    tfplural = "s"
                if fsc.totaldirs == 1:
                    tdplural = ""
                else:
                    tdplural = "s"
                print "\n-------------"
                print "Total missing: %i file%s in %i dir%s" % (fsc.totalfiles, tfplural, fsc.totaldirs, tdplural)
            elif verbose > 0:
                print "\n---------------"
                print "Nothing missing"
            else:
                print "Nothing missing"
            if fsc.totalprocessed == 1:
                plurality = ""
            else:
                plurality = "s"
            print ""
            print "Processed %i file%s in %0.4f s" % (fsc.totalprocessed, plurality, exectime)
        return 0
    except Exception, e:
        if DEBUG or False:
            raise(e)
        print >> sys.stderr, sys.argv[0].split(u"/")[-1] + u": " + unicode(e)
        print >> sys.stderr, "\t for help use --help"
        return 2

if __name__ == "__main__":
    datadir = "unittests/data"    
    if DEBUG:
        sys.argv.append("-v")
        sys.argv.append("-r")
        sys.argv.append(datadir)
    if TESTRUN:
        import doctest
        doctest.testmod()
        reload(sys)
        sys.setdefaultencoding('ascii') # IGNORE:E1101 #@UndefinedVariable
        #sys.argv.append("-h")
        #sys.argv.append("-v")
        #sys.argv.append("-V")
        #sys.argv.append("--from=0")
        #sys.argv.append("--to=10")
        #sys.argv.append("-s")
        sys.argv.append("-r")
        #sys.argv.append("--pattern='^(?!\d)(?P<filename>.+?)(?P<seqnum>\d+)$'")
        #sys.argv.append("--template='%(seqnum)s%(filename)s'")
        #sys.argv.append("unittests/data/reverse_order")
        sys.argv.append(datadir)
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'checkfileseq_profile.out'
        cProfile.run('main(["-r", datadir])', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        print >> statsfile, stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
    