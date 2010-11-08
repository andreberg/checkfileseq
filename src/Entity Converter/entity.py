#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#
# 
#  entity
#
#  A simple class for converting HTML/XML entities
#  to Unicode and vice versa. The solutions I did 
#  find where not particularly flexible or versatily 
#  enough for the needs of a project I was working on.
# 
#  There are a lot of JavaSript 'encodeURIcomponent()'-like 
#  codecs and quite a few entity decoders but encoding as 
#  well is really hard to come by especially anything 
#  that goes beyond the simple XML special chars range 
#  of "<">&'".
#
#  This class aims to add support for decoding/encoding either
#  full HTML entity mnemonics (aka friendly names) or the
#  complete range of XML entity charref codes, either decimal
#  or hexadecimal.
#
#  The way this works is currently as a command line tool
#  taking a direct param indicating coding direction and
#  a mode ("html" or "xml") as paramaters with input from STDIN.
#
#  Pre-computed lookup tables are provided instead of
#  computing everything from 'htmlentitydefs'. 
#  This of course means if said module is updated one
#  would need to update the lookup tables as well.
#  Though I highly doubt that this will be the case
#  anytime soon...
#
#  In the lookup tables, which, btw can also be output to 
#  dictionary syntax valid for "Python","Ruby" or "AppleScript",
#  troublesome characters such as line ending characters or the
#  non-breaking space, have been replaced with a unichar(code)
#  to always yield the correct result needed for a clean re.sub
#  action in replacing them with their counterparts.
#
#  LICENSE
#
#  Created by Andre Berg on 2009-03-25.
#  Copyright 2009 Berg Media. All rights reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");                   
#  you may not use this file except in compliance with the License.                  
#  You may obtain a copy of the License at                                           
#                                                                                    
#     http://www.apache.org/licenses/LICENSE-2.0                                     
#                                                                                    
#  Unless required by applicable law or agreed to in writing, software               
#  distributed under the License is distributed on an "AS IS" BASIS,                 
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.          
#  See the License for the specific language governing permissions and               
#  limitations under the License.
#
#

import re
import htmlentitydefs
import unittest
from optparse import OptionParser


