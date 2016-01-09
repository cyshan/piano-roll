class Midi(object):
    def __init__(self,fileName):
        assert(fileName[-4:]=='.mid') #midi file must end with .mid filename
        self.readFileByByte(fileName)
        self.parseMidiFile()

    def parseMidiFile(self):
        #analyzes midi file data
        base=16 #working in hexadecimal
        byteList=self.byteList
        self.parseHeaderChunk()
        self.trackNames=[None]*self.numTracks
        #create empty list to be filled with names of each track
        self.tempoTrack=[]
        for track in xrange(self.numTracks): #parse each track
            self.trackNum=track
            self.parseTrackChunk(track)
            
    def parseHeaderChunk(self):
        #parses header chunk of midi file, and then removes it from byteList
        byteList=self.byteList
        chunkType='MThd' #in midi spec
        base=16 #hex is base 16
        firstFourBytes=self.hexToAscii(byteList[:len(chunkType)])
        #turn first four bytes into a "word" by ascii
        assert(firstFourBytes==chunkType) #part of midi specification
        byteList=byteList[len(chunkType):]#remove parts of list no longer needed
        headerLength=int(self.combineBytes(byteList[0:4]),base)
        #next four bytes are for header length
        byteList=byteList[4:] #removes the leader length bytes
        self.format=int(self.combineBytes(byteList[0:2]),base)
        self.numTracks=int(self.combineBytes(byteList[2:4]),base)
        self.ticksPerQuarterNote=int(self.combineBytes(byteList[4:6]),base)
        #all part of midi specs, turns 2 byte sequence into ints
        byteList=byteList[headerLength:]
        self.byteList=byteList

    def parseTrackChunk(self,track):
        #parses one track chunk of midi file, and then removes it from byteList
        byteList=self.byteList
        chunkType='MTrk' #in midi spec
        base=16 #hex is base 16
        firstFourBytes=self.hexToAscii(byteList[:len(chunkType)])
        #turn first four bytes into a "word" by ascii
        assert(firstFourBytes==chunkType) #part of midi specification
        byteList=byteList[len(chunkType):] #removes type of chunk
        self.byteList=byteList
        #in format 1, only last track has midi data
        if self.format==1 and track<self.numTracks-1:
            #0th track of format 1 is tempo track 
            self.parseTempoTrack()
        elif self.format==1: #for midi track in format 1
            self.parseTrack()
        elif self.format==0:
            self.parseTrack()

    def variableLengthValue(self):
        #starting from beginning of track, turns a variable length bytes
        #into an int value
        value=0
        base=16 #in hexadecimal
        track=self.track
        maxByte=128 #max representation of 7 bits
        while int(track[0],base)>maxByte: #while first bit is 1
            value+=int(track[0],base) % maxByte
            value*=128 #moves "bits" right 7 places
            track=track[1:]
            #add last 7 bits of first byte to deltaTime and delete first byte
        value+=int(track[0],base) % maxByte
        track=track[1:] #add last byte in delta time and delete
        self.track=track
        return value
   
    def parseTrack(self):
        #parses a non-tempo track
        byteList=self.byteList
        base=16
        trackLength=int(self.combineBytes(byteList[0:4]),base)
        #next four bytes are for track length
        byteList=byteList[4:] #remove header length bytes from byteList
        self.track=byteList[:trackLength]
        self.dataTrack=[] #store track data with format <deltaTime><info>
        self.deltaTime=0 #time between events
        while True: #will loop over track until it hits stop command
            self.deltaTime+=self.variableLengthValue()
            #tempo track should only contain meta events
            if self.track[0]=='ff': #token for meta event
                self.track=self.track[1:] #remove token
                if self.parseMetaEvent(self.dataTrack)==False:
                    #stop command reached
                    break
            else:
                self.parseMidiEvent(self.dataTrack)
                #any other token means it's a midi event
        byteList=byteList[trackLength:] #done with track, delete track
        self.byteList=byteList
    
    def parseTempoTrack(self):
        #for format 1, when first track is always tempo track, parse tempo
        byteList=self.byteList
        base=16
        trackLength=int(self.combineBytes(byteList[0:4]),base)
        #next four bytes are for track length
        byteList=byteList[4:] #remove header length bytes from byteList
        self.track=byteList[:trackLength]
        #stores all tempo info in a list with format <deltaTime><info>
        self.deltaTime=0 #time between events
        while True: #will loop over track until it hits stop command
            self.deltaTime+=self.variableLengthValue()
            #tempo track should only contain meta events
            if self.track[0]=='ff': #token for meta event
                self.track=self.track[1:] #remove token
                if self.parseMetaEvent(self.tempoTrack)==False:
                    #stop command reached
                    break
        byteList=byteList[trackLength:] #done with track, delete track
        self.byteList=byteList

    def parseMetaEvent(self,dataTrack):
        #handles each possible meta event, takes in a dataTrack to store data
        #returns false only if end is reached
        track=self.track
        event=track[0] #first byte represents event type
        self.track=track=track[1:] #removes event type
        eventLength=self.variableLengthValue()
        track=self.track
        #next bytes represent event length
        self.eventData=track[:eventLength]
        if event=='2f': return False #end token
        elif event[0]=='0': #if first char of event is 0, it's a text event
            self.textEvent=event[1]#second char of event decides the text event
            self.parseTextEvent()
        elif event[0]=='5': #5 controls tempo, key sig, etc.
            self.eventType=event[1]#second char of event decides exact event
            dataTrack+=[self.deltaTime]
            self.deltaTime=0
            self.parseTempoEvent(dataTrack)
        self.track=track[eventLength:] #removes event from track

    def parseTextEvent(self):
        #stores text according to value of text event
        textEvent=int(self.textEvent)
        text=self.hexToAscii(self.eventData)
        if textEvent==0: #sequence data
            self.sequenceNumber=self.eventData
        elif textEvent==1: #generic text field
            self.text=text
        elif textEvent==2: #copyright notice
            self.copyright=text
        elif textEvent==3: #sequence/track name
            if self.format==0:
                self.sequenceName=text
            else:self.trackNames[self.trackNum]=text
        elif textEvent==4: #instrument
            self.instrumentNmae=text
        elif textEvent==5: #lyrics
            self.lyrics=text
        elif self.textEvent==6: #marker
            sef.marker=text
        elif self.textEvent==7: #cue points
            self.cuePoint=text

    def parseTempoEvent(self,dataTrack):
        #parsing of tempo, keysig, etc. events
        (event,data)=(self.eventType,self.eventData)
        base=16 #hexadecimal
        if event=='1': #tempo change-tempo is microseconds per quarter note
            ms=int(self.combineBytes(data),base)#turn hexadecimal into int
            sec=ms/1000000.0 #million ms in a sec
            dataTrack+=[('tempo',sec)] #store data in format (eventType,data)
        elif event=='8': #time signature change
            #time sig is 4 separate bytes, each with different meaning
            num=int(data[0],base) #0th byte is numerator of time sig
            den=2**int(data[1],base) #1st byte is log 2 of denom of time sig
            clock=int(data[2],base)#2nd byte is clock ticks per metronome click
            quarterNote=int(data[3],base)
            #3rd byte defines number of 32nd notes per quarter note (usually 8)
            dataTrack+=[('timesig',num,den,clock,quarterNote)]
        elif event=='9': #key signature change
            #key sig is two bytes, first for key, and second for major/minor
            key=int(data[0],base) #key is number of sharps or flats by sign
            mi=int(data[1], base) #0 is major 1 is minor
            dataTrack+=[('keysig', key, mi)]

    def parseMidiEvent(self,dataTrack):
        #handles certain midi events, takes in a dataTrack to store data
        track=self.track
        base=16 #hexadecimal
        event=int(track[0],base)
        msb=128 #isolates most significant byte
        if event<msb: #all events have 1 in msb, so this is running status
            event=self.event
        else:
            self.event=track[0]
            self.track=track=track[1:] #removes event type
        self.eventType=event=int(self.event[0],base)
        #only first 4 bits determine event
        if event>=8 and event<=14: #channel messages
            self.chanNum=int(self.event[1],base) #last 4 bits is channel num
            if event>=8 and event<=10 or event==13: #note on or note off
                self.parseNoteEvent(dataTrack)
            elif event==11: #control change
                self.parseControlChange()
            elif event==12: #program change
                self.parseProgramChange()
        elif event==15: #system messages
            pass
        
    def parseNoteEvent(self,dataTrack):
        #stores note on/off into into data
        dataTrack+=[self.deltaTime] #stores dTime into list
        self.deltaTime=0
        event=self.eventType
        track=self.track
        base=16 #hexadecimal
        data=track[:2] #next 2 bytes are data for note events
        note=int(data[0],base) #note number is stored in first data byte
        velocity=int(data[1],base) #velocity is stored in second data byte
        if event==8: #note off
            dataTrack+=[('off', note)] 
        elif event==9: #note on
            dataTrack+=[('on', note,velocity)]
        self.track=track[2:] #delete note data from track
        
    def parseControlChange(self):
        #does not do anything except delete data from track
        self.track=self.track[2:]
        
    def parseProgramChange(self):
        #does not do anything except delete data from track
        self.track=self.track[1:]

    @staticmethod
    def combineBytes(byteList):
        #combines a list of hex bytes into a single hex string
        combinedByte=''
        for byte in byteList:
            combinedByte+=byte
        return combinedByte

    @staticmethod
    def hexToAscii(byteList):
        #turns a list of hex bytes into an ascii string of characters
        base=16 #hexadecimal
        string=''
        for byte in byteList:
            char=chr(int(byte,base))
            string+=char
        return string
    
    def readFileByByte(self,fileName):
        #takes in a file name and returns the contents of the file
        #as a list of decimal bytes (0-255)
        midi=open(fileName,'rb')
        midiFile=midi.read()
        byteList=[]
        for byteIndex in xrange(len(midiFile)):
            byte=hex(ord(midiFile[byteIndex]))[2:]
            #turns each byte into hex and removing the '0x' in front
            if len(byte)==1:
                byte='0'+byte #add placeholder if no 0 in front
            byteList+=[byte]
        self.byteList=byteList
