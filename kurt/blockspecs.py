#coding=utf8

# Copyright © 2012 Tim Radvan
# 
# This file is part of Kurt.
# 
# Kurt is free software: you can redistribute it and/or modify it under the 
# terms of the GNU Lesser General Public License as published by the Free 
# Software Foundation, either version 3 of the License, or (at your option) any 
# later version.
# 
# Kurt is distributed in the hope that it will be useful, but WITHOUT ANY 
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR 
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more 
# details.
# 
# You should have received a copy of the GNU Lesser General Public License along 
# with Kurt. If not, see <http://www.gnu.org/licenses/>.

"""Provides information about block types.
Classes:
    BlockType - information about a single type of block.

Values:
    blocks - list of BlockType objects.
    blocks_by_cmd - dict of BlockType objects indexed by their `command`.

Other values:
    block_plugin_inserts - format strings for insert types, used in 
                           Block.to_block_plugin()

The blocks list is compiled by parsing blockspecs copied directly from Scratch's 
Squeak source code.
"""
from construct import *
from construct.text import *

import re



string = QuotedString("string", start_quote="'", end_quote="'", esc_char="\\")

symbol = Struct("symbol",
    Literal("#"),    
    StringAdapter(GreedyRange(CharOf("value", set("+*/\<>=&|~:-0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"))))
    # _=@%?!`^$
)

spacer = Struct("spacer",
    Literal("#"),
    CharOf("", "~-"),
    Whitespace(),
    Value("is_block", lambda c: False)
)

value = Select("value",
    symbol,
    string,
    FloatNumber("value"),
    DecNumber("value"),
    Struct("negative number",
        Literal("-"),
        DecNumber("number"),
        Value("value", lambda ctx: -ctx['number']),
    ),
        
)

blockspec = Struct("blockspec",
    Literal("("),
    Whitespace(),
    Rename("text", string),
    Whitespace(),
    Rename("flag", symbol),
    Whitespace(),
    Rename("command", symbol),
    Whitespace(),
    OptionalGreedyRepeater(Rename("defaults", Struct("",
        value,
        Whitespace(),
    ))),
    Whitespace(),
    Literal(")"),
    Whitespace(),
    
    Value("is_block", lambda c: True)
)

category = Struct("category",
    Rename("name", string),
    Whitespace(),
    Rename("blocks", OptionalGreedyRepeater(
        Select("",
            blockspec,
            spacer,
        ),
    )),
    Whitespace(),
)

blockspecs = Struct("blockspecs",
    Rename("categories", OptionalGreedyRepeater(category)),
    #StringAdapter(OptionalGreedyRange(Char("leftovers"))), # used for DEBUG
    Terminator,
)



