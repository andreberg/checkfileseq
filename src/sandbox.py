#!/usr/local/bin/python2.7
# encoding: utf-8
'''
Created on 28.10.2010

@author: andre
'''

#import os
#import re
#from operator import itemgetter
#import locale

DOCTEST = 1

#inpath = u"/Users/andre/test/sort"
#splitpat = ur'(?P<filename>.+?)(?P<seqnum>\d*)$'
#dircontents = {}
#
#def sort_nicely(l): 
#    """ Sort the given list in the way that humans expect. """ 
#    convert = lambda text: int(text) if text.isdigit() else text 
#    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
#    l.sort(key=alphanum_key)
#
#if os.path.isdir(inpath):
#    for root, _dirs, files in os.walk(inpath):
#        sortedfiles = []
#        for f in files:
#            curpath = os.path.join(root, f)
#            filename, fileext = os.path.splitext(f)
#            match = re.match(splitpat, filename)
#            if match:
#                filebarename = match.group('filename')
#                seqnum = match.group('seqnum')
#                #print filebarename, seqnum
#                parts = (filebarename, seqnum, fileext)
#                #partsdict = {'filebarename':filebarename, 'seqnum':seqnum, 'fileext': fileext}
#                sortedfiles.append(parts)
#        def seqnum_compare(x, y): #IGNORE:C0111
#            return int(x, 10) - int(y, 10)
#        def filename_compare(x, y): #IGNORE:C0111
#            return cmp(locale.strxfrm(x), locale.strxfrm(y))
#        sortedfiles = sorted(sortedfiles, key=itemgetter(1), cmp=seqnum_compare) # sort by seqnum
#        sortedfiles = sorted(sortedfiles, key=itemgetter(0), cmp=filename_compare) # sort by filename
#        dircontents[root] = sortedfiles
#
#order = [1, 0, 2]
#
#for k, v in dircontents.iteritems():
#    print k
#    for s in v:
#        print u"%s%s%s" % (s[order[0]], s[order[1]], s[order[2]]) 


def longestCommonSubstring(s1, s2):
    ''' Compare two strings and return the longest substring that both have in common. 
    
    Tries to find each length variant of the shorter string contained by the
    longer string. Here, "length variant" means that given the shorter string, 
    construct a substring whose length is one character less from the beginning 
    of the last variant. E.g.: given "string", try to find "string", "tring",
    "ring" ... "g" inside the longer string. Each match that is several characters
    equal to a substring of the longer string is appended to the match list.
    The result is then given by finding the longest string from the match list.
    
    Efficiency is not the best, with somewhat quadratic behaviour: O(∑(len(s1))*len(s2)).
    For the needle string we have O(x^2) and for the haystack string we have O(x).
    If both are doubled in length permutation growth increases eigth-fold. 
    For a more efficient solution to this problem look at the suffix tree algorithm
    (Ukkonen et al.) which extends on the the same idea that builds the foundation 
    for this implementation.
    
    Example:
    
        >>> print longestCommonSubstring(u"pippi", u"missisippi")
        ippi
    
    @param s1: a string, usually the needle
    @type s1: C{string}
    @param s2: another string, usually the haystack
    @type s2: C{string}
    @return: The longest commong substring or None
             if no substring is found to be common 
             among both strings.
    @rtype: C{string} or C{none}
    '''
    result = u""
    s1len = len(s1)
    s2len = len(s2)
    matches = []
    #print "s1 = '%s' (len = %d)" % (s1, s1len)
    #print "s2 = '%s' (len = %d)" % (s2, s2len)
    x = 0 # short string counter
    y = 0 # long string counter
    i = 0 # length variant counter
    if s1len == 0 or s2len == 0:
        return u""
    if s1len > s2len:
        longstr = s1
        shortstr = s2
    else:
        longstr = s2
        shortstr = s1
    while True:
        curstr = shortstr[i:]
        curlen = len(curstr)
        if i >= curlen:
            break
        while True:
            if x >= curlen:
                break
            elif y >= len(longstr):
                break
            curchar = curstr[x]
            if curchar != longstr[y]:
                y += 1
                continue
            else:
                result += curchar
                x += 1
                continue
        matches.append(result)
        i += 1
        # Reset before trying 
        # the next length variant
        result = u""
        x = 0
        y = 0
    longest = u""
    for match in matches:
        if len(match) > len(longest):
            longest = match
    return longest

print longestCommonSubstring(u"André Berg", u"Mein Gott, André Berg ist ...")
print longestCommonSubstring(u"Mein Gott, André Berg ist ...", u"André Berg")
print longestCommonSubstring(u"résumé.v01.01.png", u"résumé.v01.02.png")
print "'%s'" % longestCommonSubstring(u"", u"")
print longestCommonSubstring(u"pippi", u"missisippi")
print longestCommonSubstring(u"pippi", u"missipippissippi")
print longestCommonSubstring(u"pippi", u"missiippissippi")
print longestCommonSubstring(u"André Berg", u"Hey, have you seen André berg lately?")

if DOCTEST:
    import doctest
    doctest.testmod()

