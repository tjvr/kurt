#!/usr/bin/env python
"""Load MIDI file into Scratch project as note blocks.

Usage:
    import_midi.py file.mid output.sb[2]

Example kurt script."""

from __future__ import division

import sys
import os

import midiparse as midi

# try and find kurt directory
path_to_file = os.path.join(os.getcwd(), __file__)
path_to_lib = os.path.split(os.path.split(path_to_file)[0])[0]
sys.path.insert(0, path_to_lib)
import kurt
from kurt import Block


def load_midi_file(path):
    """Yield (pitch, start_beat, end_beat) for each note in midi file."""

    midi_notes = []
    def register_note(track, channel, pitch, velocity, start, end):
        midi_notes.append((pitch, start, end))
    midi.register_note = register_note

    global m
    m = midi.MidiFile()
    m.open(midi_path)
    m.read()
    m.close()

    for (pitch, start, end) in midi_notes:
        start /= m.ticksPerQuarterNote
        end /= m.ticksPerQuarterNote
        yield (pitch, start, end)

def quantize(beat, n=8):
    return int(beat * n  +  0.5) / n


if len(sys.argv) != 3:
    print __doc__
else:
    (_, midi_path, project_path) = sys.argv

    p = kurt.Project()
    sprite = kurt.Sprite(p, "midi")

    p.sprites.append(sprite)

    # Group notes by start beat
    notes_by_beat = {}
    for (pitch, start, end) in load_midi_file(midi_path):
        start = quantize(start)
        end = quantize(end)
        length = end - start
        if start not in notes_by_beat:
            notes_by_beat[start] = []
        notes_by_beat[start].append((pitch, length))

    # Chain notes into threads
    class Thread:
        def __init__(self):
            self.current = 0
            self.notes = []
        def __repr__(self):
            return "<%r %r>" % (self.current, self.notes)
    threads = []
    offset = None
    for (start, notes) in sorted(notes_by_beat.items()):
        if not offset:
            offset = start
        start -= offset

        for note in sorted(notes):
            (pitch, length) = note
            for thread in threads:
                if thread.current <= start:
                    break
            else:
                thread = Thread()
                threads.append(thread)
            if thread.current < start:
                rest = (-1, start - thread.current)
                thread.notes.append(rest)
            thread.notes.append(note)
            thread.current = start + length

    # Output init script
    sprite.scripts.append(kurt.Script([
        Block("when @greenFlag clicked"),
        Block("broadcast", "play"),
        #Block("set tempo to %s bpm", tempo), # TODO: extract tempo
    ]))

    # Output threads
    for thread in threads:
        s = kurt.Script([
            Block("when I receive", "play"),
        ])
        for (pitch, length) in thread.notes:
            if pitch == -1:
                b = Block("rest for %s beats", length)
            else:
                b = Block("play note %s for %s beats", pitch, length)
            s.append(b)
        sprite.scripts.append(s)

    # Save
    print "Saving"
    p.convert("scratch20")
    p.save(project_path)


