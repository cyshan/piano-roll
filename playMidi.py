import time
import fluidsynth
from midiParse import Midi

def startFluidsynth():
    fs = fluidsynth.Synth()
    fs.start()
    sfid = fs.sfload("acoustic_grand_piano_ydp_20080910.sf2")
    fs.program_select(0, sfid, 0, 0)
    return fs

class PlayMidi(object):
    def __init__(self,midiFile):
        #given a midi file name, plays the midi file
        midi=Midi(midiFile)
        self.tempoTrack=midi.tempoTrack
        self.dataTrack=midi.dataTrack
        self.ticksPerQuarterNote=midi.ticksPerQuarterNote
        self.format=midi.format
        self.noteDuplicity=1
        self.fs=startFluidsynth()
        
    def playMidi(self):
        if self.format==0:
            self.playFormat0Midi()
        elif self.format==1:
            self.playFormat1Midi()

    def nextEvent(self):
        #from tracks, find next event, and executes that event
        (tempoTrack,dataTrack)=(self.tempoTrack,self.dataTrack)
        if tempoTrack==[] and dataTrack==[]:
            return False #when tracks are both empty, midi is done playing
        if dataTrack==[] or (tempoTrack!=[] and tempoTrack[0]<=dataTrack[0]):
            #tempo events take precedence
            deltaTime=tempoTrack.pop(0)
            event=tempoTrack.pop(0)
            if dataTrack!=[]: #time passes for the other track as well
                dataTrack[0]-=deltaTime
        elif tempoTrack==[] or dataTrack[0]<tempoTrack[0]:
            deltaTime=dataTrack.pop(0)
            event=dataTrack.pop(0)
            if tempoTrack!=[]:
                tempoTrack[0]-=deltaTime
        secondsPerTick=float(self.tempo)/self.ticksPerQuarterNote
        sleepTime=deltaTime*secondsPerTick
        time.sleep(sleepTime)
        self.runEvent(event)
        (self.tempoTrack,self.dataTrack)=(tempoTrack,dataTrack)

    def combineTrackEvent(self,ticksPerBeat):
        #takes two midi tracks finds next event, and adds to event list
        (tempoTrack,dataTrack)=(self.tempoTrack,self.dataTrack)
        if tempoTrack==[] and dataTrack==[]:
            return False #when tracks are both empty, midi is done playing
        if dataTrack==[] or (tempoTrack!=[] and tempoTrack[0]<=dataTrack[0]):
            #tempo events take precedence
            deltaTime=tempoTrack.pop(0)
            event=tempoTrack.pop(0)
            if dataTrack!=[]: #time passes for the other track as well
                dataTrack[0]-=deltaTime
        elif tempoTrack==[] or dataTrack[0]<tempoTrack[0]:
            deltaTime=dataTrack.pop(0)
            event=dataTrack.pop(0)
            if tempoTrack!=[]:
                tempoTrack[0]-=deltaTime
        tickRatio=float(ticksPerBeat)/self.ticksPerQuarterNote
        #adapt ticks per beat for piano roll
        deltaTime=int(round(tickRatio*deltaTime))
        self.pianoRollTrack+=[deltaTime]
        self.pianoRollTrack+=[event]

    def combineTracks(self,ticksPerBeat):
        #takes two midi tracks, combines them, and turns them into format
        #that piano roll can read
        self.pianoRollTrack=[]
        while True:
            if self.combineTrackEvent(ticksPerBeat)==False:
                break
        return self.pianoRollTrack

    def runEvent(self,event):
        #executes the event that comes up
        fs=self.fs
        eventType=event[0]
        print event
        if eventType=='tempo': #tempo change
            (eventType,tempo)=event
            self.tempo=tempo #tempo is stored in rest of event tuple
        elif eventType=='on': #note on event
            (eventType,note,velocity)=event
            for noteTimes in xrange(self.noteDuplicity):
                fs.noteon(0, note, velocity)
                #play actual note multiple times at same time to increase
                #volume of notebecause fluidsynth volume is low
        elif eventType=='off':
            (eventType,note)=event
            for noteTimes in xrange(self.noteDuplicity):
                fs.noteoff(0, note)

    def playFormat1Midi(self):
        #plays a format 1 or 0 midi file
        self.tempo=0 #placeholder for tempo (seconds per quarter note)
        while True:
            if self.nextEvent()==False:
                break
            
###############################################################################
##############################################################################3
def playScale():
    x=60
    y=60
    fs=startFluidsynth()
    while True:
        x=int(round(y))
        fs.noteon(0, x, 127)
        time.sleep(0.3)
        fs.noteoff(0,x)
        y+=1.75
        if x>71:
            break
        
#playScale()
#start=time.time()   
#PlayMidi('this-is-berk.mid')
#end=time.time()
#print end-start