class Entity(object):
    """
    A simple class for converting HTML/XML entities
    to Unicode and vice versa
    """
    
    unichar2entitycode = {
        u'‌':"&#8204;", 
        u'å':"&#xe5;", u'>':"&#62;", u'¥':"&#xa5;", u'ò':"&#xf2;", 
        u'Χ':"&#935;", u'δ':"&#948;", u'〉':"&#9002;", u'™':"&#8482;", 
        u'Ñ':"&#xd1;", u'ϒ':"&#978;", u'Ý':"&#xdd;", u'Ã':"&#xc3;", 
        u'√':"&#8730;", u'⊗':"&#8855;", u'æ':"&#xe6;", u'œ':"&#339;", 
        u'≡':"&#8801;", u'∋':"&#8715;", u'Ψ':"&#936;", u'ä':"&#xe4;", 
        u'∪':"&#8746;", u'Â':"&#xc2;", u'Ε':"&#917;", u'−':"&#8722;", 
        u'õ':"&#xf5;", u'<':"&#60", u'Î':"&#xce;", u'É':"&#xc9;", u'Ó':"&#xd3;", 
        u'‚':"&#8218;", u'″':"&#8243;", u'ø':"&#xf8;", u'ψ':"&#968;", 
        u'Κ':"&#922;", u'›':"&#8250;", u'´':"&#xb4;", u'ú':"&#xfa;", 
        u'ς':"&#962;", unichr(8206):"&#8206;", u'‍':"&#8205;", u'¸':"&#xb8;", 
        u'Ξ':"&#926;", u'¨':"&#xa8;", u'¬':"&#xac;", u'κ':"&#954;", 
        u'Æ':"&#xc6;", u'′':"&#8242;", u'Τ':"&#932;", u'⌈':"&#8968;", 
        u'¿':"&#xbf;", u'ℵ':"&#8501;", u'«':"&#xab;", u'⇓':"&#8659;", 
        u'”':"&#8221;", u'≥':"&#8805;", u'Ì':"&#xcc;", u'®':"&#xae;", 
        u'µ':"&#xb5;", unichr(173):"&#xad;", u'⋅':"&#8901;", unichr(160):"&#xa0;", 
        u'⌊':"&#8970;", u'⇐':"&#8656;", u'Ä':"&#xc4;", u'¦':"&#xa6;", 
        u'Õ':"&#xd5;", u'ß':"&#xdf;", u'♣':"&#9827;", u'à':"&#xe0;", 
        u'Ô':"&#xd4;", u'Θ':"&#920;", u'Π':"&#928;", u'Œ':"&#338;", 
        u'Š':"&#352;", u'ϑ':"&#977;", u'è':"&#xe8;", u'⊂':"&#8834;", 
        u'¡':"&#xa1;", u'½':"&#xbd;", u'ª':"&#xaa;", u'∑':"&#8721;", 
        u'¼':"&#xbc;", u'∝':"&#8733;", u'Ü':"&#xdc;", u'ñ':"&#xf1;", 
        u'⊃':"&#8835;", u'≈':"&#8776;", u'θ':"&#952;", u'∏':"&#8719;", 
        u'⊄':"&#8836;", u'⇔':"&#8660;", u'⇒':"&#8658;", u'Ø':"&#xd8;", 
        u'ν':"&#957;", u'Þ':"&#xde;", u'ÿ':"&#xff;", u'∞':"&#8734;", 
        u'Μ':"&#924;", u'≤':"&#8804;", u' ':"&#8201;", u'ê':"&#xea;", 
        u'„':"&#8222;", u'Σ':"&#931;", u'ƒ':"&#402;", u'Å':"&#xc5;", 
        u'˜':"&#732;", u'¾':"&#xbe;", u'∇':"&#8711;", u'—':"&#8212;", 
        u'↑':"&#8593;", u'‰':"&#8240;", u'Ù':"&#xd9;", u'η':"&#951;", 
        u'À':"&#xc0;", u'¹':"&#xb9;", u'∀':"&#8704;", u'ˆ':"&#710;", 
        u'ð':"&#xf0;", u'⌉':"&#8969;", u'ï':"&#xef;", u'γ':"&#947;", 
        u'λ':"&#955;", u'↔':"&#8596;", u'È':"&#xc8;", u'ξ':"&#958;", 
        u'ℜ':"&#8476;", u'÷':"&#xf7;", u'Ö':"&#xd6;", u'ℑ':"&#8465;", 
        u'…':"&#8230;", u'ì':"&#xec;", u'Ÿ':"&#376;", u'∠':"&#8736;", 
        u'⊆':"&#8838;", u'◊':"&#9674;", u'⁄':"&#8260;", u'Ð':"&#xd0;", 
        u'∗':"&#8727;", u'Ν':"&#925;", u'±':"&#xb1;", u'ω':"&#969;", 
        u'χ':"&#967;", u'²':"&#xb2;", u'³':"&#xb3;", u'Á':"&#xc1;", 
        u'¢':"&#xa2;", u'Í':"&#xcd;", u'‾':"&#8254;", u'Ê':"&#xca;", 
        u'Β':"&#914;", u'⊥':"&#8869;", u' ':"&#8195;", u'∴':"&#8756;", 
        u'π':"&#960;", u'ι':"&#953;", u'∅':"&#8709;", u'ë':"&#xeb;", 
        u'∉':"&#8713;", u'Υ':"&#933;", u'¶':"&#xb6;", u'ε':"&#949;", 
        u'Δ':"&#916;", u'℘':"&#8472;", u'ü':"&#xfc;", u'∂':"&#8706;", 
        u'î':"&#xee;", u'•':"&#8226;", u'ο':"&#959;", u'υ':"&#965;", 
        u'©':"&#xa9;", u'Ï':"&#xcf;", u'Λ':"&#923;", u'♠':"&#9824;", 
        u'–':"&#8211;", u' ':"&#8194;", u'ç':"&#xe7;", u'Û':"&#xdb;", 
        u'∩':"&#8745;", u'ô':"&#xf4;", u'μ':"&#956;", u'š':"&#353;", 
        u'‘':"&#8216;", u'∈':"&#8712;", u'Ζ':"&#918;", u'⊇':"&#8839;", 
        u'°':"&#xb0;", u'∧':"&#8743;", u'τ':"&#964;", u'£':"&#xa3;", 
        u'¤':"&#xa4;", u'∫':"&#8747;", u'û':"&#xfb;", u'⌋':"&#8971;", 
        u'↵':"&#8629;", u'ù':"&#xf9;", u'∃':"&#8707;", u'≅':"&#8773;", 
        u'‡':"&#8225;", u'⊕':"&#8853;", u'×':"&#xd7;", u'ã':"&#xe3;", 
        u'ϖ':"&#982;", u'í':"&#xed;", u'Ë':"&#xcb;", u'Φ':"&#934;", 
        u'»':"&#xbb;", u'‹':"&#8249;", u'"':"&#34;", u'Ú':"&#xda;", 
        u'Ο':"&#927;", u'≠':"&#8800;", u'Ι':"&#921;", u'é':"&#xe9;", 
        u'→':"&#8594;", u'ý':"&#xfd;", u'Ρ':"&#929;", u'↓':"&#8595;", 
        u'Α':"&#913;", u'ζ':"&#950;", u'Ω':"&#937;", u'â':"&#xe2;", 
        u'∼':"&#8764;", u'φ':"&#966;", u'♦':"&#9830;", u'¯':"&#xaf;", 
        u'←':"&#8592;", u'Ç':"&#xc7;", u'º':"&#xba;", u'⇑':"&#8657;", 
        u'β':"&#946;", u'Η':"&#919;", u'ρ':"&#961;", u'á':"&#xe1;", 
        u'α':"&#945;", unichr(8207):"&#8207;", u'·':"&#xb7;", u'Γ':"&#915;", 
        u'€':"&#8364;", u'〈':"&#9001;", u'†':"&#8224;", u'&': "&#38;",
        u'’':"&#8217;", u'þ':"&#xfe;", u'ö':"&#xf6;", u'∨':"&#8744;", 
        u'Ò':"&#xd2;", u'§':"&#xa7;", u'“':"&#8220;", u'♥':"&#9829;", 
        u'σ':"&#963;", u'ó':"&#xf3;"
    }
    
    entitycode2unichar = {
        '&#931;':u'Σ', '&#8501;':u'ℵ', '&#8756;':u'∴', 
        '&#xee;':u'î', '&#8211;':u'–', '&#xca;':u'Ê', '&#8727;':u'∗', 
        '&#xe1;':u'á', '&#8596;':u'↔', '&#916;':u'Δ', '&#913;':u'Α', 
        '&#8656;':u'⇐', '&#8220;':u'“', '&#xf0;':u'ð', '&#xbc;':u'¼', 
        '&#xb1;':u'±', '&#xa9;':u'©', '&#956;':u'μ', '&#9827;':u'♣', 
        '&#965;':u'υ', '&#8707;':u'∃', '&#920;':u'Θ', '&#xe9;':u'é', 
        '&#xf7;':u'÷', '&#xc5;':u'Å', '&#949;':u'ε', '&#xa5;':u'¥', 
        '&#xb9;':u'¹', '&#xa1;':u'¡', '&#xff;':u'ÿ', '&#8805;':u'≥', 
        '&#8476;':u'ℜ', '&#9674;':u'◊', '&#xf9;':u'ù', '&#xbd;':u'½', 
        '&#8206;':unichr(8206), '&#8243;':u'″', '&#8212;':u'—', '&#xef;':u'ï', 
        '&#8195;':u' ', '&#xdf;':u'ß', '&#8776;':u'≈', '&#8657;':u'⇑', 
        '&#929;':u'Ρ', '&#9830;':u'♦', '&#xd4;':u'Ô', '&#xf3;':u'ó', 
        '&#xd5;':u'Õ', '&#xa2;':u'¢', '&#8736;':u'∠', '&#959;':u'ο', 
        '&#xb0;':u'°', '&#966;':u'φ', '&#8704;':u'∀', '&#xcf;':u'Ï', 
        '&#919;':u'Η', '&#921;':u'Ι', '&#960;':u'π', '&#946;':u'β', 
        '&#9002;':u'〉', '&#935;':u'Χ', '&#951;':u'η', '&#xb8;':u'¸', 
        '&#8804;':u'≤', '&#978;':u'ϒ', '&#8205;':u'‍', '&#353;':u'š', 
        '&#xf8;':u'ø', '&#8744;':u'∨', '&#xe3;':u'ã', '&#8660;':u'⇔', 
        '&#xde;':u'Þ', '&#8711;':u'∇', '&#8222;':u'„', '&#xf2;':u'ò', 
        '&#xd3;':u'Ó', '&#8254;':u'‾', '&#967;':u'χ', '&#8595;':u'↓', 
        '&#xb3;':u'³', '&#xac;':u'¬', '&#958;':u'ξ', '&#9829;':u'♥', 
        '&#977;':u'ϑ', '&#8719;':u'∏', '&#922;':u'Κ', '&#xc3;':u'Ã', 
        '&#xa3;':u'£', '&#8836;':u'⊄', '&#945;':u'α', '&#8659;':u'⇓', 
        '&#950;':u'ζ', '&#xbf;':u'¿', '&#8204;':u'‌', '&#xaa;':u'ª', 
        '&#8745;':u'∩', '&#352;':u'Š', '&#xae;':u'®', '&#8225;':u'‡', 
        '&#8472;':u'℘', '&#8835;':u'⊃', '&#xc8;':u'È', '&#8734;':u'∞', 
        '&#xd2;':u'Ò', '&#8838;':u'⊆', '&#34;':u'"', '&#8743;':u'∧', 
        '&#xe4;':u'ä', '&#xdc;':u'Ü', '&#923;':u'Λ', '&#8722;':u'−', 
        '&#xcd;':u'Í', '&#xf5;':u'õ', '&#xc0;':u'À', '&#8364;':u'€', 
        '&#933;':u'Υ', '&#xfc;':u'ü', '&#8968;':u'⌈', '&#961;':u'ρ', 
        '&#xad;':unichr(173), '&#8629;':u'↵', '&#8713;':u'∉', '&#953;':u'ι', 
        '&#xba;':u'º', '&#8834;':u'⊂', '&#8465;':u'ℑ', '&#xb2;':u'²', 
        '&#60':u'<', '&#968;':u'ψ', '&#936;':u'Ψ', '&#8730;':u'√', 
        '&#xc9;':u'É', '&#8250;':u'›', '&#8201;':u' ', '&#8224;':u'†', 
        '&#376;':u'Ÿ', '&#8207;':unichr(8207), '&#xd1;':u'Ñ', '&#8593;':u'↑', 
        '&#xb5;':u'µ', '&#8260;':u'⁄', '&#8839;':u'⊇', '&#732;':u'˜', 
        '&#8855;':u'⊗', '&#8242;':u'′', '&#xce;':u'Î', '&#xfd;':u'ý', 
        '&#38;':u'&', '&#xc1;':u'Á', '&#8658;':u'⇒', '&#8970;':u'⌊', 
        '&#8733;':u'∝', '&#xf4;':u'ô', '&#xd9;':u'Ù', '&#9001;':u'〈', 
        '&#932;':u'Τ', '&#xb4;':u'´', '&#952;':u'θ', '&#8249;':u'‹', 
        '&#8218;':u'‚', '&#924;':u'Μ', '&#8230;':u'…', '&#8901;':u'⋅', 
        '&#xdd;':u'Ý', '&#969;':u'ω', '&#xd0;':u'Ð', '&#8764;':u'∼', 
        '&#xa4;':u'¤', '&#8482;':u'™', '&#8869;':u'⊥', '&#8592;':u'←', 
        '&#xcb;':u'Ë', '&#xe6;':u'æ', '&#915;':u'Γ', '&#xd8;':u'Ø', 
        '&#xab;':u'«', '&#xa6;':u'¦', '&#9824;':u'♠', '&#955;':u'λ', 
        '&#962;':u'ς', '&#8801;':u'≡', '&#402;':u'ƒ', '&#xc6;':u'Æ', 
        '&#925;':u'Ν', '&#8773;':u'≅', '&#8240;':u'‰', '&#xea;':u'ê', 
        '&#937;':u'Ω', '&#982;':u'ϖ', '&#8800;':u'≠', '&#8746;':u'∪', 
        '&#8194;':u' ', '&#xb7;':u'·', '&#xe7;':u'ç', '&#xfe;':u'þ', 
        '&#xa7;':u'§', '&#xcc;':u'Ì', '&#xf6;':u'ö', '&#xd7;':u'×', 
        '&#914;':u'Β', '&#xfb;':u'û', '&#963;':u'σ', '&#339;':u'œ', 
        '&#954;':u'κ', '&#xc2;':u'Â', '&#928;':u'Π', '&#8853;':u'⊕', 
        '&#710;':u'ˆ', '&#926;':u'Ξ', '&#8971;':u'⌋', '&#xc7;':u'Ç', 
        '&#8217;':u'’', '&#8216;':u'‘', '&#xeb;':u'ë', '&#xdb;':u'Û', 
        '&#8721;':u'∑', '&#xbb;':u'»', '&#8712;':u'∈', '&#xb6;':u'¶', 
        '&#8747;':u'∫', '&#xed;':u'í', '&#xe0;':u'à', '&#8221;':u'”', 
        '&#918;':u'Ζ', '&#xf1;':u'ñ', '&#8594;':u'→', '&#917;':u'Ε', 
        '&#62;':u'>', '&#xa8;':u'¨', '&#xd6;':u'Ö', '&#8226;':u'•', 
        '&#964;':u'τ', '&#xaf;':u'¯', '&#8706;':u'∂', '&#338;':u'Œ', 
        '&#957;':u'ν', '&#xe8;':u'è', '&#xe5;':u'å', '&#934;':u'Φ', 
        '&#927;':u'Ο', '&#947;':u'γ', '&#xc4;':u'Ä', '&#xa0;':unichr(160), 
        '&#948;':u'δ', '&#xec;':u'ì', '&#8709;':u'∅', '&#8969;':u'⌉', 
        '&#xda;':u'Ú', '&#8715;':u'∋', '&#xbe;':u'¾', '&#xe2;':u'â', 
        '&#xfa;':u'ú'
    }
    
    unichar2name = {
        u'Ë':'Euml', u'Ê':'Ecirc', u'∋':'ni', u'Í':'Iacute', 
        u'ω':'omega', u'ψ':'psi', u'χ':'chi', u'φ':'phi', u'υ':'upsilon', 
        u'τ':'tau', u'σ':'sigma', u'ς':'sigmaf', u'ρ':'rho', u'π':'pi', 
        u'Â':'Acirc', u'ϖ':'piv', u'ϒ':'upsih', u'ϑ':'thetasym', u'Ψ':'Psi', 
        u'Ω':'Omega', u'ƒ':'fnof', u'€':'euro', u'ö':'ouml', u'Π':'Pi', 
        u'Ρ':'Rho', u'Σ':'Sigma', u'Τ':'Tau', u'Υ':'Upsilon', u'Φ':'Phi', 
        u'Χ':'Chi', u'θ':'theta', u'ι':'iota', u'κ':'kappa', u'λ':'lambda', 
        u'μ':'mu', u'∇':'nabla', u'ξ':'xi', u'ο':'omicron', u'α':'alpha', 
        u'β':'beta', u'γ':'gamma', u'δ':'delta', u'ε':'epsilon', u'ζ':'zeta', 
        u'η':'eta', u'Θ':'Theta', u'Ι':'Iota', u'Κ':'Kappa', u'Ø':'Oslash', 
        u'Μ':'Mu', u'Ν':'Nu', u'Ξ':'Xi', u'Ο':'Omicron', u'Α':'Alpha', 
        u'Β':'Beta', u'Γ':'Gamma', u'Δ':'Delta', u'Ε':'Epsilon', u'Ζ':'Zeta', 
        u'Η':'Eta', u'ô':'ocirc', u'¯':'macr', u'Ç':'Ccedil', u'⋅':'sdot', 
        u'¨':'uml', u'∞':'infin', u'∠':'ang', u'©':'copy', u'Ó':'Oacute', 
        u'≠':'ne', u'«':'laquo', u'´':'acute', u'−':'minus', u'µ':'micro', 
        u'¶':'para', u'·':'middot', u'⇐':'lArr', u'⇑':'uArr', u'⇒':'rArr', 
        u'⇓':'dArr', u'⇔':'hArr', u'Õ':'Otilde', u'∃':'exist', u'∩':'cap', 
        u'™':'trade', u'↔':'harr', u'é':'eacute', u'ℵ':'alefsym', u'"':'quot', 
        u'〈':'lang', u'〉':'rang', u'∂':'part', u'◊':'loz', u'î':'icirc', 
        u'¿':'iquest', u'<':'lt', u'&':'amp', u'∧':'and', u'⌉':'rceil', 
        u'⌈':'lceil', u'⌋':'rfloor', u'⌊':'lfloor', u'ℜ':'real', u'ù':'ugrave', 
        u'℘':'weierp', u'∉':'notin', u'∈':'isin', u'É':'Eacute', u'È':'Egrave', 
        u'Ï':'Iuml', u'Î':'Icirc', u'∏':'prod', u'Ì':'Igrave', u'Ã':'Atilde', 
        u'∀':'forall', u'Á':'Aacute', u'À':'Agrave', u'∅':'empty', u'Æ':'AElig', 
        u'Å':'Aring', u'Ä':'Auml', u'Û':'Ucirc', u'Ú':'Uacute', u'Ù':'Ugrave', 
        u'√':'radic', u'ß':'szlig', u'Þ':'THORN', u'Ý':'Yacute', u'Ü':'Uuml', 
        u'∑':'sum', u'Ò':'Ograve', u'Ñ':'Ntilde', u'Ð':'ETH', u'×':'times', 
        u'Ö':'Ouml', u'∗':'lowast', u'Ô':'Ocirc', u'ë':'euml', u'ê':'ecirc', 
        u'∫':'int', u'è':'egrave', u'ï':'iuml', u'ˆ':'circ', u'í':'iacute', 
        u'ì':'igrave', u'ã':'atilde', u'â':'acirc', u'á':'aacute', u'à':'agrave', 
        u'ç':'ccedil', u'æ':'aelig', u'å':'aring', u'ä':'auml', u'û':'ucirc', 
        u'ú':'uacute', u'⁄':'frasl', u'ø':'oslash', u'ÿ':'yuml', u'∼':'sim', 
        u'ý':'yacute', u'ü':'uuml', u'ó':'oacute', u'ò':'ograve', u'ñ':'ntilde', 
        u'ð':'eth', u'÷':'divide', u'∴':'there4', u'õ':'otilde', u'>':'gt', 
        u'≈':'asymp', u'≅':'cong', u'þ':'thorn', u'↵':'crarr', u'♦':'diams', 
        u'♥':'hearts', u'♣':'clubs', u'♠':'spades', u'¤':'curren', u'¥':'yen', 
        u'¦':'brvbar', u'§':'sect', unichr(160):'nbsp', u'¡':'iexcl', u'¢':'cent', 
        u'£':'pound', u'¬':'not', unichr(173):'shy', u'≤':'le', u'≥':'ge', u'Λ':'Lambda', 
        u'®':'reg', u'ª':'ordf', u'≡':'equiv', u'↓':'darr', u'→':'rarr', 
        u'↑':'uarr', u'←':'larr', u'°':'deg', u'±':'plusmn', u'²':'sup2', 
        u'³':'sup3', u'¼':'frac14', u'½':'frac12', u'¾':'frac34', u'˜':'tilde', 
        u'¸':'cedil', u'¹':'sup1', u'ν':'nu', u'»':'raquo', u'⊇':'supe', 
        u'⊆':'sube', u'⊄':'nsub', u'⊃':'sup', u'⊂':'sub', u'⊗':'otimes', 
        u'⊕':'oplus', u'œ':'oelig', u'Œ':'OElig', u'⊥':'perp', u'∪':'cup', 
        u'š':'scaron', u'Š':'Scaron', u'Ÿ':'Yuml', u'ℑ':'image', u'‰':'permil', 
        u'″':'Prime', u'′':'prime', u'º':'ordm', u'‹':'lsaquo', u'›':'rsaquo', 
        u'‾':'oline', u'‡':'Dagger', u'†':'dagger', u'•':'bull', u'…':'hellip', 
        u'∨':'or', u'–':'ndash', u'—':'mdash', u'∝':'prop', u'’':'rsquo', 
        u'‘':'lsquo', u'‚':'sbquo', u'”':'rdquo', u'“':'ldquo', u'„':'bdquo', 
        u' ':'emsp', u' ':'ensp', u' ':'thinsp', u'‍':'zwj', u'‌':'zwnj', 
        unichr(8207):'rlm', unichr(8206):'lrm'
    }
    
    name2unichar = {
        'zwnj':u"‌", 'aring':u"å", 'gt':u">", 'yen':u"¥", 
        'ograve':u"ò", 'Chi':u"Χ", 'delta':u"δ", 'rang':u"〉", 'trade':u"™", 
        'Ntilde':u"Ñ", 'upsih':u"ϒ", 'Yacute':u"Ý", 'Atilde':u"Ã", 'radic':u"√", 
        'otimes':u"⊗", 'aelig':u"æ", 'oelig':u"œ", 'equiv':u"≡", 'ni':u"∋", 
        'Psi':u"Ψ", 'auml':u"ä", 'cup':u"∪", 'Acirc':u"Â", 'Epsilon':u"Ε", 
        'minus':u"−", 'otilde':u"õ", 'lt':u"<", 'Icirc':u"Î", 'Eacute':u"É", 
        'Oacute':u"Ó", 'sbquo':u"‚", 'Prime':u"″", 'oslash':u"ø", 'psi':u"ψ", 
        'Kappa':u"Κ", 'rsaquo':u"›", 'acute':u"´", 'uacute':u"ú", 'sigmaf':u"ς", 
        'lrm':unichr(8206), 'zwj':u"‍", 'cedil':u"¸", 'Xi':u"Ξ", 'uml':u"¨", 'not':u"¬", 
        'kappa':u"κ", 'AElig':u"Æ", 'prime':u"′", 'Tau':u"Τ", 'lceil':u"⌈", 
        'iquest':u"¿", 'alefsym':u"ℵ", 'laquo':u"«", 'dArr':u"⇓", 'rdquo':u"”", 
        'ge':u"≥", 'Igrave':u"Ì", 'reg':u"®", 'micro':u"µ", 'shy':unichr(173), 
        'sdot':u"⋅", 'nbsp':unichr(160), 'lfloor':u"⌊", 'lArr':u"⇐", 'Auml':u"Ä", 
        'brvbar':u"¦", 'Otilde':u"Õ", 'szlig':u"ß", 'clubs':u"♣", 'agrave':u"à", 
        'Ocirc':u"Ô", 'Theta':u"Θ", 'Pi':u"Π", 'OElig':u"Œ", 'Scaron':u"Š", 
        'thetasym':u"ϑ", 'egrave':u"è", 'sub':u"⊂", 'iexcl':u"¡", 'frac12':u"½", 
        'ordf':u"ª", 'sum':u"∑", 'frac14':u"¼", 'prop':u"∝", 'Uuml':u"Ü", 
        'ntilde':u"ñ", 'sup':u"⊃", 'asymp':u"≈", 'theta':u"θ", 'prod':u"∏", 
        'nsub':u"⊄", 'hArr':u"⇔", 'rArr':u"⇒", 'Oslash':u"Ø", 'nu':u"ν", 
        'THORN':u"Þ", 'yuml':u"ÿ", 'infin':u"∞", 'Mu':u"Μ", 'le':u"≤", 
        'thinsp':u" ", 'ecirc':u"ê", 'bdquo':u"„", 'Sigma':u"Σ", 'fnof':u"ƒ", 
        'Aring':u"Å", 'tilde':u"˜", 'frac34':u"¾", 'nabla':u"∇", 'mdash':u"—", 
        'uarr':u"↑", 'permil':u"‰", 'Ugrave':u"Ù", 'eta':u"η", 'Agrave':u"À", 
        'sup1':u"¹", 'forall':u"∀", 'circ':u"ˆ", 'eth':u"ð", 'rceil':u"⌉", 
        'iuml':u"ï", 'gamma':u"γ", 'lambda':u"λ", 'harr':u"↔", 'Egrave':u"È", 
        'xi':u"ξ", 'real':u"ℜ", 'divide':u"÷", 'Ouml':u"Ö", 'image':u"ℑ", 
        'hellip':u"…", 'igrave':u"ì", 'Yuml':u"Ÿ", 'ang':u"∠", 'sube':u"⊆", 
        'loz':u"◊", 'frasl':u"⁄", 'ETH':u"Ð", 'lowast':u"∗", 'Nu':u"Ν", 
        'plusmn':u"±", 'omega':u"ω", 'chi':u"χ", 'sup2':u"²", 'sup3':u"³", 
        'Aacute':u"Á", 'cent':u"¢", 'Iacute':u"Í", 'oline':u"‾", 'Ecirc':u"Ê", 
        'Beta':u"Β", 'perp':u"⊥", 'emsp':u" ", 'there4':u"∴", 'pi':u"π", 
        'iota':u"ι", 'empty':u"∅", 'euml':u"ë", 'notin':u"∉", 'Upsilon':u"Υ", 
        'para':u"¶", 'epsilon':u"ε", 'Delta':u"Δ", 'weierp':u"℘", 'uuml':u"ü", 
        'part':u"∂", 'icirc':u"î", 'bull':u"•", 'omicron':u"ο", 'upsilon':u"υ", 
        'copy':u"©", 'Iuml':u"Ï", 'Lambda':u"Λ", 'spades':u"♠", 'ndash':u"–", 
        'ensp':u" ", 'ccedil':u"ç", 'Ucirc':u"Û", 'cap':u"∩", 'ocirc':u"ô", 
        'mu':u"μ", 'scaron':u"š", 'lsquo':u"‘", 'isin':u"∈", 'Zeta':u"Ζ", 
        'supe':u"⊇", 'deg':u"°", 'and':u"∧", 'tau':u"τ", 'pound':u"£", 
        'curren':u"¤", 'int':u"∫", 'ucirc':u"û", 'rfloor':u"⌋", 'crarr':u"↵", 
        'ugrave':u"ù", 'exist':u"∃", 'cong':u"≅", 'Dagger':u"‡", 'oplus':u"⊕", 
        'times':u"×", 'atilde':u"ã", 'piv':u"ϖ", 'iacute':u"í", 'Euml':u"Ë", 
        'Phi':u"Φ", 'raquo':u"»", 'lsaquo':u"‹", 'quot':u"\"", 'Uacute':u"Ú", 
        'Omicron':u"Ο", 'ne':u"≠", 'Iota':u"Ι", 'eacute':u"é", 'rarr':u"→", 
        'yacute':u"ý", 'Rho':u"Ρ", 'darr':u"↓", 'Alpha':u"Α", 'zeta':u"ζ", 
        'Omega':u"Ω", 'acirc':u"â", 'sim':u"∼", 'phi':u"φ", 'diams':u"♦", 
        'macr':u"¯", 'larr':u"←", 'Ccedil':u"Ç", 'ordm':u"º", 'uArr':u"⇑", 
        'beta':u"β", 'Eta':u"Η", 'rho':u"ρ", 'aacute':u"á", 'alpha':u"α", 
        'rlm':unichr(8207), 'middot':u"·", 'Gamma':u"Γ", 'euro':u"€", 'lang':u"〈", 
        'dagger':u"†", 'amp':u"&", 'rsquo':u"’", 'thorn':u"þ", 'ouml':u"ö", 
        'or':u"∨", 'Ograve':u"Ò", 'sect':u"§", 'ldquo':u"“", 'hearts':u"♥", 
        'sigma':u"σ", 'oacute':u"ó"
    }
    
    def __init__(self):
        super(Entity, self).__init__()
        self.version = 0.1
        self.unichar2entitycode = self.unichar2entitycode
        self.entitycode2unichar = self.entitycode2unichar
        self.unichar2name = self.unichar2name
        self.name2unichar = self.name2unichar
    
    def decode(self, s, mode="html"):
        """
        Decode an mnemonic ("html") or decimal/hexadecimal ("xml") entity reference 
        into a unicode character
        """
        if (mode == "html"):
            codepoints = htmlentitydefs.name2codepoint
            codes = '|'.join(codepoints)            
            result = re.sub('&(%s);' % codes, lambda m: unichr(codepoints[m.group(1)]), s)
        else:
            codes = '|'.join(self.entitycode2unichar)
            result = re.sub('(%s)' % codes, lambda m: self.entitycode2unichar[m.group(1)], s)
            
        return unicode(result)
    
    def encode(self, s,mode="html", preserve_xml_chars=False):
        """
        Encode a unicode character to mnemonic value for 'html' mode 
        and to decimal or hexadecimal value for 'xml' mode.
        """
        
        _entitydefs = htmlentitydefs.entitydefs
        codepoints = htmlentitydefs.name2codepoint.values()
        _names = htmlentitydefs.codepoint2name
        
        xmlchars = {
            u"'":{'code':"&#39;", 'name':"apos"},
            u'"':{'code':"&#34;", 'name':"quot"},
            u'&':{'code':"&#38;", 'name':"amp"},
            u'<':{'code':"&#60;", 'name':"lt"},
            u'>':{'code':"&#62;", 'name':"gt"}
        }
        
        arr = []
        if mode == "html" and preserve_xml_chars == False:
            s = re.sub("&", "&amp;", s);
            for i in s:
                curChar = i
                curCharId = ord(curChar)
                if ((curCharId not in arr) and (curCharId in codepoints) and (curChar != "&")):                    
                    try:
                        friendlyName = "&" + self.unichar2name[curChar] + ";"
                        s = re.sub(curChar, friendlyName, s)
                        arr.append(curCharId)
                    except:
                        pass
        elif mode == "html" and preserve_xml_chars == True:
            #s = re.sub("&", "&amp;", s);
            for i in s:
                curChar = i
                curCharId = ord(curChar)
                if ((curCharId not in arr) and (curChar not in xmlchars) and (curCharId in codepoints) and (curChar != "&")):                    
                    try:
                        friendlyName = "&" + self.unichar2name[curChar] + ";"
                        s = re.sub(curChar, friendlyName, s)
                        arr.append(curCharId)
                    except:
                        pass            
        else:
            for i in s:
                curChar = i
                curCharId = ord(curChar)
                if (curChar not in xmlchars):
                    try:
                        entityCode = self.unichar2entitycode[curChar]
                        s = s.replace(curChar, entityCode)
                        arr.append(curCharId)
                    except KeyError:
                        pass
        
        return s.encode("utf-8")
    



