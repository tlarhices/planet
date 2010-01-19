"""

    This file hold simple widgets
    that are not composed of other widgets

    includes labels, buttons, entry, check, radio, icons

"""

from treegui.widgets import *
from treegui.components import *

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

class SetterBar(ProgressBar):
    def __init__(self, text, percent, **placement):
        ProgressBar.__init__(self, percent, **placement)
        self.textComponent = self.add(Label(text))
        self.children.reverse()
      
    def mouseEvent(self, event, x, y):
        if event=="mouse1":
            self.setProgress(float(x)/self.width*100)
            if self.callbackParams!=None:
              self.callbackParams["etat"]=float(x)/self.width*100
              self.callback(**self.callbackParams)
            
    def callback(self, text, value):
      pass
      
class Groupe(Pane):
  def __init__(self, **placement):
    self.doPlacement(placement)
    
  def add(self, composant):
    Pane.add(composant)
    self.MAJ()
    
  def remove(self, composant):
    Pane.remove(composant)
    self.MAJ()

  def MAJ(self):
    if len(self.children)==0:
      self.width = 15
      self.height = 15
      return
    cote = int(math.sqrt(len(self.children))+0.5)
    self.width = cote*self.children[0].width+(cote+1)*PAD
    self.height = cote*self.children[0].height+(cote+1)*PAD
    ligne = 0
    colone = 0
    for composant in self.children:
      if colone >= cote:
        ligne+=1
        colone = 0
      composant.x=colone*PAD+(colone-1)*composant.width
      composant.y=colone*PAD+(colone-1)*composant.width
      colone+=1
