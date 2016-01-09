from eventBasedAnimationClass import EventBasedAnimationClass
from Tkinter import *

class SequencerStaticGraphics(EventBasedAnimationClass):
    #displays all the graphics that do not change when program is running
    def __init__(self):
        super(SequencerStaticGraphics,self).__init__()
        (self.width,self.height) = (1362,701)
        #specific height and width on my computer when window is maximized
        #window is forced to be maximized, so should not cause problems
        self.backgroundColor='midnight blue'
        self.buttonColor='medium blue'
        self.buttonTextColor='pale turquoise'
        self.dynY0=48 #where dynamic graphics start
        
    def createTopRowButtons(self):
        #add buttons in top row to button dict
        buttonDict=dict()
        topLeft=['New', 'Import','Export','Duplet','Triplet']
        #buttons on top left
        topRight=['Help'] #buttons on top left
        (buttonX0,buttonX1)=(0,0) #these will change for each button
        letterWidth=27 #length of button depends of length of text
        buttonY1=25 #this is the same, creates buttons on row at top
        buttonPower=0.85 #makes increase of button size with text len sublinear
        for button in topLeft:
            buttonWidth=(len(button)*letterWidth)**buttonPower
            buttonX1+=buttonWidth #add width of button 
            buttonDict[button]=(buttonX0,0,buttonX1,buttonY1)
            buttonX0=buttonX1 #sets up for next button
        (buttonX0,buttonX1)=(self.width,self.width)
        #these will change for each button, but starting from right
        for button in topRight:
            buttonWidth=(len(button)*letterWidth)**buttonPower
            buttonX0-=buttonWidth
            buttonDict[button]=(buttonX0,0,buttonX1,buttonY1)
            buttonX1=buttonX0
        self.buttons=buttonDict

    def createSecondRowButtons(self):
        #add buttons in second row to button dict
        buttonDict=self.buttons
        secondRowButtons=['Play','Piano Roll', 'Tempo']
        (buttonX0,buttonX1)=(0,0) #these will change for each button
        letterWidth=27 #length of button depends of length of text
        buttonY0=25
        self.frameY0=buttonY1=46 #changes for second row, also top of dynamic
        buttonPower=0.85 #makes increase of button size with text len sublinear
        for button in secondRowButtons:
            buttonWidth=(len(button)*letterWidth)**buttonPower
            buttonX1+=buttonWidth #add width of button 
            buttonDict[button]=(buttonX0,buttonY0,buttonX1,buttonY1)
            buttonX0=buttonX1 #sets up for next button
        self.buttons=buttonDict       
    
    def createButtons(self):
        #creates dict of buttons with keys as button
        #names and button coords as values
        self.createTopRowButtons()
        self.createSecondRowButtons()

    def drawButtons(self):
        #draw all the buttons in the button dict
        buttons=self.buttons
        for key in buttons:
            (x0,y0,x1,y1)=buttons[key]
            (cx,cy)=((x0+x1)/2,(y1+y0)/2)
            self.canvas.create_rectangle(x0,y0,x1,y1,fill=self.buttonColor)
            self.canvas.create_text(cx,cy,text=key,fill=self.buttonTextColor)

    def drawDynamicGraphicsFrame(self):
        #draws frame for where all the dynamic graphics will be kept in
        self.canvas.create_rectangle(0,self.frameY0,self.width,self.height,
                                     width=4)
            
    def redrawAll(self):
        #does not delete all--deleted in dynamic graphics
        self.drawButtons()
        self.drawDynamicGraphicsFrame()

    def initAnimation(self):
        self.createButtons()
        
############################################################################
def testStaticGraphics():
    staticG=SequencerStaticGraphics()
    staticG.run()

##testStaticGraphics()
