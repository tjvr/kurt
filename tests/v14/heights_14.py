from kurt.scratch14.heights import *



test_block_heights = {
 # reporter
 'heading': 17,
 'xpos': 17,
 'ypos': 17,
 'costumeIndex': 17,
 'scale': 17,
 'backgroundIndex': 17,
 'tempo': 17,
 'volume': 17,
 'readVariable': 17,
 'contentsOfList:': 17,
 'answer': 17,
 'mousePressed': 17,
 'mouseX': 17,
 'mouseY': 17,
 'soundLevel': 17,
 'timer': 17,
 '&': 17,
 '|': 17,
 'not': 17,
 'isLoud': 17,

 # reporter with number/string insert
 '*': 18,
 '<': 18,
 'concatenate:with:': 18,
 'randomFrom:to:': 18,
 'letter:of:': 18,
 'stringLength:': 18,
 '\\\\': 18,
 'rounded': 18,
 'abs': 18,
 'sqrt': 18,
 '+': 18,
 '-': 18,
 '/': 18,
 '=': 18,
 '>': 18,

 # reporter with menu
 'getAttribute:of:': 19,
 'computeFunction:of:': 19,
 'touching:': 19,
 'sensor:': 19,
 'sensorPressed:': 19,
 'getLine:ofList:': 19,
 'lineCountOfList:': 19,
 'list:contains:': 19,
 'distanceTo:': 19,
 'keyPressed:': 19,

 # stack
 'bounceOffEdge': 24,
 'changeSizeBy:': 24,
 'changeXposBy:': 24,
 'changeYposBy:': 24,
 'filterReset': 24,
 'forward:': 24,
 'glideSecs:toX:y:elapsed:from:': 24,
 'gotoX:y:': 24,
 'heading:': 24,
 'hide': 24,
 'nextCostume': 24,
 'say:': 24,
 'say:duration:elapsed:from:': 24,
 'show': 24,
 'think:': 24,
 'think:duration:elapsed:from:': 24,
 'turnLeft:': 24,
 'turnRight:': 24,
 'xpos:': 24,
 'ypos:': 24,
 'doWaitUntil': 24,
 'noteOn:duration:elapsed:from:': 24,
 'comeToFront': 24,
 'goBackByLayers:': 24,
 'stopAllSounds': 24,
 'drum:duration:elapsed:from:': 24,
 'rest:elapsed:from:': 24,
 'midiInstrument:': 24,
 'changeVolumeBy:': 24,
 'setVolumeTo:': 24,
 'changeTempoBy:': 24,
 'setTempoTo:': 24,
 'stampCostume': 24,
 'putPenDown': 24,
 'putPenUp': 24,
 'clearPenTrails': 24,
 'changePenHueBy:': 24,
 'setPenHueTo:': 24,
 'changePenShadeBy:': 24,
 'setPenShadeTo:': 24,
 'changePenSizeBy:': 24,
 'penSize:': 24,
 'wait:elapsed:from:': 24,
 'doAsk': 24,
 'timerReset': 24,
 'nextBackground': 24,
 'motorOnFor:elapsed:from:': 24,
 'allMotorsOn': 24,
 'allMotorsOff': 24,
 'startMotorPower:': 24,

 # stack with menu
 'broadcast:': 25, # unless empty in which case 24
 'doBroadcastAndWait': 25, # unless empty in which case 24
 'changeGraphicEffect:by:': 25,
 'setGraphicEffect:to:': 25,
 'gotoSpriteOrMouse:': 25,
 'pointTowards:': 25,
 'lookLike:': 25,
 'setVar:to:': 25,
 'playSound:': 25,
 'doPlaySoundAndWait': 25,
 'changeVar:by:': 25,
 'showVariable:': 25,
 'hideVariable:': 25,
 'append:toList:': 25,
 'deleteLine:ofList:': 25,
 'insert:at:ofList:': 25,
 'setLine:ofList:to:': 25,
 'showBackground:': 25,
 'setMotorDirection:': 25,
 
 # hats
 'KeyEventHatMorph': 41,
 'whenGreenFlag': 43,
 'whenClicked': 38, # MouseClickEventHatMorph
 'whenIReceive': 39,

 # cap
 'doReturn': 19,
 'stopAll': 22,

 # C cap
 'doForever': 42,
 
 # C cap with bool
 'doForeverIf': 43,

 # C
 'doUntil': 47,
 'doIf': 47,

 # C with number
 'doRepeat': 48,

 # E
 'doIfElse': 75,
}

for command in test_block_heights:
    block = kurt.Block(command)
    args = []
    for insert in block.type.inserts:
        arg = insert.default
        if insert.shape == 'readonly-menu':
            if not arg:
                arg = "cheese"
        args.append(arg)
    block.args = args
    assert block_height(block) == test_block_heights[command]

assert block_height(kurt.Block("if", None, [kurt.Block("lookLike:")])) == 57
assert block_height(kurt.Block("forever", [kurt.Block("lookLike:")])) == 52
assert block_height(kurt.Block("doUntil", None, [kurt.Block("lookLike:")])) == 57
assert block_height(kurt.Block('doIfElse', None, [kurt.Block('say:', 'Hello!')]
    * 2, [kurt.Block('say:', 'Hello!')] * 2)) == 133
assert block_height(kurt.Block("if", kurt.Block("<"))) == 52
assert block_height(kurt.Block("forever if", kurt.Block("<"))) == 48
assert block_height(kurt.Block("say", kurt.Block("join", 3, 4))) == 28
assert block_height(kurt.Block("broadcast", kurt.Block("join", 3, 4))) == 28

