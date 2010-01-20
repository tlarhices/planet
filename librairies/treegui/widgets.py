"""

    This file hold simple widgets
    that are not composed of other widgets

    includes labels, buttons, entry, check, radio, icons

"""

class Widget(object):
    """
        This is the root of the UI object hiarchy
    """

    id = None           # name it can be found in the system
    
    parent = None
    x = 0
    y = 0
    width = 20
    height = 20
    _x = 0
    _y = 0
    _width = 20
    _height = 20


    text = None     
    font = "default_font"     
    icon = None
    tooltip = None

    visable = True       # can we see
    disabled = False     # can we interect   
    control = False      # can we focus and interect    

    
    children = None        # only holders can have children   
    clips = True        # does it clip children 
    
    style = "frame"
    
    editsText = False
    
    color = (1,1,1,1)
    clickExpand = 0
    
    def __init__(self,**placement):
        self.doPlacement(placement)    
        self.children = []
        
    def doPlacement(self, placement):
        
        if "id" in placement: self.id = placement["id"]
        if "x" in placement: self.x = placement["x"]
        if "y" in placement: self.y = placement["y"]
        if "pos" in placement: self.x,self.y = placement["pos"]
        if "width" in placement: self.width = placement["width"]
        if "height" in placement: self.height = placement["height"]
        if "size" in placement: self.width,self.height = placement["size"]
        if "clips" in placement: self.clips = placement["clips"]
        if "style" in placement: self.style = placement["style"]
        if "icon" in placement: self.icon = placement["icon"]
        if "font" in placement: self.font = placement["font"]
        
    def toggle(self):
        self.visable = not self.visable
        
    def show(self):
        self.visable = True
        
    def hide(self):
        self.visable = False
        
    def onAdd(self):
        """ called when this is added to some holder """
        
    def onRemove(self):
        """ called on removal """
        
    def onIn(self):
        """ called when mouse starts to hover """
    onIn = False
        
    def onOut(self):
        """ called when mouse moves out """
    onOut = False
            
    def onHover(self):
        """ called when mouse is hovering over this """
    onHover = False
    
    def __onHover__(self):
      pass
    
        
    def onClick(self):
        """ called when this is right clicked """
    onClick = False
        
    def onContext(self):
        """ called when this is left clicked """
    onContext = False
        
    def onDoubleClick(self):
        """ called on double right click """
        
    def onFocus(self):
        """ called when this gains focus """
        
    def onUnFocus(self):
        """ called when focus is lost """
        
    def onKey(self, key):
        """ called when key is typed into this """
        
    def onDrag(self):
        """ when dragging """
        
    def onDrop(self):
        """ when the element is dropped """
        
    def mouseEvent(self,event,x,y):
        """ mouse even to override all other mouse events. """
        return False
        
    def fix(self,x,y):
        """ does some thing before the thing is drawn """
        
        
class Icon(Widget):
    """ a simple image that can act as a button"""
    clips = False
    style = None
    def __init__(self, icon, **placement):
        self.doPlacement(placement)    
        self.icon = icon
        
class RotatedIcon(Widget):
    """ a simple image that can act as a button"""
    clips = False
    style = None
    def __init__(self, icon,rotation, **placement):
        self.doPlacement(placement)            
        self.icon = icon
        self.rotation = rotation
        
class Label(Widget):
    """ display a string of text in the ui """
    clips = False
    style = "label"

    def __init__(self, text="" , **placement):
        self.doPlacement(placement)    
        self.text = text
                
class Button(Widget):
    """ this should have up, over, down, disabled states """ 
    style = "button"
    upStyle = "button"
    overStyle = "button_over"
    downStyle = "button_down"

    control = True
    
    def __init__(self, text, onClick, **placement):
        self.doPlacement(placement)    
        self.text = text
        self.onClick = onClick        
    
    def onKey(self,char):
        if char == "enter": self.onClick()
            
    def onIn(self):
        self.style = self.overStyle

    def onOut(self):
        self.style = self.upStyle



class ValueButton(Button):
    """ 
        this button has a value that gets passed to 
        onSelect button
    """
    def __init__(self, text, value, onSelect, **placement):
        Button.__init__(self, text, self.onClick, **placement)
        self.value = value
        self.onSelect = onSelect
   
    def onClick(self):
       self.onSelect(self.value)



