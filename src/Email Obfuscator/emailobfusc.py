#!/usr/bin/env python
# encoding: utf-8

"""
Email Obfuscator 01.py

Created by Andre Berg on 2010-10-04.
Copyright (c) 2010 Berg Media. All rights reserved.
"""

import sys
import os
import re
from optparse import OptionParser

program_name = os.path.basename(sys.argv[0])
program_shortdesc = u"ordinal string obfuscation, useful for (de)scrambling email addresses"
program_version = u"v0.1"
program_build_date = u"2010-10-04"

license = u'''Copyright 2010 André Berg (Berg Media)                                                
Licensed under the MIT License, http://www.opensource.org/licenses/mit-license.php'''

version_message = u'%%prog %s (%s)' % (program_version, program_build_date)
usage_message = u'''
    %s: [-h|--help] [--version] [-v <num>|--verbose=<num>]  => help, version, verbosity -OR-
    %s: [-s<str>|--suffix=<str>] [-p<str>|--prefix=<str>] <str1 ... strN> -OR-
    %s: -r|--reverse [-s<str>|--suffix=<str>] [-p<str>|--prefix=<str>] <str1 ... strN>
''' % (program_name, program_name, program_name)

def printInfo(option, optstr, value, parser):
    lic = re.split(ur'[\s\t]*\n', license)
    lic = "\n    ".join(lic)
    help_message = u'''
    %s - %s
    
    %s
    
    Replaces each char with its ordinal, and wraps it as numerical xml entity '&#<nnn>;' (by default).
    A different wrapping scheme can be used by supplying custom prefix and suffix strings.
    The process can also be reversed by specifying the reverse flag.
    
    See also: %s --help
    
    ''' % (program_name, program_shortdesc, lic, program_name)
    print help_message
    sys.exit(0)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) == 1:
        print u"%s - %s\n\nsee %s --help." % (program_name, program_shortdesc, program_name)
        return 1
    try:
        # setup option parser
        parser = OptionParser(version=version_message, usage=usage_message, description=license)
        parser.add_option("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %default]", metavar="FILE")
        parser.add_option("-p", "--prefix", dest="prefix", help="specify prefix string [default: %default]", metavar="STR")
        parser.add_option("-s", "--suffix", dest="suffix", help="specify suffix string [default: %default]", metavar="STR")
        parser.add_option("-i", "--info", action="callback", callback=printInfo, help="short program description")
        parser.add_option("-r", "--reverse", dest="reverse", action="store_true", help="perform reverse operation")
        
        parser.set_defaults(prefix="&#", suffix=";", reverse=False)
        
        # process options
        (opts, args) = parser.parse_args(argv[1:])
        
        if opts.verbose > 0:
            print "verbose on\n"
        
        if opts.reverse:
            for arg in args:
                result = u""
                if opts.verbose > 0:
                    print u"de-obfuscating '%s'" % arg
                chars = re.split(ur'[%s%s]' % (opts.prefix, opts.suffix), arg)
                for char in chars:
                    if not (char == u'' or char == ''):
                        result = u"%s%s" % (result, unichr(int(char)))
                result = u"%s\n" % result
                if opts.verbose > 0:
                    print u"result = %s" % result
                else:
                    print result,
        else:
            for arg in args:
                result = u""
                if opts.verbose > 0:
                    print u"obfuscating '%s'" % arg
                for char in arg:
                    result = u"%s%s%s%s" % (result, opts.prefix, ord(char), opts.suffix)
                result = u"%s\n" % result
                if opts.verbose > 0:
                    print u"result = %s" % result
                else:
                    print result,
    except Exception, e:
        print >> sys.stderr, sys.argv[0].split(u"/")[-1] + u": " + unicode(e).decode('unicode_escape')
        print >> sys.stderr, "\t for help use --help"
        return 2


if __name__ == "__main__":
    #sys.exit(main([sys.argv[0], u"email@web.de", u"andre.berg@email.de"]))
    #sys.exit(main([sys.argv[0], u"-vv", u"email@web.de", u"andre.berg@email.de"]))
    #sys.exit(main([sys.argv[0], u"-h"]))
    #sys.exit(main([sys.argv[0], u"-i"]))
    #sys.exit(main([sys.argv[0], u"-r", u"-v", u'&#101;&#109;&#97;&#105;&#108;&#64;&#119;&#101;&#98;&#46;&#100;&#101;']))
    #sys.exit(main([sys.argv[0], u"-r", u'&#101;&#109;&#97;&#105;&#108;&#64;&#119;&#101;&#98;&#46;&#100;&#101;']))
    #sys.exit(main([sys.argv[0], u"-r", u"--prefix=!", u"--suffix=+", u'!101+!255+']))
    #sys.exit(main([sys.argv[0], u"--prefix=&#", u"--suffix=;", "blah@microsoft.com"]))
    #sys.exit(main([sys.argv[0], u'--reverse', u'&#97;&#110;&#100;&#114;&#101;&#64;&#119;&#101;&#98;&#46;&#100;&#101;']))
    sys.exit(main())
