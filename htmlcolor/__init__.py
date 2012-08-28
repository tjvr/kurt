#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010, David Sveningsson <ext@sidvind.com>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the author nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""
Parse HTML/CSS colors
"""

import unittest
import re

from names import names

DecimalFactory = lambda v: int(v,16)
FloatFactory = lambda v: int(v,16)/255.0
HexFactory = lambda v: v

# Get a list of all hexadecimal digits.
_hex_literals = [hex(v)[-1] for v in range(0,16)]

def enforceComponents():
    def decorate(func):
        def wrapper(self, *args, **kwargs):
            n = self.Components
            fill = self.ResultFactory(self.Fill)
            
            assert n in [3,4]
            
            result = func(self, *args, **kwargs)
            components = len(result)
            
            if components == n:
                return result
            elif components > n:
                return result[:n]
            else:
                return result + (n - components) * (fill,)
        return wrapper
    return decorate

class Parser:
    def __init__(self, factory=DecimalFactory, components=3, fill='ff'):
        self.ResultFactory = factory
        self.Components = components
        self.Fill = fill
    
    @enforceComponents()
    def parse(self, string):
        """
        Parses a HTML/CSS color.
        
        :param string: The string to parse
        :return: A tuple containing the color components.
        """
        if not isinstance(string, basestring):
            raise ValueError, 'must be a string'
        
        func = self._detect_format(string)
        result = func(string)
        
        return tuple([self.ResultFactory(x) for x in result])
    
    @staticmethod
    def _parse_hex(string):
        if string[0] == '#':
            string = string[1:]
        
        n = len(string)
        fmt = {
            3: '([0-9A-Fa-f]{1})' * 3, # shorthand RGB
            4: '([0-9A-Fa-f]{1})' * 4, # shorthand RGBA
            6: '([0-9A-Fa-f]{2})' * 3, # RGB
            8: '([0-9A-Fa-f]{2})' * 4 # RGBA
        }
        
        match = re.match(fmt[n], string)
        
        if match:
            groups = match.groups()
            
            # shorthand RGB{,A} must be extended
            if n in [3,4]:
                groups = tuple([2*x for x in groups])
            
            return groups
        else:
            raise ValueError,'Unable to parse "%s"' % (string)
    
    @staticmethod
    def _parse_name(string):
        try:
            return names[string]
        except KeyError:
            raise ValueError,'Unrecognized color name "%s"' % (string)
    
    @staticmethod
    def _detect_format(string):
        if string[0] == '#':
            return Parser._parse_hex
        elif [item for item in string if item not in _hex_literals] == []:
            return Parser._parse_hex
        else:
            return Parser._parse_name

class factory_test(unittest.TestCase):
    def setUp(self):
        self.p = Parser()
    
    def test_decimal(self):
        self.p.ResultFactory = DecimalFactory
        self.p.Components = 3
        self.assertEqual(self.p.parse('#fff'), (255, 255, 255))
    
    def test_float(self):
        self.p.ResultFactory = FloatFactory
        self.p.Components = 3
        self.assertEqual(self.p.parse('#fff'), (1.0, 1.0, 1.0))
    
    def test_hex(self):
        self.p.ResultFactory = HexFactory
        self.p.Components = 3
        self.assertEqual(self.p.parse('#fff'), ('ff', 'ff', 'ff'))
    
    def test_custom(self):
        self.p.ResultFactory = lambda x: int(x,16) * 2
        self.p.Components = 3
        self.assertEqual(self.p.parse('#fff'), (510, 510, 510))

class components_test(unittest.TestCase):
    def setUp(self):
        self.p = Parser()
    
    def test_invalid(self):
        self.p.ResultFactory = DecimalFactory
        for c in [2,5]:
            self.p.Components = c
            self.assertRaises(AssertionError, self.p.parse, '#fff')
    
    def test_valid(self):
        self.p.ResultFactory = DecimalFactory
        self.p.Components = 3
        self.assertEqual(self.p.parse('#fff'), (255, 255, 255))
        self.p.Components = 4
        self.assertEqual(self.p.parse('#ffff'), (255, 255, 255, 255))

class test(unittest.TestCase):
    def setUp(self):
        self.p = Parser(factory=DecimalFactory, components=3)
    
    def test_invalid(self):
        self.assertRaises(ValueError, self.p.parse, 0)
    
    def test_invalid_hex(self):
        self.assertRaises(ValueError, self.p.parse, '#foobar')
    
    def test_short_hex_rgb(self):
        self.assertEqual(self.p.parse('#f70'), (255, 119, 0))
    
    def test_short_hex_rgba(self):
        self.p.Components = 4
        self.assertEqual(self.p.parse('#f70f'), (255, 119, 0, 255))
    
    def test_decimal_rgb(self):
        self.assertEqual(self.p.parse('#ff7700'), (255, 119, 0))
    
    def test_decimal_rgba_fill(self):
        self.p.Components = 4
        self.assertEqual(self.p.parse('#ff7700'), (255, 119, 0, 255))
    
    def test_decimal_rgba(self):
        self.p.Components = 4
        self.assertEqual(self.p.parse('#ff770077'), (255, 119, 0, 119))

    def test_float_rgb(self):
        self.p.ResultFactory = FloatFactory
        [self.assertAlmostEqual(x,y,1) for (x,y) in zip(self.p.parse('#ff7700'), (1.0, 0.46, 0.0))]
    
    def test_float_rgba_fill(self):
        self.p.ResultFactory = FloatFactory
        self.p.Components = 4
        [self.assertAlmostEqual(x,y,1) for (x,y) in zip(self.p.parse('#ff7700'), (1.0, 0.46, 0.0, 1.0))]
    
    def test_float_rgba(self):
        self.p.ResultFactory = FloatFactory
        self.p.Components = 4
        [self.assertAlmostEqual(x,y,1) for (x,y) in zip(self.p.parse('#ff770077'), (1.0, 0.46, 0.0, 0.46))]
    
    def test_sign(self):
        self.assertEqual(self.p.parse('#ff7700'), (255, 119, 0))
        self.assertEqual(self.p.parse('ff7700'), (255, 119, 0))
    
    def test_name(self):
        self.assertEqual(self.p.parse('red'), (255, 0, 0))
    
    def test_invalid_name(self):
        self.assertRaises(ValueError, self.p.parse, 'foobar')