### Taken from Squeak source, with modifications.
# Note: apostrophes ' and slashes \ need special escaping.
squeak_blockspecs = """'control' ('when green flag clicked' #S #EventHatMorph) ('when %k key pressed' #K #KeyEventHatMorph) ('when %m clicked' #M #MouseClickEventHatMorph) #- ('wait %n secs' #t #wait:elapsed:from: 1) #- ('forever' #c #doForever) ('repeat %n' #c #doRepeat 10) #- ('broadcast %e' #- #broadcast:) ('broadcast %e and wait' #s #doBroadcastAndWait) ('when I receive %e' #E #-) #- ('forever if %b' #c #doForeverIf) ('if %b' #c #doIf) ('if %b' #c #doIfElse) ('wait until %b' #s #doWaitUntil) ('repeat until %b' #c #doUntil) #- ('stop script' #s #doReturn) ('stop all' #- #stopAll) 'operators' ('%n + %n' #r #+ #- #-) ('%n - %n' #r #- #- #-) ('%n * %n' #r #* #- #-) ('%n / %n' #r #/ #- #-) #- ('pick random %n to %n' #r #randomFrom:to: 1 10) #- ('%s < %s' #b #< '' '') ('%s = %s' #b #= '' '') ('%s > %s' #b #> '' '') #- ('%b and %b' #b #&) ('%b or %b' #b #|) ('not %b' #b #not) #- ('join %s %s' #r #concatenate:with: 'hello ' 'world') ('letter %n of %s' #r #letter:of: 1 'world') ('length of %s' #r #stringLength: 'world') #- ('%n mod %n' #r #\\\\ #- #-) ('round %n' #r #rounded #-) #- ('%f of %n' #r #computeFunction:of: 'sqrt' 10) ('A block with color %C and color %c' #- #thingwithColor:andColor:) 'sound' ('play sound %S' #- #playSound:) ('play sound %S until done' #s #doPlaySoundAndWait) ('stop all sounds' #- #stopAllSounds) #- ('play drum %D for %n beats' #t #drum:duration:elapsed:from: 48 0.2) ('rest for %n beats' #t #rest:elapsed:from: 0.2) #- ('play note %N for %n beats' #t #noteOn:duration:elapsed:from: 60 0.5) ('set instrument to %I' #- #midiInstrument: 1) #- ('change volume by %n' #- #changeVolumeBy: -10) ('set volume to %n%' #- #setVolumeTo: 100) ('volume' #r #volume) #- ('change tempo by %n' #- #changeTempoBy: 20) ('set tempo to %n bpm' #- #setTempoTo: 60) ('tempo' #r #tempo) 'motor' ('motor on for %n secs' #t #motorOnFor:elapsed:from: 1) ('motor on' #- #allMotorsOn) ('motor off' #- #allMotorsOff) ('motor power %n' #- #startMotorPower: 100) ('motor direction %W' #- #setMotorDirection: 'this way') 'variables' ('show variable %v' #- #showVariable:) ('hide variable %v' #- #hideVariable:) 'list' ('add %s to %L' #- #append:toList: 'thing') #- ('delete %y of %L' #- #deleteLine:ofList: 1) ('insert %s at %i of %L' #- #insert:at:ofList: 'thing' 1) ('replace item %i of %L with %s' #- #setLine:ofList:to: 1 'list' 'thing') #- ('item %i of %L' #r #getLine:ofList: 1) ('length of %L' #r #lineCountOfList:) ('%L contains %s' #b #list:contains: 'list' 'thing')"""

squeak_stage_blockspecs = """'sensing' ('ask %s and wait' #s #doAsk 'What\\'s your name?') ('answer' #r #answer) #- ('mouse x' #r #mouseX) ('mouse y' #r #mouseY) ('mouse down?' #b #mousePressed) #- ('key %k pressed?' #b #keyPressed: 'space') #- ('reset timer' #- #timerReset) ('timer' #r #timer) #- ('%a of %m' #r #getAttribute:of:) #- ('loudness' #r #soundLevel) ('loud?' #b #isLoud) #~ ('%H sensor value' #r #sensor: 'slider') ('sensor %h?' #b #sensorPressed: 'button pressed') 'looks' ('switch to background %l' #- #showBackground: 'background1') ('next background' #- #nextBackground) ('background #' #r #backgroundIndex) #- ('change %g effect by %n' #- #changeGraphicEffect:by: 'color' 25) ('set %g effect to %n' #- #setGraphicEffect:to: 'color' 0) ('clear graphic effects' #- #filterReset) #- 'pen' ('clear' #- #clearPenTrails)"""

