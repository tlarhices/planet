"""

    This file hold simple widgets
    that are not composed of other widgets

    includes labels, buttons, entry, check, radio, icons

"""

from treegui.widgets import *

class PictureCheck(Label):
    """
        Standard on/off button
    """
    style = "CHECKOFF"
    value = False
    
    def __init__(self, picOn, picOff, text, **placement):
        self.doPlacement(placement)    
        self.text = "   "+text
        self.icon = picOff
        self.picOff = picOff
        self.picOn = picOn

    def onClick(self):
        """ checks or uncecks the button value """
        self.value = not self.value
        if self.value:
            self.icon = self.picOn
        else:
            self.icon = self.picOff
        self.callback(self.text.strip(), self.value)
            
    def callback(self, text, value):
      pass
            
class PictureRadio(Check):
    """ 
        radio button ... only one button of this 
        type can be selected in a given parent 
    """
    style = "RADIOOFF"
    value = False
            
    def __init__(self, picOn, picOff, text="", **placement):
        self.text = "   "+text
        self.doPlacement(placement)    
        self.icon = picOff
        self.picOff = picOff
        self.picOn = picOn
            
    def onClick(self):
        """ 
            changes the state of the radio and 
            changaes the state of the radio buttons 
            around it
        """
        if self.parent != None:
          for child in self.parent.children:
              if child.__class__ == self.__class__:
                  child.value = False
                  child.icon = child.picOff
                
        self.value = not self.value
        if self.value:
            self.icon = self.picOn
        else:
            self.icon = self.picOff  
        self.callback(self.text.strip(), self.value)
            
    def callback(self, text, value):
      pass
      
      
class IconButton(Icon):
  callbackParams = None
  def onClick(self):
    if self.callbackParams!=None:
      self.callback(**self.callbackParams)
            
    def callback(self, text, value):
      pass