class EntityTests(unittest.TestCase):
    
    def setUp(self):
        # let's start small :)
        self.str1 = u"André Berg"
        self.str2 = "Andr&eacute; Berg"
        # getting bigger...
        self.testData = u"\"å>¥òΧδ〉™ÑϒÝÃ√⊗æœ≡∋Ψä∪ÂΕ−õ<ÎÉÓ‚″øψΚ›´úς‎‍¸Ξ¨¬κÆ′Τ⌈¿ℵ«⇓”≥Ì®µ­⋅ ⌊⇐Ä¦Õß♣àÔΘΠŒŠϑè⊂¡½ª∑¼∝Üñ⊃≈θ∏⊄⇔⇒ØνÞÿ∞Μ≤ ê„ΣƒÅ˜¾∇—↑‰ÙηÀ¹∀ˆð⌉ïγλ↔Èξℜ÷Öℑ…ìŸ∠⊆◊⁄Ð∗Ν±ωχ²³Á¢Í‾ÊΒ⊥ ∴πι∅ë∉Υ¶εΔ℘ü∂î•ου©ÏΛ♠– çÛ∩ôμš‘∈Ζ⊇°∧τ£¤∫û⌋↵ù∃≅‡⊕×ãϖíËΦ»‹ÚΟ≠Ιé→ýΡ↓ΑζΩâ∼φ♦¯←Çº⇑βΗρáα‏·Γ€〈†&’þö∨Ò§“♥σó"
        # monster slam!
        self.testDataHandEncodedHTML = "&quot;&aring;&gt;&yen;&ograve;&Chi;&delta;&rang;&trade;&Ntilde;&upsih;&Yacute;&Atilde;&radic;&otimes;&aelig;&oelig;&equiv;&ni;&Psi;&auml;&cup;&Acirc;&Epsilon;&minus;&otilde;&lt;&Icirc;&Eacute;&Oacute;&sbquo;&Prime;&oslash;&psi;&Kappa;&rsaquo;&acute;&uacute;&sigmaf;&lrm;&zwj;&cedil;&Xi;&uml;&not;&kappa;&AElig;&prime;&Tau;&lceil;&iquest;&alefsym;&laquo;&dArr;&rdquo;&ge;&Igrave;&reg;&micro;&shy;&sdot;&nbsp;&lfloor;&lArr;&Auml;&brvbar;&Otilde;&szlig;&clubs;&agrave;&Ocirc;&Theta;&Pi;&OElig;&Scaron;&thetasym;&egrave;&sub;&iexcl;&frac12;&ordf;&sum;&frac14;&prop;&Uuml;&ntilde;&sup;&asymp;&theta;&prod;&nsub;&hArr;&rArr;&Oslash;&nu;&THORN;&yuml;&infin;&Mu;&le;&thinsp;&ecirc;&bdquo;&Sigma;&fnof;&Aring;&tilde;&frac34;&nabla;&mdash;&uarr;&permil;&Ugrave;&eta;&Agrave;&sup1;&forall;&circ;&eth;&rceil;&iuml;&gamma;&lambda;&harr;&Egrave;&xi;&real;&divide;&Ouml;&image;&hellip;&igrave;&Yuml;&ang;&sube;&loz;&frasl;&ETH;&lowast;&Nu;&plusmn;&omega;&chi;&sup2;&sup3;&Aacute;&cent;&Iacute;&oline;&Ecirc;&Beta;&perp;&emsp;&there4;&pi;&iota;&empty;&euml;&notin;&Upsilon;&para;&epsilon;&Delta;&weierp;&uuml;&part;&icirc;&bull;&omicron;&upsilon;&copy;&Iuml;&Lambda;&spades;&ndash;&ensp;&ccedil;&Ucirc;&cap;&ocirc;&mu;&scaron;&lsquo;&isin;&Zeta;&supe;&deg;&and;&tau;&pound;&curren;&int;&ucirc;&rfloor;&crarr;&ugrave;&exist;&cong;&Dagger;&oplus;&times;&atilde;&piv;&iacute;&Euml;&Phi;&raquo;&lsaquo;&Uacute;&Omicron;&ne;&Iota;&eacute;&rarr;&yacute;&Rho;&darr;&Alpha;&zeta;&Omega;&acirc;&sim;&phi;&diams;&macr;&larr;&Ccedil;&ordm;&uArr;&beta;&Eta;&rho;&aacute;&alpha;&rlm;&middot;&Gamma;&euro;&lang;&dagger;&amp;&rsquo;&thorn;&ouml;&or;&Ograve;&sect;&ldquo;&hearts;&sigma;&oacute;"
        self.testDataHandEncodedXML = "\"&#xe5;>&#xa5;&#xf2;&#935;&#948;&#9002;&#8482;&#xd1;&#978;&#xdd;&#xc3;&#8730;&#8855;&#xe6;&#339;&#8801;&#8715;&#936;&#xe4;&#8746;&#xc2;&#917;&#8722;&#xf5;<&#xce;&#xc9;&#xd3;&#8218;&#8243;&#xf8;&#968;&#922;&#8250;&#xb4;&#xfa;&#962;&#8206;&#8205;&#xb8;&#926;&#xa8;&#xac;&#954;&#xc6;&#8242;&#932;&#8968;&#xbf;&#8501;&#xab;&#8659;&#8221;&#8805;&#xcc;&#xae;&#xb5;&#xad;&#8901;&#xa0;&#8970;&#8656;&#xc4;&#xa6;&#xd5;&#xdf;&#9827;&#xe0;&#xd4;&#920;&#928;&#338;&#352;&#977;&#xe8;&#8834;&#xa1;&#xbd;&#xaa;&#8721;&#xbc;&#8733;&#xdc;&#xf1;&#8835;&#8776;&#952;&#8719;&#8836;&#8660;&#8658;&#xd8;&#957;&#xde;&#xff;&#8734;&#924;&#8804;&#8201;&#xea;&#8222;&#931;&#402;&#xc5;&#732;&#xbe;&#8711;&#8212;&#8593;&#8240;&#xd9;&#951;&#xc0;&#xb9;&#8704;&#710;&#xf0;&#8969;&#xef;&#947;&#955;&#8596;&#xc8;&#958;&#8476;&#xf7;&#xd6;&#8465;&#8230;&#xec;&#376;&#8736;&#8838;&#9674;&#8260;&#xd0;&#8727;&#925;&#xb1;&#969;&#967;&#xb2;&#xb3;&#xc1;&#xa2;&#xcd;&#8254;&#xca;&#914;&#8869;&#8195;&#8756;&#960;&#953;&#8709;&#xeb;&#8713;&#933;&#xb6;&#949;&#916;&#8472;&#xfc;&#8706;&#xee;&#8226;&#959;&#965;&#xa9;&#xcf;&#923;&#9824;&#8211;&#8194;&#xe7;&#xdb;&#8745;&#xf4;&#956;&#353;&#8216;&#8712;&#918;&#8839;&#xb0;&#8743;&#964;&#xa3;&#xa4;&#8747;&#xfb;&#8971;&#8629;&#xf9;&#8707;&#8773;&#8225;&#8853;&#xd7;&#xe3;&#982;&#xed;&#xcb;&#934;&#xbb;&#8249;&#xda;&#927;&#8800;&#921;&#xe9;&#8594;&#xfd;&#929;&#8595;&#913;&#950;&#937;&#xe2;&#8764;&#966;&#9830;&#xaf;&#8592;&#xc7;&#xba;&#8657;&#946;&#919;&#961;&#xe1;&#945;&#8207;&#xb7;&#915;&#8364;&#9001;&#8224;&&#8217;&#xfe;&#xf6;&#8744;&#xd2;&#xa7;&#8220;&#9829;&#963;&#xf3;"
    
    def testEncode(self):
        self.assertEqual(Entity().encode(self.str1), self.str2)
    
    def testDecode(self):
        self.assertEqual(Entity().decode(self.str2), self.str1)
    
    def testEncodeTestDataHTML(self):
        self.assertEquals(Entity().encode(self.testData), (self.testDataHandEncodedHTML))
    
    def testEncodeTestDataXML(self):
        self.assertEquals(Entity().encode(self.testData, mode="xml"), self.testDataHandEncodedXML)
    
    def testDecodeTestDataHandEncodedHTML(self):
        self.assertEquals(Entity().decode(self.testDataHandEncodedHTML), self.testData)
    
    def testDecodeTestDataHandEncodedXML(self):
        self.assertEquals(Entity().decode(self.testDataHandEncodedXML, mode="xml"), self.testData)
    
    def testEncodeDecodeRoundtripHTML(self):
        self.assertEquals(Entity().decode(Entity().encode(self.testData)), self.testData)
    
    def testEncodeDecodeRoundtripXML(self):
        self.assertEquals(Entity().decode(Entity().encode(self.testData, mode="xml"), mode="xml"), self.testData)
    


