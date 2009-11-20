#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandac.PandaModules import *

import sys

import treegui
from treegui.components import Form,Widget,ScrollPane
from treegui.widgets import *
from treegui.core import Gui
import rtheme

class Gauche(Form):
  style = "default"
  
  def clic(self, bouton, etat):
    print bouton.lower, etat
  
  def inverse(self):
    for bouton in self.boutons:
      bouton.onClick()
  
  def __init__(self, gui):
    self.gui=gui
    Form.__init__(self)
    self.add(Label("Unitées :".decode("utf-8"), x=3, y = 0))
    self.boutons = []
    i=1
    liste=[]
    liste.append(("gugusse 1",0,10,"rtheme/twotone/user-over.png", "rtheme/twotone/user.png"))
    liste.append(("gugusse 2",0,30,"rtheme/twotone/user-over.png", "rtheme/twotone/user.png"))
    liste.append(("gugusse 3",10,50,"rtheme/twotone/user-over.png", "rtheme/twotone/user.png"))
    liste.sort()
    for elem in liste:
      check = self.add(PictureRadio(elem[3], elem[4], elem[0].capitalize(), x=3, y = 17*i))
      check.callback = self.clic
      self.boutons.append(check)
      i+=1
    
    self.x = "left" 
    self.y = "top" 
    self.width = "110px"
    self.height = "80%"
        
class Droite(Form):
  style = "default"

  def __init__(self, gui):
    self.gui=gui
    Form.__init__(self)
    
    self.plus = self.add(Icon("rtheme/twotone/zoom-in.png", x="left", y=0))
    #self.plus.onClick = self.gui.zoomPlus
    self.moins = self.add(Icon("rtheme/twotone/zoom-out.png", x="right", y=0))
    #self.moins.onClick = self.gui.zoomMoins
    self.haut = self.add(Icon("rtheme/twotone/arrow-up.png", x="center", y=20))
    #self.haut.onClick = self.gui.deplaceHaut
    self.gauche = self.add(Icon("rtheme/twotone/arrow-left.png", x="left", y=37))
    #self.gauche.onClick = self.gui.deplaceGauche
    self.droite = self.add(Icon("rtheme/twotone/arrow-right.png", x="right", y=37))
    #self.droite.onClick = self.gui.deplaceDroite
    self.bas = self.add(Icon("rtheme/twotone/arrow-down.png", x="center", y=54))
    #self.bas.onClick = self.gui.deplaceBas
    
    zero = 60
    self.snapGPS = self.add(PictureRadio("rtheme/twotone/target-over.png", "rtheme/twotone/target.png", y = zero + 17, x=0))
    self.snapContenu = self.add(PictureRadio("rtheme/twotone/news-over.png", "rtheme/twotone/news.png", y = zero + 17, x=17))
    self.snapLibre = self.add(PictureRadio("rtheme/twotone/move-over.png", "rtheme/twotone/move.png", y = zero + 17, x=34))
    self.snapGPS.onClick()
    
    self.x = "right" 
    self.y = "top" 
    self.width = "54px"
    self.height = "105px"

class BasGauche(Form):
  style = "default"
  
  def __init__(self, gui):
    self.gui = gui
    Form.__init__(self)
    
    self.haut = self.add(Label(self.gui.joueur.nom, y="top"))
    self.bas = self.add(Label("", y="bottom"))
    self.centre = self.add(Label("bois : 0\r\nbouffe : 0", y="center"))
    
    #label.font = font
    
    self.x = "left" 
    self.y = "center" 
    self.width = "80px"
    self.height = "100%"

class BasDroite(Form):
  style = "default"
  
  def __init__(self, gui):
    self.gui = gui
    Form.__init__(self)
    
    self.haut = self.add(Label("", y="top"))
    self.bas = self.add(Label("", y="bottom"))
    self.centre = self.add(Label("", y="center"))
    #label.font = font
    
    self.x = "left" 
    self.y = "center" 
    self.width = "100%"
    self.height = "100%"

class Bas(Form):
  style = "default"
  
  def __init__(self, gui):
    self.gui = gui
    Form.__init__(self)
    
    self.droite = self.add(BasDroite(gui))
    
    self.x = "center" 
    self.y = "bottom" 
    self.width = "80%"
    self.height = "60px"

class Interface:
  joueur = None
  def __init__(self):
    base.accept("q", sys.exit)
    base.accept("escape", sys.exit)
    #base.accept("arrow_left", self.deplaceGauche)
    #base.accept("arrow_right", self.deplaceDroite)
    #base.accept("arrow_up", self.deplaceHaut)
    #base.accept("arrow_down", self.deplaceBas)
    #base.accept("mouse1", clicGauche)
    #base.accept("mouse2", clicCentre)
    #base.accept("mouse3", clicDroit)

    self.gui = Gui(theme = rtheme.RTheme())
    self.bas = Bas(self)
    self.gui.add(self.bas)
    self.quit = self.gui.add(Icon("rtheme/twotone/x.png", x="right", y="top"))
    self.quit.onClick = sys.exit
    
  def ajouteJoueur(self, joueur):
    print "GUI pour joueur",joueur.nom
    self.joueur = joueur
    self.droite = Droite(self)
    self.gui.add(self.droite)
    self.gauche = Gauche(self)
    self.gui.add(self.gauche)
    self.bas.gauche = self.bas.add(BasGauche(self))
    self.bas.droite.x = "80px"
    
    
  def afficheTexte(self, texte, forceRefresh=False):
    """Affiche le texte sur l'écran, si texte==None, alors efface le dernier texte affiché"""
    try:
      if texte!=None:
        self.bas.droite.haut.text=self.bas.droite.centre.text
        self.bas.droite.centre.text=self.bas.droite.bas.text
        self.bas.droite.bas.text=texte
        
    except NameError:
      return
    
    if forceRefresh:
      self.gui._doMouse()
      self.gui._doDrag()
      self.gui._reSize()
      self.gui._layout()
      self.gui._draw()
      base.graphicsEngine.renderFrame()
    