class TextArea(Label):
    """ single line entry for people to fight text with """
    style = "entry"
    text = ""
    control = True
    
    editsText = True
    
    textLimit = None
    
    multiLine = True
    
    selection = (0,0)
    caret = -1
    
    def onClick(self):
        gui.focusOn(self)
        return True
    
    def onKey(self,char):
        #print "char:",char
        #print "caret:",self.caret
        
        if len(char) == 1:
            self.text = self.text[:self.caret]+char+self.text[self.caret:]
            self.caret += 1
        elif char == "backspace":
            if self.caret > 0:
                self.text = self.text[:self.caret-1]+self.text[self.caret:]
                self.caret -= 1
        elif char == "delete":
            if self.caret < len(self.text):
                self.text = self.text[:self.caret]+self.text[self.caret+1:]
        elif char == "space":
            self.text = self.text[:self.caret]+" "+self.text[self.caret:]
            self.caret += 1
        elif char == "arrow_left":
            if self.caret > 0:
                self.caret -= 1
        elif char == "arrow_right":
            if self.caret < len(self.text):
                self.caret += 1
        elif char == "home":
            if self.caret > 0:
                self.caret = 0
        elif char == "end":
            if self.caret > 0:
                self.caret = len(self.text)
        elif self.multiLine and char == "enter" :
            self.text += "\n"
            self.caret += 1
        elif not self.multiLine and char == "enter" :    
            self.onEnter(self.text)
        elif self.multiLine and char == "arrow_up" :
            lastLine = 0
            thisLine = 0
            for i,c in enumerate(self.text+" "):
                if i == self.caret:
                    lead = min(self.caret - thisLine,thisLine - lastLine)
                    self.caret = lastLine + lead
                    break
                if c == "\n":
                    lastLine = thisLine
                    thisLine = i
            if self.caret < 1 : self.caret = 1
        elif self.multiLine and char == "arrow_down" :
            farLine = len(self.text)
            lastLine = len(self.text)
            thisLine = len(self.text)
            for i,c in reversed(list(enumerate(self.text+" "))):
                if c == "\n":
                    farLine = lastLine
                    lastLine = thisLine
                    thisLine = i
                if thisLine < self.caret:
                    lead = min(self.caret-thisLine, abs(farLine-lastLine))
                    self.caret = lastLine + lead
                    break
            if self.caret > len(self.text) : self.caret = len(self.text)
        else:
            print char,"undefined for tree text entry yet"
         
        if self.textLimit:
            self.text = self.text[:self.textLimit]
           
    def onFocus(self):
        if self.caret == -1:
            self.caret = len(self.text)
        
    def onUnfocus(self):
        self.caret = -1 
    
class Entry(TextArea):
    multiLine = False
    
    def onEnter(self,text):
        """ overide if you need enter events, like chat and stuff """
        
class PasswordEntry(Entry):
    """ single line entry that types as stars "*" """
    
    style = "entry"
    password = ""
    
    def onKey(self,char):
        self.text = self.password
        Entry.onKey(self,char)
        self.password = self.text
        self.text = "*"*len(self.password)
            
class Text(Widget):
    """ multi-line entry for people to fight text with """
    style = "textbox"   
    control = True 

class Check(Label):
    """
        Standard on/off button
    """
    style = "CHECKOFF"
    value = False

    def __init__(self, text, **placement):
        self.doPlacement(placement)    
        self.text = "     "+text
            
    def onClick(self):
        """ checks or uncecks the button value """
        self.value = not self.value
        if self.value:
            self.style = "CHECKON"
        else:
            self.style = "CHECKOFF"  
            
class Radio(Check):
    """ 
        radio button ... only one button of this 
        type can be selected in a given parent 
    """
    style = "RADIOOFF"
    value = False
            
    def onClick(self):
        """ 
            changes the state of the radio and 
            changaes the state of the radio buttons 
            around it
        """
        
        for child in self.parent.children:
            if child.__class__ == self.__class__:
                child.value = False
                child.style = "RADIOOFF"
                
        self.value = not self.value
        if self.value:
            self.style = "RADIOON"
        else:
            self.style = "RADIOOFF"  
        