##
#  printDict
#
#  Created by Andre Berg on 2009-03-24.
#  Copyright 2009 Berg Media. All rights reserved.
#
#  License: Apache 2.0
#  Warranty: "AS-IS", no warranties of any kind, either express or implied
#
def printDict(d, invert=False, silent=False, preset="Python", beginChar=None, endChar=None, separator=None, keyPrefix=None, keySuffix=None, valuePrefix=None, valueSuffix=None):
    """Print a string representation of a dictionary 'd' optionally inversing its keys and values.
    
    Works a bit like PHP's 'print_r' function.
        
    Params:
         invert: inverts keys and values in 'd'
         
         silent: if True does not use 'print' to output
                 the dictionary, but instead just returns it 
                 as string
                 
         preset: the name of a programming language for which
                 the printed out dictionary should be semantically 
                 correct. This just changes the prefixes and suffixes 
                 prepended/appended to each key and each value.
                 
                 Predefined values currently include 'Python' (default)
                 'Ruby' and 'AppleScript'. You can define your own 
                 presets in the source below or just use the following 
                 seven params to overwrite on a single-case basis.
                 
    Returns:
         A string with the printed/converted dictionary, or 
         False in case of an error
    """
    
    if not isinstance(d, dict):
        return d
    if (invert == True):
        i = {}
        for k,v in d.items():
            i[v] = k
        d = i
    j = 0
    
    dlen = len(d)
    result = u""
    
    try:
        sep = ", "
        bc = "{"
        ec = "}"
        
        if (preset == "Python"):
            kp = "u'"
            ks = "'"
            vp = ":'"
            vs = "'"            
        elif (preset == "Ruby"):
            kp = "'"
            ks = "' => "
            vp = "'"
            vs = "'"
        elif (preset == "AppleScript"):
            kp = "|"
            ks = "|:"
            vp = "\""
            vs = "\""
        else:
            kp = ""
            ks = ""
            vp = ""
            vs = ""
        
        if (keyPrefix is not None):
            kp = keyPrefix
        if (keySuffix is not None):
            ks = keySuffix
        if (valuePrefix is not None):
            vp = valuePrefix
        if (valueSuffix is not None):
            vs = valueSuffix
        if (beginChar is not None):
            bc = beginChar
        if (endChar is not None):
            ec = endChar
        if (separator is not None):
            sep = separator                
        
        for (k, v) in d.items():
            if (j == 0):
                result += bc + kp + k + ks + vp + v + vs + sep
            elif (j < dlen-1):
                result += kp + k + ks + vp + v + vs + sep
            else:
                result += kp + k + ks + vp + v + vs + ec
            j+=1
        
        # fix tripple double quotes - no language accepts these
        # at least not to the knowledge of the author
        result = re.sub('"""', r'"\""', result)
        
        if (silent != True):
            print result
        return result
    except:
        return False