squeak_sprite_blockspecs = """'motion' ('move %n steps' #- #forward:) ('turn cw %n degrees' #- #turnRight: 15) ('turn ccw %n degrees' #- #turnLeft: 15) #- ('point in direction %d' #- #heading: 90) ('point towards %m' #- #pointTowards:) #- ('go to x:%n y:%n' #- #gotoX:y: 0 0) ('go to %m' #- #gotoSpriteOrMouse:) ('glide %n secs to x:%n y:%n' #t #glideSecs:toX:y:elapsed:from: 1 50 50) #- ('change x by %n' #- #changeXposBy: 10) ('set x to %n' #- #xpos: 0) ('change y by %n' #- #changeYposBy: 10) ('set y to %n' #- #ypos: 0) #- ('if on edge, bounce' #- #bounceOffEdge) #- ('x position' #r #xpos) ('y position' #r #ypos) ('direction' #r #heading) 'pen' ('clear' #- #clearPenTrails) #- ('pen down' #- #putPenDown) ('pen up' #- #putPenUp) #- ('set pen color to %c' #- #penColor:) ('change pen color by %n' #- #changePenHueBy:) ('set pen color to %n' #- #setPenHueTo: 0) #- ('change pen shade by %n' #- #changePenShadeBy:) ('set pen shade to %n' #- #setPenShadeTo: 50) #- ('change pen size by %n' #- #changePenSizeBy: 1) ('set pen size to %n' #- #penSize: 1) #- ('stamp' #- #stampCostume) 'looks' ('switch to costume %l' #- #lookLike:) ('next costume' #- #nextCostume) ('costume #' #r #costumeIndex) #- ('say %s for %n secs' #t #say:duration:elapsed:from: 'Hello!' 2) ('say %s' #- #say: 'Hello!') ('think %s for %n secs' #t #think:duration:elapsed:from: 'Hmm...' 2) ('think %s' #- #think: 'Hmm...') #- ('change %g effect by %n' #- #changeGraphicEffect:by: 'color' 25) ('set %g effect to %n' #- #setGraphicEffect:to: 'color' 0) ('clear graphic effects' #- #filterReset) #- ('change size by %n' #- #changeSizeBy:) ('set size to %n%' #- #setSizeTo: 100) ('size' #r #scale) #- ('show' #- #show) ('hide' #- #hide) #- ('go to front' #- #comeToFront) ('go back %n layers' #- #goBackByLayers: 1) 'sensing' ('touching %m?' #b #touching:) ('touching color %C?' #b #touchingColor:) ('color %C is touching %C?' #b #color:sees:) #- ('ask %s and wait' #s #doAsk 'What''s your name?') ('answer' #r #answer) #- ('mouse x' #r #mouseX) ('mouse y' #r #mouseY) ('mouse down?' #b #mousePressed) #- ('key %k pressed?' #b #keyPressed: 'space') #- ('distance to %m' #r #distanceTo:) #- ('reset timer' #- #timerReset) ('timer' #r #timer) #- ('%a of %m' #r #getAttribute:of:) #- ('loudness' #r #soundLevel) ('loud?' #b #isLoud) #~ ('%H sensor value' #r #sensor: 'slider') ('sensor %h?' #b #sensorPressed: 'button pressed')"""

squeak_obsolete_blockspecs = """'obsolete number blocks' ('abs %n' #r #abs #-) ('sqrt %n' #r #sqrt #-) 'obsolete sound blocks' ('rewind sound %S' #- #rewindSound:) 'obsolete sprite motion blocks' ('point away from edge' #- #turnAwayFromEdge) ('glide x:%n y:%n in %n secs' #t #gotoX:y:duration:elapsed:from: 50 50 1) 'obsolete sprite looks blocks' ('change costume by %n' #- #changeCostumeIndexBy: 1) ('change background by %n' #- #changeBackgroundIndexBy: 1) #- ('change stretch by %n' #- #changeStretchBy:) ('set stretch to %n%' #- #setStretchTo: 100) #- ('say nothing' #- #sayNothing) #- ('change visibility by %n' #- #changeVisibilityBy: -10) ('set visibility to %n%' #- #setVisibilityTo: 100) 'obsolete image effects' ('change color-effect by %n' #- #changeHueShiftBy: 25) ('set color-effect to %n' #- #setHueShiftTo: 0) #- ('change fisheye by %n' #- #changeFisheyeBy: 10) ('set fisheye to %n' #- #setFisheyeTo: 0) #~ ('change whirl by %n' #- #changeWhirlBy: 30) ('set whirl to %n' #- #setWhirlTo: 0) #- ('change pixelate by %n' #- #changePixelateCountBy: 1) ('set pixelate to %n' #- #setPixelateCountTo: 1) #~ ('change mosaic by %n' #- #changeMosaicCountBy: 1) ('set mosaic to %n' #- #setMosaicCountTo: 1) #- ('change brightness-shift by %n' #- #changeBrightnessShiftBy: 10) ('set brightness-shift to %n' #- #setBrightnessShiftTo: 0) #~ ('change saturation-shift by %n' #- #changeSaturationShiftBy: 10) ('set saturation-shift to %n' #- #setSaturationShiftTo: 0) #- ('change pointillize drop by %n' #- #changePointillizeSizeBy: 5) ('set pointillize drop to %n' #- #setPointillizeSizeTo: 0) #~ ('change water ripple by %n' #- #changeWaterRippleBy: 5) ('set water ripple to %n' #- #setWaterRippleTo: 0) #- ('change blur by %n' #- #changeBlurBy: 1) ('set blur to %n' #- #setBlurTo: 0)"""
### End Squeak code



