from staticGraphics import SequencerStaticGraphics
from Tkinter import *
from playMidi import PlayMidi
from midiParse import Midi
from createMidi import CreateMidi
import copy
import time
import fluidsynth
import math
import tkFileDialog
import tkMessageBox

class PianoRoll(SequencerStaticGraphics):
    #displays the piano roll screen
    def __init__(self):
        super(PianoRoll,self).__init__()
        self.pianoRollY0=self.dynY0+40 #scroll bar, measure # above piano roll
        self.keyHeight=15
        self.keyWidth=80
        #y coord of lowest key on piano (C-1) and all keys display above that
        #initial position starts G2 at bottom of screen
        self.beatsPerMeasure=4
        self.measureLineWidth=3
        self.beatLineWidth=2
        self.divisionLineWidth=1
        self.ticksPerBeat=24 #initial conditions
        self.noteLength=6 #initial note length (in ticks)
        #time in ticks of rightmost point of piano roll
        self.maxVel=127 #notes are by default at max velocity
        self.noteColor='powder blue'
        self.clickedNote=None
        self.noteLengthSliderHitbox=10
        self.noteLengthChange=None
        self.measureNumberBarHeight=20
        self.bufferTime=288 #time after last note stored
        self.endLengthChangeHitbox=5 #width in pixels of end hitboxes
        self.sliderChangeLeft=False
        self.sliderChangeRight=False
        self.sliderShift=False
        (self.minTempo,self.maxTempo)=(20,400)
        
    def leftMousePressed(self,event):
        (x,y)=(event.x,event.y)
        (self.x,self.y)=(x,y)
        (self.clickX,self.clickY)=(self.x,self.y)
        self.noteLengthChange=None
        self.sliderChangeLeft=False
        self.sliderChangeRight=False
        self.sliderShift=False #resets states on mouseclick
        self.clickedNote=None
        if self.helpScreen==True: #click closes help screen
            self.helpScreen=False
        else:
            if (x>=self.keyWidth and x<=self.width and y>=self.pianoRollY0 and
                y<=self.height): #clicked inside piano roll entry space
                if self.tempoScreen==True:
                    self.tempoScreenClick()
                else:
                    self.pianoRollClick()
            elif (y>self.dynY0 and y<self.pianoRollY0-
                  self.measureNumberBarHeight): #mouse clicked on measure slider
                self.measureSliderClick()
            else: #click on control space
                self.controlSpaceClick()

    def rightMousePressed(self,event):
        if self.tempoScreen==False and self.helpScreen==False:
            #does not do anything on tempo or help screen
            (x,y)=(event.x,event.y)
            (self.x,self.y)=(x,y)
            if (x>=self.keyWidth and x<=self.width and y>=self.pianoRollY0 and
                y<=self.height): #clicked inside piano roll entry space
                self.pianoRollRightClick()

    def rightMouseMotion(self,event):
        #dragging right mouse click across screen deletes all notes it contacts
        if self.tempoScreen==False and self.helpScreen==False:
            #does not do anything on tempo or help screen
            (self.x,self.y)=(event.x,event.y)
            if self.noteClicked(delete=True):
                self.redrawAll()

    def leftMouseMotion(self,event):
        if self.helpScreen==False: #does not do anything on help screen
            (x,y)=(event.x,event.y)
            (self.x,self.y)=(x,y)
            if self.noteLengthChange!=None and self.tempoScreen==False:
                #if a lenght change hitbox clicked, motion 
                #changes length of note (also must not be on tempo screen)
                self.changeNoteLength()
            elif (self.sliderChangeLeft or self.sliderChangeRight or
                  self.sliderShift):
                self.sliderMove()
                self.redrawAll()
            elif self.clickedNote!=None and self.tempoScreen==False:
                #if a note was clicked(or created)(must not be on tempo screen)
                if (x>=self.keyWidth and x<=self.width and y>=self.pianoRollY0
                    and y<=self.height): #clicked inside piano roll entry space
                    if self.movedToDifferentNote()==True:
                        #if mouse moved over to different note
                        self.switchNote()
                        self.redrawAll()

    def changeNoteLength(self):
        #changes the length of the note in self.noteLengthChange
        (note, time)=self.clickPositionNote()
        (note,timeOn,timeOff)=self.noteLengthChange
        ticksPerDivision=self.ticksPerBeat/self.divisionsPerBeat
        divisionOff=float(timeOff)/ticksPerDivision
        divisionOn=float(timeOn)/ticksPerDivision
        division=int(round(time*self.divisionsPerBeat/self.ticksPerBeat))
        noteLength=division-divisionOn
        #nth division on grid from left
        if division!=divisionOff and noteLength>0: #can't have notelength<=0
            self.deleteNote((note,timeOn,timeOff))
            newTimeOff=division*ticksPerDivision
            self.notes+=[(note,timeOn,newTimeOff)]
            self.noteLengthChange=(note,timeOn,newTimeOff)
            self.noteLength=newTimeOff-timeOn #changes default note length
            self.redrawAll()

    def clickPositionNote(self):
        #returns the clicked note and clicked time (in ticks) of self.x, self.y
        (x,y)=(self.x,self.y)
        noteClicked=(self.keyPosition-y)/self.keyHeight
        tickWidth=self.measureWidth/self.beatsPerMeasure/self.ticksPerBeat
        timeClicked=(x-self.keyWidth)/tickWidth+self.timePosition
        #gives the time of the position clicked in terms of ticks
        return (noteClicked,timeClicked)
        
    def movedToDifferentNote(self):
        #checks if mouse moved off of original note
        (note, time)=self.clickPositionNote()
        (noteClicked,timeOn,timeOff)=self.clickedNote
        if note==noteClicked:
            if time>timeOn and time<timeOff:
                return False
        else: return True

    def switchNote(self):
        #swiches note as mouse moved over to a different note
        note=self.clickedNote
        self.deleteNote(note)
        self.fs.noteoff(0,self.clickedNote[0])
        self.newNote()
        self.fs.noteon(0,self.clickedNote[0],self.maxVel)

    def onKeyPressed(self,event):
        if self.helpScreen==False: #does nothing on help screen
            if event.keysym=='space':
                self.playMusic()

    def deleteNote(self,deleteNote):
        #deletes a note from the note list
        for note in self.notes:
            if note==deleteNote:
                (note,timeOn,timeOff)=deleteNote
                self.notes.remove((note,timeOn,timeOff))

    def mouseWheel(self, event):
        self.deltaMouseWheel=event.delta/120
        #for some reason, mousewheel events are always multiples of 120
        if self.helpScreen==False: #does nothing on help screen
            if self.tempoScreen==False:
                self.changePianoRollVerticalPosition()
                self.keyRange()
            else: #tempoScreen is on
                self.changeTempoScreenVerticalPosition()
            self.redrawAll()

    def changePianoRollVerticalPosition(self):
        #scrolls the piano roll up and down
        deltaY=self.deltaMouseWheel
        noteChange=3 #goes up or down 3 notes for every mousewheel change
        deltaY=noteChange*self.keyHeight*deltaY
        minY=self.height #bottom of piano cannot be lower than bottom of screen
        maxY=self.pianoRollY0+self.keyHeight*len(self.noteList)
        #top of piano roll cannot go off scale
        self.keyPosition+=deltaY
        if self.keyPosition<minY:
            self.keyPosition=minY
        elif self.keyPosition>maxY:
            self.keyPosition=maxY

    def changeTempoScreenVerticalPosition(self):
        #scrolls the tempo screen up and down
        deltaY=self.deltaMouseWheel
        tempoChange=3 #goes up or down 3 bpm
        deltaY=tempoChange*self.keyHeight*deltaY
        minY=self.height+self.keyHeight*self.minTempo
        #bottom of piano cannot be lower than bottom of screen
        maxY=self.pianoRollY0+self.keyHeight*self.maxTempo
        #top of piano roll cannot go off scale
        self.tempoPosition+=deltaY
        if self.tempoPosition<minY:
            self.tempoPosition=minY
        elif self.tempoPosition>maxY:
            self.tempoPosition=maxY
    
    def leftMouseReleased(self,event):
        if self.tempoScreen==False and self.helpScreen==False:
            #does not do anything on tempo or help screen
            if self.clickedNote!=None:
                self.fs.noteoff(0,self.clickedNote[0])
            #stop playing note when mouse released

    def pianoRollRightClick(self):
        #right click on piano roll deletes the note that was there
        if self.noteClicked(delete=True): #deletes note if one was clicked
            return

    def controlSpaceClick(self):
        #handles clicks that are not on piano roll
        (x,y)=(self.x,self.y)
        buttonClicked=None
        for button in self.buttons: #goes though every button, check if clicked
            (x0,y0,x1,y1)=self.buttons[button]
            if x>x0 and x<x1 and y>y0 and y<y1:
                buttonClicked=button
        if buttonClicked!=None:
            if buttonClicked=='Play': self.playMusic()
            elif buttonClicked=='New': self.newPianoRoll()
            elif buttonClicked=='Import': self.importMidiFile()
            elif buttonClicked=='Export': self.exportMidiFile()
            elif buttonClicked=='Duplet':
                self.tripletDivisions=False
                self.changeDivisionsPerBeat()
            elif buttonClicked=='Triplet':
                self.tripletDivisions=True
                self.changeDivisionsPerBeat()
            elif buttonClicked=='Tempo': self.tempoScreen=True
            elif buttonClicked=='Piano Roll': self.tempoScreen=False
            elif buttonClicked=='Help': self.helpScreen=True

    def newPianoRoll(self):
        #create new piano roll midi
        message = "Do you want to save as MIDI file?"
        title = "Piano Roll"
        response = tkMessageBox.askquestion(title, message)
        if response=='yes':
            fileName = tkFileDialog.asksaveasfilename(initialfile=['New.mid'])
            if fileName!='': #if there is a file name
                CreateMidi(fileName,timingTrack,self.ticksPerBeat)
        self.initAnimation()

    def importMidiFile(self):
        #takes in midi file through dialog, and displays notes on piano roll
        self.initAnimation()
        self.midiFile=tkFileDialog.askopenfilename(filetypes=[(
                                                    'all files','.mid')])
        slashI=-1 #resets the parameters on piano roll
        for i in xrange(len(self.midiFile)-1,-1,-1):
            if self.midiFile[i]=='/': #finds i of last slash
                slashI=i
                break
        self.fileName=self.midiFile[slashI+1:] #for rewriting name
        self.midi=Midi(self.midiFile)
        playMidi=PlayMidi(self.midiFile)
        self.noteTimingList=playMidi.combineTracks(self.ticksPerBeat)
        self.convertTimingTrackToNoteList()
        self.correctSliderPosition() #new notes, change slider position

    def exportMidiFile(self):
        #takes the current music on piano roll and exports it as a midi file
        self.createTimingTrack()
        timingTrack=self.noteTimingList
        if self.fileName!=None:
            fileName = tkFileDialog.asksaveasfilename(initialfile=
                                                      [self.fileName])
        else:fileName = tkFileDialog.asksaveasfilename(initialfile=['New.mid'])
        if fileName!='': #if there is a file name
            CreateMidi(fileName,timingTrack,self.ticksPerBeat)
    
    def playMusic(self):
        #plays the music shown on the piano roll
        if self.midiFile==None:
            self.createTimingTrack()
            self.playNoteTimingTrack()
        else:
            playMidi=PlayMidi(self.midiFile)
            self.noteTimingList=playMidi.combineTracks(self.ticksPerBeat)
            self.playNoteTimingTrack()

    def createTimingTrack(self):
        #turns list of notes into a timing track
        #that is more readable for audio purposes
        self.noteTimingList=[]
        for note in self.notes:
            if note[0]=='tempo':
                (event,time,tempo)=note
                self.addTempoToTimingList(time,tempo)
            else:
                self.addNoteToTimingList(*note)

    def addNoteToTimingList(self,note,timeOn,timeOff):
        #adds the note to a timing list
        timingList=self.noteTimingList
        timingList=self.addToTimingList(timeOn,('on',note,self.maxVel),
                                        timingList)
        timingList=self.addToTimingList(timeOff,('off',note,0),timingList)
        self.noteTimingList=timingList

    def addTempoToTimingList(self,time,tempo):
        #adds a tempo event to the timing list
        timingList=self.noteTimingList
        timingList=self.addToTimingList(time,('tempo',tempo),timingList)
        self.noteTimingList=timingList

    @staticmethod
    def addToTimingList(time,event,timingList):
        #inserts an event into timing list and returns the timing list
        if timingList==[]:#if timing list is empty just add event
            timingList=([time]+[event])
        elif time<=timingList[0]: #if event is before all others
            timingList=([time]+[event]+[timingList[0]-time]
                        +timingList[1:])
        else: #event occurs after others
            totalDelay=0 #running count of delays up to a point in the list
            for delayI in xrange(0,len(timingList),2):
                totalDelay+=timingList[delayI]
                if totalDelay>time: #once delay adds to more than time
                    previousDelay=totalDelay-timingList[delayI]
                    timingList=(timingList[:delayI]+
                        [time-previousDelay]+[event]
                        +[totalDelay-time]+timingList[delayI+1:])
                    break
            if totalDelay<=time: #the delay never reached the time
                timingList+=([time-totalDelay]+[event])
        return timingList

    def playNoteTimingTrack(self):
        #plays the note timing track
        noteTimingTrack=copy.deepcopy(self.noteTimingList)
        secPerMinute=60.0
        beatsPerSec=self.tempo/secPerMinute
        secondsPerTick=1.0/(self.ticksPerBeat*beatsPerSec)
        #note track will now be played note by note
        while noteTimingTrack!=[]:
            #until track is empty or stop button is pressed
            tickDelay=noteTimingTrack.pop(0)
            beatsPerSec=self.tempo/secPerMinute
            secondsPerTick=1.0/(self.ticksPerBeat*beatsPerSec)
            timeDelay=secondsPerTick*tickDelay
            time.sleep(timeDelay)
            event=noteTimingTrack.pop(0)
            self.runEvent(event)

    def convertTimingTrackToNoteList(self):
        #takes in a timing track of delays and events, and creates note list
        notes=[] #format = list of -- (note,timeOn,timeOff)
        #tempo events not yet supported
        timingTrack=self.noteTimingList
        noteOnDict=dict() #dictionary of notes and their on times
        #to find match with their off times
        totalTicks=0 #ticks that have so far elapsed in timing track
        while timingTrack!=[]:
            tickDelay=timingTrack.pop(0)
            totalTicks+=tickDelay
            event=timingTrack.pop(0)
            eventType=event[0]
            if eventType=='on': #note on event
                (eventType,note,velocity)=event
                noteOnDict[note]=totalTicks
            elif eventType=='off': #note off event
                (eventType,note)=event
                timeOff=totalTicks
                timeOn=noteOnDict[note]
                notes+=[(note,timeOn,timeOff)]
            elif eventType=='tempo': #tempo event
                (eventType,tempo)=event
                time=totalTicks
                notes+=[('tempo',time,tempo)]
        self.notes=notes

    def runEvent(self,event):
        #executes the event that comes up
        fs=self.fs
        eventType=event[0]
        if eventType=='tempo': #tempo change
            (eventType,tempo)=event #tempo is seconds per quarter note
            tempo=60/tempo #tempo is quarter notes per minute
            self.tempo=tempo #tempo is stored in rest of event tuple
        elif eventType=='on': #note on event
            (eventType,note,velocity)=event
            fs.noteon(0, note, velocity)
        elif eventType=='off':
            if len(event)==2: #sometimes off event has no velocity
                (eventType,note)=event
            else:(eventType,note,velocity)=event
            fs.noteoff(0, note)

    def tempoScreenClick(self):
        #handles click on tempo screen
        self.midiFile=None #midi file changed, no longer displaying original
        tempo=(self.tempoPosition-self.y)/self.keyHeight+1 #tempo in bpm
        secsPerMinute=60.0
        tempo=secsPerMinute/tempo
        tickWidth=(self.measureWidth/self.beatsPerMeasure/self.ticksPerBeat)
        ticksPerDivision=self.ticksPerBeat/self.divisionsPerBeat
        divisionNumber=int(((self.x-self.keyWidth)/tickWidth+self.timePosition)/
                        ticksPerDivision)
        #the amount of divisions that exist before clicked place
        ticksPerDivision=int(round(self.ticksPerBeat/self.divisionsPerBeat))
        time=divisionNumber*ticksPerDivision #number of ticks when note on
        self.notes+=[('tempo', time,tempo)]

    def pianoRollClick(self):
        #handles click on piano roll
        if self.noteClicked()==False:
            self.newNote()
        elif self.clickedInNoteLengthChange():
            return
        else:
            self.fs.noteon(0,self.clickedNote[0],self.maxVel)

    def measureSliderClick(self):
        #handles click inside measure slider bar
        #four parts to slider:left end changer,right end changer,
        #middle shift, and the part not on the slider
        maxTimeOff=self.lastTimeOff()
        totalTicks=maxTimeOff+self.bufferTime
        self.maxTime=maxTime=max(self.maxTime,totalTicks)
        self.sliderLeftEnd=self.timePosition*self.width/maxTime
        self.sliderRightEnd=self.timeEnd*self.width/maxTime
        x=self.x
        if x>self.sliderLeftEnd and x<self.sliderRightEnd: #on the slider
            (self.clickX)=(self.x)
            if x<self.sliderLeftEnd+self.endLengthChangeHitbox: #in the hitboxes
                self.sliderChangeLeft=True
            elif x>self.sliderRightEnd-self.endLengthChangeHitbox:
                self.sliderChangeRight=True #else just move slider
            else: self.sliderShift=True
        else: #not on slider
            self.moveSliderToPosition()

    def moveSliderToPosition(self):
        #moves slider to position clicked
        maxTime=self.maxTime
        sliderWidth=self.sliderRightEnd-self.sliderLeftEnd
        cx=self.x
        sliderLeftEnd=cx-0.5*sliderWidth
        sliderRightEnd=cx+0.5*sliderWidth
        if sliderRightEnd>self.width:
            sliderRightEnd=self.width
            sliderLeftEnd=sliderRightEnd-sliderWidth
        elif sliderLeftEnd<0: #keeps slider within range
            sliderLeftEnd=0
            sliderRightEnd=sliderWidth
        self.sliderShift=True #able to shift slider afterwards
        self.clickX=self.x
        self.timePosition=sliderLeftEnd*maxTime/self.width
        self.timeEnd=sliderRightEnd*maxTime/self.width

    def correctSliderPosition(self):
        #slider position may change after every new note is added
        #so this corrects the slider position
        maxTimeOff=self.lastTimeOff()
        totalTicks=maxTimeOff+self.bufferTime
        self.maxTime=480 #minimum max time on slider
        self.maxTime=maxTime=max(self.maxTime,totalTicks)
        if self.timePosition>self.maxTime: #re-adjusted to more than max time
            self.timePosition=0
        if self.timeEnd>self.maxTime:
            self.timeEnd=self.maxTime #make sure slider doesn't go off bar

    def sliderMove(self):
        #handles mouse motion after slider has been clicked
        maxTime=self.maxTime
        minSliderLength=10
        (sliderLeftEnd,sliderRightEnd)=(self.sliderLeftEnd,self.sliderRightEnd)
        sliderWidth=self.sliderRightEnd-self.sliderLeftEnd
        if self.sliderChangeLeft==True:
            sliderLeftEnd=self.x
            if sliderLeftEnd>sliderRightEnd-minSliderLength:
                sliderLeftEnd=sliderRightEnd-minSliderLength
        elif self.sliderChangeRight==True:
            sliderRightEnd=self.x
            if sliderRightEnd<sliderLeftEnd+minSliderLength:
                sliderRightEnd=sliderLeftEnd+minSliderLength
        else: #slider bar shift (clicked in middle)
            dx=self.x-self.clickX
            sliderLeftEnd+=dx
            sliderRightEnd+=dx
            if sliderRightEnd>self.width:
                sliderRightEnd=self.width
                sliderLeftEnd=sliderRightEnd-sliderWidth
            elif sliderLeftEnd<0: #keeps slider within range
                sliderLeftEnd=0
                sliderRightEnd=sliderWidth
        self.timePosition=sliderLeftEnd*maxTime/self.width
        self.timeEnd=sliderRightEnd*maxTime/self.width
        self.changeMeasureSpecs()

    def changeMeasureSpecs(self):
        #changes measure width, division num, etc. to fit with new
        #time position and time end
        measureWidth=self.measureWidth
        beatsPerMeasure=self.beatsPerMeasure
        divisionsPerBeat=self.divisionsPerBeat
        ticksPerBeat=self.ticksPerBeat #initial conditions
        ticksOnScreen=self.timeEnd-self.timePosition
        beatsOnScreen=float(ticksOnScreen)/ticksPerBeat
        measuresOnScreen=beatsOnScreen/beatsPerMeasure
        pianoRollWidth=self.width-self.keyWidth
        self.measureWidth=measureWidth=pianoRollWidth/measuresOnScreen
        #redefine measure width based on start and stop times
        self.changeDivisionsPerBeat()

    def changeDivisionsPerBeat(self):
        #changes divisions per beat to fit with measure width
        #so that divisions not too cramped or spread out
        if self.tripletDivisions==False:
            divisionsPerBeat=2
            maxDivisionsPerBeat=8
        else: #triplets
            divisionsPerBeat=3
            maxDivisionsPerBeat=24
        divWidth=self.measureWidth/self.beatsPerMeasure/divisionsPerBeat
        (minDivWidth,maxDivWidth)=(20,40) 
        while divWidth>maxDivWidth:
            divWidth/=2
            divisionsPerBeat*=2
            if divisionsPerBeat>maxDivisionsPerBeat:
                divisionsPerBeat=maxDivisionsPerBeat
                break
        while divWidth<minDivWidth:
            divWidth*=2
            divisionsPerBeat=divisionsPerBeat/2.0
        self.divisionsPerBeat=divisionsPerBeat

    def lastTimeOff(self):
        #returns the time in ticks at the end of the last note
        maxTimeOff=0
        for note in self.notes:
            (note,timeOn,timeOff)=note
            if timeOff>maxTimeOff:
                maxTimeOff=timeOff
        return maxTimeOff

    def clickedInNoteLengthChange(self):
        #test if clicked into hitbox to change the note length
        #if clicked in hitbox, set self.noteLengthChange to note
        (x,y)=(self.x,self.y)
        (noteClicked,time)=self.clickPositionNote()
        tickWidth=(self.measureWidth/self.beatsPerMeasure/
                           self.ticksPerBeat)
        for note in self.notes:
            (note,timeOn,timeOff)=note
            if note==noteClicked:
                #note must be the same
                noteOffX=(timeOff-self.timePosition)*tickWidth+self.keyWidth
                #calculates the x position of timeOff in terms of pixels
                noteOffHitboxLeft=noteOffX-self.noteLengthSliderHitbox
                #defines position of left end of hitbox
                if x>noteOffHitboxLeft and x<noteOffX:
                    #x is within hitbox
                    self.noteLengthChange=(note,timeOn,timeOff)

    def noteClicked(self,delete=False):
        #checks all the notes to see if any were clicked
        (noteClicked, timeClicked)=self.clickPositionNote()
        #gives the time of the position clicked in terms of ticks
        for note in self.notes:
            (note, timeOn,timeOff)=note
            if noteClicked==note and timeClicked>timeOn and timeClicked<timeOff:
                if delete==True:
                    self.notes.remove((note, timeOn,timeOff))
                self.clickedNote=(note,timeOn,timeOff)
                self.noteLength=timeOff-timeOn
                return True
        return False #none of the notes were clicked

    def newNote(self):
        #adds a new note to the piano roll
        self.midiFile=None #midi file changed, no longer displaying original
        note=(self.keyPosition-self.y)/self.keyHeight #note num as in midi spec
        tickWidth=(self.measureWidth/self.beatsPerMeasure/self.ticksPerBeat)
        ticksPerDivision=self.ticksPerBeat/self.divisionsPerBeat
        divisionNumber=int(((self.x-self.keyWidth)/tickWidth+self.timePosition)/
                        ticksPerDivision)
        #the amount of divisions that exist before clicked place
        ticksPerDivision=int(round(self.ticksPerBeat/self.divisionsPerBeat))
        timeOn=divisionNumber*ticksPerDivision #number of ticks when note on
        timeOff=timeOn+self.noteLength
        self.notes+=[(note,timeOn,timeOff)]
        self.fs.noteon(0, note, self.maxVel)
        self.clickedNote=(note,timeOn,timeOff)
        self.correctSliderPosition()

    def createNoteList(self):
        #creates a list of the key names, in the order of low to high
        #such that index of list is the midi value for that note
        notes=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
        noteList=[]
        for octave in xrange(-1,10): #in midispec, notes range from C-1 to G9
            if octave ==9:
                for note in notes[0:8]: #only goes up to G9 (not B9)
                    noteList+=[note+str(octave)]
            else:
                for note in notes:
                   noteList+=[note+str(octave)]
        self.noteList=noteList
        
    def drawBackground(self):
        #draws background to gui
        self.canvas.create_rectangle(0,0,self.width,self.height,
                                     fill=self.backgroundColor,width=0)

    def keyRange(self):
        #finds the range of keys that get displayed on screen
        keyHeight=self.keyHeight
        self.lowestKey=int((self.keyPosition-self.height)/keyHeight)
        self.highestKey=int((self.keyPosition-self.pianoRollY0)/keyHeight)+1
        
    def drawKeys(self):
        #draws the piano keys that are displayed on screen
        (noteList,keyHeight)=(self.noteList,self.keyHeight)
        (lowestKey,highestKey)=(self.lowestKey,self.highestKey)
        for key in xrange(lowestKey, highestKey):
            y0=self.keyPosition-(key+1)*keyHeight
            y1=self.keyPosition-(key)*keyHeight
            if y1>self.pianoRollY0: #key must be on the dynamic region of screen
                note=noteList[key]
                if note[1]=='#': #black key vs white key
                    keyColor='black'
                else: keyColor='white'
                if y0<self.pianoRollY0:
                    #if key extends past screen, cut off part key
                    y0=self.pianoRollY0
                x0=0
                x1=self.keyWidth
                self.canvas.create_rectangle(x0,y0,x1,y1,fill=keyColor)
                (cx,cy)=((x0+x1)/2,(y0+y1)/2)
                textColor='white' if keyColor=='black' else 'black'
                #text color opposite of key color for contrast
                self.canvas.create_text(cx,cy,text=note, fill=textColor,
                                        font='arial 9')

    def drawHorizontalLines(self):
        #draws the horizontal lines for the grid
        (lowestKey,highestKey)=(self.lowestKey,self.highestKey)
        for key in xrange(lowestKey, highestKey):
            y=self.keyPosition-(key)*self.keyHeight
            if y>self.pianoRollY0: #y must by in the box
                self.canvas.create_line(self.keyWidth,y,self.width,y,
                                    fill='slate gray')
                
    def drawVerticalLines(self):
        #draws the vertical lines for the grid
        measureWidth=self.measureWidth
        beatWidth=measureWidth/float(self.beatsPerMeasure)
        divisionWidth=beatWidth/self.divisionsPerBeat
        divisionsPerMeasure=self.divisionsPerBeat*self.beatsPerMeasure
        ticksPerDivision=self.ticksPerBeat/self.divisionsPerBeat
        tickWidth=(beatWidth/self.ticksPerBeat)
        lineX=self.keyWidth+(-self.timePosition%ticksPerDivision)*tickWidth
        divisionNum=math.ceil(float(self.timePosition)/ticksPerDivision)
        while lineX<self.width: #while line is on the screen
            if divisionNum%divisionsPerMeasure==0: #line is a measure line
                self.canvas.create_line(lineX,self.pianoRollY0,lineX,self.height
                        ,width=self.measureLineWidth, fill='light slate gray')
            elif divisionNum%self.divisionsPerBeat==0: #beat division
                self.canvas.create_line(lineX,self.pianoRollY0,lineX,self.height
                         ,width=self.beatLineWidth, fill='light slate gray')
            else:
                self.canvas.create_line(lineX,self.pianoRollY0,lineX,self.height
                     ,width=self.divisionLineWidth, fill='light slate gray')
            lineX+=divisionWidth
            divisionNum+=1
     
    def drawGrid(self):
        #draws grid for the notes
        self.drawHorizontalLines()
        self.drawVerticalLines()

    def drawNotes(self):
        #draws notes entered into piano roll
        rightLineWidth=self.noteLengthSliderHitbox
        #line to seperate hitbox for length change from rest of note
        beatWidth=self.measureWidth/float(self.beatsPerMeasure)
        divisionWidth=beatWidth/self.divisionsPerBeat
        ticksPerDivision=self.ticksPerBeat/self.divisionsPerBeat
        tickWidth=divisionWidth/ticksPerDivision
        for note in self.notes:
            if note[0]!='tempo': #not a tempo event
                (note,timeOn, timeOff)=note
                y1=self.keyPosition-(note)*self.keyHeight
                if y1>self.pianoRollY0:
                    x1=self.keyWidth+tickWidth*(timeOff-self.timePosition)
                    if x1>self.keyWidth: #key must be on screen
                        y0=y1-self.keyHeight
                        if y0<self.pianoRollY0:
                            y0=self.pianoRollY0 #y0 must be on piano roll
                        x0=self.keyWidth+tickWidth*(timeOn-self.timePosition)
                        if x0<self.keyWidth:
                            x0=self.keyWidth
                        self.canvas.create_rectangle(x0,y0,x1,y1,
                                                     fill=self.noteColor)
                        self.canvas.create_line(x1-rightLineWidth,y0+2,
                                                x1-rightLineWidth,y1-2,width=1)     

    def drawMeasureNumbers(self):
        #draws the measure numbers above the piano roll
        barHeight=self.measureNumberBarHeight
        self.canvas.create_rectangle(0,self.pianoRollY0-barHeight,self.width,
                                     self.pianoRollY0,fill='light grey')
        ticksPerMeasure=self.ticksPerBeat*self.beatsPerMeasure
        tickWidth=self.measureWidth/ticksPerMeasure
        measureNum=int(math.ceil(float(self.timePosition)/ticksPerMeasure))+1
        #first measure num that will display on bar (starts from measure 1)
        measureNumX=(self.keyWidth+(-self.timePosition%
                        ticksPerMeasure)*tickWidth)
        #x of first measure number
        cy=self.pianoRollY0-0.5*barHeight
        while measureNumX<self.width:
            self.canvas.create_text(measureNumX,cy,text=measureNum)
            measureNumX+=self.measureWidth
            measureNum+=1

    def drawMeasureSlider(self):
        #draws the slider at top of piano roll that determines how many
        #measures of the piano roll will be shown
        sliderLeftEnd=self.timePosition*self.width/self.maxTime
        sliderRightEnd=self.timeEnd*self.width/self.maxTime
        x0=sliderLeftEnd
        x1=sliderRightEnd
        y0=self.dynY0
        y1=self.pianoRollY0-self.measureNumberBarHeight #ends above bar nums
        self.canvas.create_rectangle(x0,y0,x1,y1,fill='azure')
        leftSliderLine=sliderLeftEnd+self.endLengthChangeHitbox
        rightSliderLine=sliderRightEnd-self.endLengthChangeHitbox
        #lines to change length of slider at right and left
        self.canvas.create_line(leftSliderLine,y0+2,leftSliderLine,y1-2,width=1)
        self.canvas.create_line(rightSliderLine,y0+2,
                                rightSliderLine,y1-2,width=1)

    def createTempoList(self):
        #takes all the tempo events in self.notes, and creates a list
        #that can easily be drawn
        tempoList=[]
        for event in self.notes:
            if event[0]=='tempo':
                (eventType,time,tempo)=event #tempo is seconds per quarter note
                tempo=60/tempo #tempo is quarter notes per minute
                #inserts event into sorted list (by time)
                if (tempoList==[] or time<tempoList[0][0]):
                    #time before first tempo event
                    tempoList=[(time,tempo)]+tempoList
                elif time>=tempoList[-1][0]: #time after last event
                    tempoList+=[(time,tempo)]
                else:
                    for i in xrange(len(tempoList)):
                        if time<tempoList[i][0]: #time of that event
                            tempoList=(tempoList[:i]+[(time,tempo)]+
                                       tempoList[i:])
                            break
        self.tempoList=tempoList

    def drawTempoBox(self,timeStart,timeEnd,tempo):
        #draws a tempo block on tempo screen
        measureWidth=self.measureWidth
        beatWidth=measureWidth/float(self.beatsPerMeasure)
        tickWidth=(beatWidth/self.ticksPerBeat)
        y1=self.tempoPosition
        y0=y1-tempo*self.keyHeight
        x1=self.keyWidth+tickWidth*(timeEnd-self.timePosition)
        if x1>self.keyWidth: #tempo box must be on screen
            if y0<self.pianoRollY0:
                y0=self.pianoRollY0 #y0 must be on piano roll
            x0=self.keyWidth+tickWidth*(timeStart-self.timePosition)
            if x0<self.keyWidth:
                x0=self.keyWidth
            self.canvas.create_rectangle(x0,y0,x1,y1,fill=self.noteColor,
                                         width=0)

    def drawTempoScreen(self):
        #draws the screen where tempo can be set
        self.createTempoList()
        oldTime=None #stores time of previous tempo event
        for tempoEvent in self.tempoList:
            (time,tempo)=tempoEvent
            if oldTime==None:
                oldTime=time
            else: self.drawTempoBox(oldTime,time,oldTempo)
            oldTempo=tempo
            oldTime=time
        if oldTime!=None: #draws last tempo box
            lastTime=self.lastTimeOff()
            self.drawTempoBox(oldTime,lastTime,oldTempo)

    def drawTempoNumbers(self):
        #draws the tempo numbers for the tempo screen
        minTempoDisplayed=(self.tempoPosition-self.height)/self.keyHeight
        maxTempoDisplayed=(self.tempoPosition-self.pianoRollY0)/self.keyHeight+1
        tempoInterval=5 #the interval between tempo numbers displayed
        minTempoDisplayed=minTempoDisplayed/tempoInterval*tempoInterval
        #lowest tempo displayed should be multiple of tempo interval
        for tempo in xrange(minTempoDisplayed,maxTempoDisplayed,tempoInterval):
            cx=self.keyWidth/2
            cy=self.tempoPosition-tempo*self.keyHeight
            self.canvas.create_text(cx,cy,text=tempo,font='arial 10',
                                    fill='white')

    def drawHelpScreen(self):
        #draws the help screen
        #code adapted from class notes
        with open('help.txt', 'rt') as fin:
            helpText=fin.read()
        (cx,cy)=(self.width/2,self.height/2)
        self.canvas.create_text(cx,cy,text=helpText,font='ariel 12',
                                fill='white')
        
    def redrawAll(self):
        self.canvas.delete(ALL)
        self.drawBackground()
        if self.helpScreen==True:
            self.drawHelpScreen()
        else:
            super(PianoRoll,self).redrawAll()
            self.drawMeasureNumbers()
            self.drawMeasureSlider()
            self.drawGrid()
            if self.tempoScreen==True:
                self.drawTempoScreen()
                self.drawTempoNumbers()
            else:
                self.drawKeys()
                self.drawNotes()
    
    def startFluidsynth(self,soundfont):
        #takes in a soundfont to create an instance of fluidsynth
        fs = fluidsynth.Synth()
        fs.start()
        sfid = fs.sfload(soundfont)
        fs.program_select(0, sfid, 0, 0)
        return fs

    def initAnimation(self):
        super(PianoRoll,self).initAnimation()
        self.createNoteList()
        self.notes=[] #store all the notes in a list(mostly for visual purposes)
        self.noteTimingList=[] #stores all the notes in a list (for timing)
        self.fs=self.startFluidsynth('Kawai Grand Piano.sf2')
        self.midiFile=None #no midi file imported initially
        self.fileName=None #file that imported from
        self.tempo=120 #set default tempo to be 120 (bpm)
        self.timePosition=0 #time (in ticks) at leftmost point of piano roll
        self.measureWidth=500.0 #easier to handle as a float
        self.timeEnd=(self.width/self.measureWidth*self.ticksPerBeat*
                      self.beatsPerMeasure)
        self.keyPosition=self.keyHeight*90-3
        self.maxTime=480 #total ticks for full slider bar at top
        self.divisionsPerBeat=4 #smallest subdivision shown of a beat
        self.tripletDivisions=False
        self.tempoScreen=False
        self.keyRange()
        self.tempoPosition=self.height+self.keyHeight*80
        #starts with bottom tempo being 100
        self.helpScreen=False
        
############################################################################
def testAddToTimingList():
    print 'Testing addToTimingList()...',
    pianoRoll=PianoRoll()
    timingList=[]
    timingList=pianoRoll.addToTimingList('on','C7',10,timingList)
    assert timingList==[10, ('on', 'C7', 127)]
    timingList=pianoRoll.addToTimingList('on','C5',5,timingList)
    assert timingList==[5, ('on', 'C5', 127), 5, ('on', 'C7', 127)]
    timingList=pianoRoll.addToTimingList('off','C7',10,timingList)
    assert timingList==[5, ('on', 'C5', 127), 5, ('on', 'C7', 127),
                        0, ('off', 'C7', 0)]
    timingList=pianoRoll.addToTimingList('off','C5',7,timingList)
    assert timingList==[5, ('on', 'C5', 127), 2, ('off', 'C5', 0),
                        3, ('on', 'C7', 127), 0, ('off', 'C7', 0)]
    print 'Passed!'
    
def runPianoRoll():
    pianoRoll=PianoRoll()
    pianoRoll.run()

def testAll():
    testAddToTimingList()
    runPianoRoll()

#testAll()

runPianoRoll()