# ====================
# = Main starts here =
# ====================

def main():
    
    name = "Entity Encoder/Decoder"
    version = "0.2"
    shortinfo = "%s v%s" % (name, version)              
    license = u"Copyright 2009 André Berg (Berg Media)                                               \
                Licensed under the MIT License, http://www.opensource.org/licenses/mit-license.php"
                   
    usage = '\n'\
            '   entity -d|--decode|-e|--encode [-m|--mode <"html|xml">] [-x|--preserve-xml-chars] [input] => [processed output] -OR-\n'\
            '   entity -p|--print-dict <"u2e|e2u|u2n|n2u"> [-l|--lang <"Python|Ruby|AppleScript">] => [conversion table output]\n'
           
    
    parser = OptionParser(version=shortinfo, usage=usage, description=license)
    parser.add_option("-m", "--mode", dest="mode", type="string", help="coding scheme: html or xml [default: %default]")
    parser.add_option("-l", "--lang", dest="lang", type="choice", choices=["Python", "Ruby", "AppleScript"], help="the language syntax for outputting entity dictionaries: currently supported \"Ruby\", \"Python\" or \"AppleScript\". [default: %default]")
    parser.add_option("-d", "--decode", dest="action", action="store_const", const="decode", help="action: decode")
    parser.add_option("-e", "--encode", dest="action", action="store_const", const="encode", help="action: encode")
    parser.add_option("-p", "--print-dict", dest="print_dict", type="choice", choices=("u2e", "e2u", "u2n", "n2u"), metavar="DICT", help="action: print entity dictionary (in language set by -l|--lang) [default: %default]")
    parser.add_option("-x", "--preserve-xml-chars", dest="preserve_xml_chars", action="store_true", default=False, help="preserves xml special chars (<>&\"\') in html mode [default: %default]")
    
    parser.set_defaults(mode="html", lang="Python")
    
    #sys.argv = [sys.argv[0],"-p", "u2e", "-x", "-l", "Rubyx", "andré berg", "<a href=\"images/test.png&x=1\">test öä & png</a>"]
    #sys.argv = [sys.argv[0], "-d", "-x", u"andr&eacute; berg", u"<a href=\"images/test.png&x=1\">test &ouml;&auml; & png</a>"]
    (opts, args) = parser.parse_args()
        
    if (opts.action and opts.print_dict):
        if opts.action == "encode":
            parser.error("options --encode and --print-dict are mutually exclusive")
        elif opts.action == "decode":
            parser.error("options --decode and --print-dict are mutually exclusive")
    
    if opts.print_dict and opts.lang == None:
        parser.error("--print-dict specified but missing --lang")
        
    res = u""
    for arg in args:
        res += arg.decode("utf-8")
    
    if opts.action == "encode":
        #print "encoding..."
        print Entity().encode(res, opts.mode, opts.preserve_xml_chars)
    elif opts.action == "decode":
        #print "decoding..."
        result = Entity().decode(res, opts.mode)
        print result.encode("utf-8")
    elif opts.print_dict == "u2e":
        print printDict(Entity().unichar2entitycode, preset=opts.lang)
    elif opts.print_dict == "e2u":
        print printDict(Entity().entitycode2unichar, preset=opts.lang)
    elif opts.print_dict == "u2n":
        print printDict(Entity().unichar2name, preset=opts.lang)
    elif opts.print_dict == "n2u":
        print printDict(Entity().name2unichar, preset=opts.lang)
    else:
        print usage
        #print opts, args
        return 1
    
    return 0



if __name__ == '__main__':
    # test command line options
    #sys.argv.append('-v')
    #sys.argv.append('-h')
    #unittest.main()
    main()
