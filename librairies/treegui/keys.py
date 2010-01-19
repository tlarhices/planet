"""

    This module regesters keys and converts them to user event
    this is how they key can be bound to other events 

"""
import os
from pandac.PandaModules import Vec2

class Keys:
    """ processes keys including mouse buttons"""
    
    def __init__(self,keyFilename='cfg/keys.config'):
        """ create event prosessor """
        self.focus = None
        self.bound = {}
        
        self.loadFile('cfg/defaultkeys.config')
        self.loadFile('cfg/keys.config')
        
                
        for event in self.bound.keys():
            base.accept(event,self.onKey,[event]) 
                       
        letters = "abcdefghijklmnopqrstuvwxyz"     
        symbols = "1234567890-=,./[]\\;'`"
        shifted = "!@#$%^&*()_+<>?{}|:\"~"
        work = ['enter','backspace','space','tab','delete','home','end','arrow_left','arrow_up','arrow_down','arrow_right']        
        self.mouseEvents = dict.fromkeys(["mouse1", "mouse2", "mouse3"])
        for mouseEvent in ["mouse1", "mouse2", "mouse3","mouse1-up","mouse2-up","mouse3-up","shift-mouse1"]:
            base.accept(mouseEvent,self.onKey,[mouseEvent])
        for letter in symbols+letters:
            base.accept(letter,self.onKey,[letter])
            base.accept(letter+'-repeat',self.onKey,[letter])
            base.accept('shift-'+letter,self.onKey,[letter.upper()])
            base.accept('shift-'+letter+'-repeat',self.onKey,[letter.upper()]) 
        for event in work:
            base.accept(event,self.onKey,[event])
            base.accept(event+'-repeat',self.onKey,[event])
        for index,key in enumerate(symbols):
            base.accept('shift-'+key,self.onKey, [shifted[index]] )
            base.accept('shift-'+key+'-repeat',self.onKey, [shifted[index]] ) 
        self.inputKeys = dict.fromkeys(list(letters+letters.upper()+symbols+shifted)+work)

        self.lastMouseTime = 0
        self.lastMouse = None

        
    def loadFile(self,keyFilename):
        """" load a file with key file syntax """
        if os.path.exists(keyFilename):
            text = vfs.readFile(keyFilename,True)
            for n,line in enumerate(text.split("\n")):
                s = line.split() 
                if s == []:
                    continue
                elif line[0] == "#":
                    pass
                elif line[0] != "#":
                    key,message = s   
                    self.bound[key] = message
                else:
                    print "error in keys.txt file on line %i"%n
    
        
    def getMouseVec(self):
        """ returns mouse vector """
        md = base.win.getPointer( 0 )
        return Vec2(md.getX(),md.getY())

    def onKey(self,key,time=0):
        """ 
            if gui is in focus give keys to that else 
            see if they are bound to action 
        """

        if key in ("mouse1-up","mouse2-up","mouse3-up"):            
            gui.dragWidget = None
            
        if key in self.mouseEvents:
            if gui.baseMouseEvent(key):
                return
            
        if self.focus != None and key in self.inputKeys:
            if key == 'tab':
                self.focus = gui.focusNext(self.focus)
                return
            
            if self.focus.onKey(key):
                return
        
        if key in self.bound:
            messenger.send(self.bound[key])
        
    
      
        