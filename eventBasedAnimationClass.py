# eventBasedAnimationClass.py
# Taken with minor changes from course notes (more bindings and name changes)
# Also starts window at fullscreen, not resizable
# Code for starting window fullscreen taken from:
# http://tkinter.unpythonic.net/wiki/MaximizedWindow
  
from Tkinter import *
import sys

class EventBasedAnimationClass(object):
    def leftMousePressed(self, event): pass
    def rightMousePressed(self, event): pass
    def onKeyPressed(self, event): pass
    def mouseMotion(self,event): pass
    def leftMouseMotion(self,event): pass
    def rightMouseMotion(self,event): pass
    def leftMouseReleased(self,event): pass
    def rightMouseReleased(self,event): pass
    def mouseWheel(self,event): pass
    def onTimerFired(self): pass
    def redrawAll(self): pass
    def initAnimation(self): pass

    def __init__(self):
        self.timerDelay = 250 # in milliseconds (set to None to turn off timer)

    def leftMousePressedWrapper(self, event):
        if (not self._isRunning): return
        self.leftMousePressed(event)
        self.redrawAll()

    def rightMousePressedWrapper(self, event):
        if (not self._isRunning): return
        self.rightMousePressed(event)
        self.redrawAll()

    def leftMouseMotionWrapper(self, event):
        if (not self._isRunning): return
        self.leftMouseMotion(event)

    def rightMouseMotionWrapper(self, event):
        if (not self._isRunning): return
        self.rightMouseMotion(event)

    def rightMouseReleasedWrapper(self,event):
        if (not self._isRunning): return
        self.rightMouseReleased(event)
        self.redrawAll()
        
    def leftMouseReleasedWrapper(self,event):
        if (not self._isRunning): return
        self.leftMouseReleased(event)
        self.redrawAll()

    def onKeyPressedWrapper(self, event):
        if (not self._isRunning): return
        self.onKeyPressed(event)
        self.redrawAll()

    def onTimerFiredWrapper(self):
        if (not self._isRunning): self.root.destroy(); return
        if (self.timerDelay == None): return # turns off timer
        self.onTimerFired()
        self.redrawAll()
        self.canvas.after(self.timerDelay, self.onTimerFiredWrapper)
    
    def mouseMotionWrapper(self, event):
        if (not self._isRunning): return
        self.mouseMotion(event)

    def mouseWheelWrapper(self,event):
        if (not self._isRunning): return
        self.mouseWheel(event)

    def quit(self):
        if (not self._isRunning): return
        self._isRunning = False
        if (self.runningInIDLE):
            # in IDLE, must be sure to destroy here and now
            self.root.destroy()
        else:
            # not IDLE, then we'll destroy in the canvas.after handler
            self.root.quit()

    def run(self):
        # create the root and the canvas
        self.root = Tk()
        self.canvas = Canvas(self.root)
        self.canvas.pack(fill=BOTH, expand=YES)
        toplevel = self.root.winfo_toplevel()
        toplevel.wm_state('zoomed')
        self.initAnimation()
        # set up events
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.quit())
        self._isRunning = True
        self.runningInIDLE =  ("idlelib" in sys.modules)
        # DK: You can use a local function with a closure
        # to store the canvas binding, like this:
        def f(event): self.leftMousePressedWrapper(event)    
        self.root.bind("<Button-1>", f)
        def g(event): self.mouseMotionWrapper(event)    
        self.root.bind("<Motion>", g)
        def h(event): self.rightMousePressedWrapper(event)    
        self.root.bind("<Button-3>", h)
        def i(event): self.leftMouseMotionWrapper(event)    
        self.root.bind("<B1-Motion>", i)
        def j(event): self.rightMouseMotionWrapper(event)    
        self.root.bind("<B3-Motion>", j)
        def k(event):self.leftMouseReleasedWrapper(event)
        self.root.bind("<B1-ButtonRelease>", k)
        def l(event):self.rightMouseReleasedWrapper(event)
        self.root.bind("<B3-ButtonRelease>", l)
        def m(event): self.mouseWheelWrapper(event)
        self.root.bind("<MouseWheel>", m)
        # DK: Or you can just use an anonymous lamdba function, like this:
        self.root.bind("<Key>", lambda event: self.onKeyPressedWrapper(event))
        self.onTimerFiredWrapper()
        # and launch the app (This call BLOCKS, so your program waits
        # until you close the window!)
        self.root.mainloop()

##EventBasedAnimationClass().run()
