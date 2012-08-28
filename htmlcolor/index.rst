Documentation
=============

The htmlcolor module parses HTML/CSS colors. It accepts regular hexadecimal
notation, CSS shorthand notation and named colors. In addition it also supports
four-component colors such as RGBA.

Sample usage
------------

Parsing a color, regular hex-notation, shorthand notation or named colors. It
also supports hex-notation without the #-sign.

>>> import htmlcolor
>>> parser = htmlcolor.Parser()
>>> parser.parse('#ff7700')
(255, 119, 0)
>>> parser.parse('#f70')
(255, 119, 0)
>>> parser.parse('hotpink')
(255, 105, 180)
>>> parser.parse('ff7700')
(255, 119, 0)

Result factory allow to convert the color elements.

>>> parser = htmlcolor.Parser(factory=htmlcolor.FloatFactory)
>>> parser.parse('#ff7700')
(1.0, 0.46666666666666667, 0.0)
>>> parser = htmlcolor.Parser(factory=lambda x: int(x,16)*2)
>>> parser.parse('#ff7700')
(510, 238, 0)

Also supports four-component colors such as RGBA.

>>> parser = htmlcolor.Parser(components=4)
>>> parser.parse('#ff7700')
(510, 238, 0, 255)
>>> parser.parse('#ff770020')
(510, 238, 0, 32)

Parser object
-------------

.. class:: htmlcolor.Parser([factory=DecimalFactory, components=3, fill='ff'])
  
  *factory* is the result factory.
  
  *components* is the number of components to handle, insufficient fields will
  fill the color using *fill*.
  
  *fill* is the hexadecimal notation to use as filling when there aren't enough
  components in the string.
  
  .. method:: parse(string) -> tuple
    
    Parses *string* an and returns a tuple of color elements. The number of
    elements depends on *components*.
  
  .. attribute:: ResultFactory
   
    A callable which converts the format of the color elements.
  
  .. attribute:: Components
  
    Specifies how many color components the result should be. (RGB: 3, RGBA: 4)
  
  .. attribute:: Fill
  
    Filling to use when there aren't enough components in the string being
    parsed.

Builtin factories
-----------------

.. function:: DecimalFactory

  Converts from hexadecimal notation to decimal. Values between 0-255.

.. function:: FloatFactory

  Converts from hexadecimal notation to float. Values between 0.0-1.0.

.. function:: HexFactory

  Converts from hexadecimal notation to hex (string). Values between '00'-'FF'.