class BlockType:
    """Information about a single type of block.
    Attributes:
        command - the command used in Squeak to run the block. (see Block.name)
        text - text that appears on the block. 
               Contains inserts starting with % signs.
        parts - text, split up into text segments and inserts.
        flag - a single char describing the kind of block.
        category - where this block is found in Scratch's interface.
        defaults - list of default values for block inserts. (see Block.args)
    """
    INSERT_RE = re.compile(r'(%.)')
    
    def __init__(self, command, text, flag='-', category='', defaults=None):
        self.command = command
        self.text = text
        self.flag = flag
        self.category = category
        if defaults is None: defaults = []
        self.defaults = defaults
    
    def copy(self):
        return BlockType(self.command, self.text, self.flag, self.category, self.defaults[:])
    
    @property
    def parts(self):
        return self.INSERT_RE.split(self.text)
    
    def __repr__(self):
        return '<BlockType(%s)>' % self.command
    
    def make_default(self, script=None):
        return Block(script, self.command, *self.defaults[:])


def parse_blockspec(squeak_code):
    parsed = blockspecs.parse(squeak_code)
    categories = parsed.categories
    
    blocks = []
    for category in categories:
        for block in category.blocks:
            if not block.is_block:
                continue
            
            block = BlockType(
                block.command.value,
                block.text,
                block.flag.value,
                category.name, 
                [default.value for default in block.defaults],
            )
            blocks.append(block)
    
    return blocks



blocks = (list(parse_blockspec(squeak_blockspecs)) + 
    list(parse_blockspec(squeak_stage_blockspecs)) + 
    list(parse_blockspec(squeak_sprite_blockspecs)) + 
    list(parse_blockspec(squeak_obsolete_blockspecs)))

blocks += [
    BlockType("readVariable", "%v", "r", "variables"),
    #BlockType("changeVariable", "change %v by %n", category="variables"),
]

blocks_by_cmd = {}
for block in blocks:
    cmd = block.command
    blocks_by_cmd[cmd] = block

blocks_by_text = {}
for block in blocks:
    text = ''.join(part.replace(" ", "") for part in blocks[20].parts
                    if part and not part[0] == "%") # Remove spaces and inserts
    if text not in blocks_by_text:
        # Some blocks have same text
        blocks_by_text[text] = block

block_plugin_inserts = {
    "%b": "<%s>",
    "%n": "(%s)",
    "%d": "(%s v)",
    "%s": "[%s]",
    "%c": "[#%s]",
    "%C": "[#%s]",
        
    "%m": "[%s v]",
    "%a": "[%s v]",
    "%e": "[%s v]",
    "%k": "[%s v]",
        
    "%v": "[%s v]",
    "%L": "[%s v]",
    "%i": "(%s v)",
    "%y": "(%s v)",
        
    "%f": "[%s v]",
        
    "%l": "[%s v]",
    "%g": "[%s v]",
        
    "%S": "[%s v]",
    "%D": "(%s v)",
    "%N": "(%s v)",
    "%I": "(%s v)",
    
    "%h": "[%s v]",
    "%H": "[%s v]",
    "%W": "[%s v]",
}

from scripts import Block

