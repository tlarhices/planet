"""

    This file hold simple widgets
    that are not composed of other widgets

    includes labels, buttons, entry, check, radio, icons

"""

from treegui.widgets import *
from treegui.components import *
import math
import general

PAD = 4

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
    else:
      self.callback()
            
  def callback(self):
    pass
    
class IconButtonCouleur(Pane):
  colorCenter = None
  colorAround = None
  iconFile = None
  callbackParams = None
  
  def __init__(self, icon, colorCenter, colorAround, **placement):
    Pane.__init__(self, **placement)
    self.style=None
    self.colorCenter = colorCenter
    self.colorAround = colorAround
    self.iconFile = icon
    button = self.add(IconButton(self.iconFile))
    button.callback = self.buttonCallback
    button.x=2
    button.y=2
    button.color = colorCenter
    fond = self.add(Pane(width="100%", height="100%"))
    fond.color = colorAround
    self.width=20 #15 pour l'icone + contour de 2
    self.height=20
    
  def onClick(self):
    self.buttonCallback()
    
  def buttonCallback(self):
    if self.callbackParams!=None:
      self.callback(**self.callbackParams)
    else:
      self.callback()
            
  def callback(self):
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
  largeur = None
  hauteur = None
  
  def __init__(self, largeur=None, hauteur=None, **placement):
    self.largeur = largeur
    self.hauteur = hauteur
    self.doPlacement(placement)
    self.children=[]
    
  def add(self, composant):
    comp = Pane.add(self, composant)
    self.MAJ()
    return comp
    
  def remove(self, composant):
    comp = Pane.remove(self, composant)
    self.MAJ()
    return comp

  def MAJ(self):
    if len(self.children)==0:
      self.width = 15
      self.height = 15
      return
      
    if self.largeur==None and self.hauteur==None:
      cote = int(math.sqrt(len(self.children))+0.5)
      largeur = cote
      hauteur = cote
      
    elif self.largeur == None:
      hauteur = self.hauteur
      largeur = int(float(len(self.children))/hauteur+0.5)
      
    elif self.hauteur == None:
      largeur = self.largeur
      hauteur = int(float(len(self.children))/largeur+0.5)
      
    else:
      largeur = self.largeur
      hauteur = self.hauteur
      
      
    if largeur<1:
      largeur=1
    if hauteur<1:
      hauteur=1
      
    self.width = largeur*self.children[0].width+(largeur-2)*PAD
    
    ligne = 0
    colone = 0
    for composant in reversed(self.children):
      if colone >= largeur:
        ligne+=1
        colone = 0
      composant.x=colone*PAD+colone*composant.width
      composant.y=ligne*PAD+ligne*composant.height
      self.height = composant.y + composant.height
      colone+=1
    
class EntryHistory(Entry):
  
  def tradTouche(self, touche):
    letters = "abcdefghijklmnopqrstuvwxyz"     
    symbols = "1234567890-^@[;:],./\\"#"1234567890-=,./[]\\;'`"
    shifted = "!\"#$%&'()~=~`{+*}<>?_"#"!@#$%^&*()_+<>?{}|:\"~"
    
    if "shift" in general.io.touchesControles:
      if touche in letters:
        return touche.upper()
      if touche in symbols:
        return shifted[symbols.index(touche)]
    return touche

  def onKey(self, char):
    char = self.tradTouche(char)
    if char=="arrow_up":
      history = self.history(-1)
      if history != None:
        self.text = history
    elif char=="arrow_down":
      history = self.history(1)
      if history != None:
        self.text = history
    else:
      Entry.onKey(self, char)
      
  def history(self, move):
    return None
    
class TextAreaRO(Label):
  """ single line entry for people to fight text with """
    
  def onKey(self,char):
    pass
    
  def onFocus(self):
    self.caret = -1 
        
  def onUnfocus(self):
    self.caret = -1 
      
