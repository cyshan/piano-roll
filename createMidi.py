class CreateMidi(object):
    #creates a midi file out of a note timing track
    def __init__(self,fileName,timingTrack,ticksPerBeat):
        self.byteList=[]
        self.ticksPerBeat=ticksPerBeat
        self.timingTrack=timingTrack
        #create a list of ints (0-255) to turn into binary midi file
        self.createHeaderChunk()
        self.createTrackChunk()
        binaryFile=bytearray(self.byteList)
        with open(fileName, 'wb') as f:
            f.write(binaryFile)

    def createHeaderChunk(self):
        #creates the header chunk for the file
        byteList=self.byteList
        chunkType='MThd' #chunk must begin with chunk type
        for c in chunkType:
            byteList+=[ord(c)]
        chunkLen=6 #standard len for header chunk
        midiFormat=0 #will only write format 0 midi files
        tracks=1 #midi 0 can only have 1 track
        ticksPerBeat=self.ticksPerBeat
        dataByteLen=[(chunkLen,4),(midiFormat,2),(tracks,2),(ticksPerBeat,2)]
        #list of data and how many bytes it occupies
        for dataLen in dataByteLen:
            (data,length)=dataLen
            byteList+=self.convertToBytes(data,length)
        self.byteList=byteList

    def createTrackChunk(self):
        #from the timing track, create a track chunk
        byteList=self.byteList
        chunkType='MTrk' #chunk must begin with chunk type
        for c in chunkType:
            byteList+=[ord(c)]
        self.track=[] #list of bytes in the track (as ints)
        while self.timingTrack!=[]:
            tickDelay=self.timingTrack.pop(0)
            self.track+=self.createVariableLenBytes(tickDelay)
            event=self.timingTrack.pop(0)
            self.addEventToTrack(event)
        endToken=[1,255,47,0] #token for end of track
        self.track+=endToken
        trackLength=len(self.track)
        byteList+=self.convertToBytes(trackLength,4)
        #4 bytes to represent track length
        byteList+=self.track
        self.byteList=byteList

    def addEventToTrack(self,event):
        #adds an event (tempo, noteOn, noteOff) to self.track
        eventType=event[0]
        if eventType=='on':
            (eventType,note,velocity)=event
            eventMarker=144 #marker to signal on event
            eventList=[eventMarker,note,velocity]
        elif eventType=='off':
            (eventType,note,velocity)=event
            eventMarker=128 #marker to signal off event
            eventList=[eventMarker,note,velocity]
        elif eventType=='tempo':
            (eventType,tempo)=event
            tempoMarker=[255,81,3] #signals a tempo event
            tempo=int(tempo*1000000) #turns tempo back into microsecs per beat
            tempoData=self.convertToBytes(tempo,3) #tempo represented by 3 bytes
            eventList=tempoMarker+tempoData
        self.track+=eventList

    @staticmethod
    def createVariableLenBytes(num):
        #takes an int, and creates a list of bytes to represent the int
        #in the variable length format
        byteList=[]
        bitsPerByte=7 #usable bits per byte is 7 (msb is 1 except last byte)
        maxVal=2**7 #max value per variable len byte
        if num==0:
            byteList=[0]
            return byteList
        while num>0: #until num is "used up"
            byteList=[num%maxVal+maxVal]+byteList
            #makes msb of every byte '1'
            num/=maxVal
        byteList[-1]-=maxVal #takes away msb of last byte
        return byteList

    @staticmethod
    def convertToBytes(num,numBytes):
        #converts an int into a list of certain number of bytes
        byteList=[None]*numBytes
        maxByte=256 #values stored in a byte
        for byteNum in xrange(numBytes-1,-1,-1):
            byteList[byteNum]=num%maxByte #256 is base for 1 byte
            num/=maxByte #for next byte
        return byteList

############################################################################
############################################################################

def testConvertToBytes():
    print 'Testing convertToBytes()...',
    timingTrack=[]
    createMidi=CreateMidi('foo.mid',timingTrack,24)
    assert(createMidi.convertToBytes(6,4)==[0,0,0,6])
    assert(createMidi.convertToBytes(0,4)==[0,0,0,0])
    assert(createMidi.convertToBytes(2354245,4)==[0,35,236,69])
    assert(createMidi.convertToBytes(2763306,3)==[42,42,42])
    assert(createMidi.convertToBytes(6,1)==[6])
    print 'Passed!'

def testCreateVariableLenBytes():
    print 'Testing createVariableLenBytes()...',
    timingTrack=[]
    createMidi=CreateMidi('foo.mid',timingTrack,24)
    assert(createMidi.createVariableLenBytes(0)==[0])
    assert(createMidi.createVariableLenBytes(64)==[64])
    assert(createMidi.createVariableLenBytes(127)==[127])
    assert(createMidi.createVariableLenBytes(128)==[129,0])
    assert(createMidi.createVariableLenBytes(134217728)==[192,128,128,0])
    print 'Passed!'
    
def testCreateMidi():
    timingTrack=[0, ('on', 60, 127), 24, ('off', 60, 0),
     0, ('on', 62, 127), 24, ('off', 62, 0), 0,
     ('on', 64, 127), 24, ('off', 64, 0), 0,
     ('on', 65, 127), 24, ('off', 65, 0)]
    createMidi=CreateMidi('foo.mid',timingTrack,24)

        
def testAll():
    testConvertToBytes()
    testCreateVariableLenBytes()
    testCreateMidi()

#testAll()
    
