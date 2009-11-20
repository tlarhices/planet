#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandac.PandaModules import *

import sys
import general

import treegui
from treegui.components import Form,Widget,ScrollPane
from treegui.widgets import *
from treegui.core import Gui
import rtheme

class Gauche(Form):
  """Contient la liste des unitées que l'on peut construire"""
  style = "default"
  
  def clic(self, bouton, etat):
    """
    On a cliqué sur un bouton de construction d'unité
    bouton : le texte du bouton
    etat : si True alors le bouton est actif (ce devrait toujours être le cas de figure)
    """
    print bouton.lower, etat
  
  def __init__(self, gui):
    self.gui=gui
    Form.__init__(self)
    #On met un titre au menu
    self.add(Label("Unitées :".decode("utf-8"), x=3, y = 0))
    
    #On place les boutons d'achat de gugusse
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
    
    #On positionne la Form
    self.x = "left" 
    self.y = "top" 
    self.width = "110px"
    self.height = "80%"
        
class Droite(Form):
  """Contrôles de la caméra"""
  style = "default"

  def __init__(self, gui):
    self.gui=gui
    Form.__init__(self)
    
    self.plus = self.add(Icon("rtheme/twotone/zoom-in.png", x="left", y=0))
    self.plus.onClick = general.zoomPlus
    self.moins = self.add(Icon("rtheme/twotone/zoom-out.png", x="right", y=0))
    self.plus.onClick = general.zoomMoins
    self.haut = self.add(Icon("rtheme/twotone/arrow-up.png", x="center", y=20))
    self.plus.onClick = general.deplaceHaut
    self.gauche = self.add(Icon("rtheme/twotone/arrow-left.png", x="left", y=37))
    self.plus.onClick = general.deplaceGauche
    self.droite = self.add(Icon("rtheme/twotone/arrow-right.png", x="right", y=37))
    self.plus.onClick = general.deplaceDroite
    self.bas = self.add(Icon("rtheme/twotone/arrow-down.png", x="center", y=54))
    self.plus.onClick = general.deplaceBas
    
    #On positionne la Form
    self.x = "right" 
    self.y = "34px" 
    self.width = "54px"
    self.height = "105px"

class BasGauche(Form):
  """Informations sur le joueur"""
  style = "default"
  
  def __init__(self, gui):
    self.gui = gui
    Form.__init__(self)
    
    #Nom du joueur
    self.haut = self.add(Label(self.gui.joueur.nom, y="top"))
    #Statistiques
    self.bas = self.add(Label("bois : 0\r\nbouffe : 0", y="center"))
    
    #On positionne la Form
    self.x = "left" 
    self.y = "center" 
    self.width = "80px"
    self.height = "100%"

class BasDroite(Form):
  """Boite de message"""
  style = "default"
  
  def __init__(self, gui):
    self.gui = gui
    Form.__init__(self)
    
    #On garde 3 lignes de texte
    self.haut = self.add(Label("", y="top"))
    self.centre = self.add(Label("", y="center"))
    self.bas = self.add(Label("", y="bottom"))
    
    #On positionne la Form
    self.x = "left" 
    self.y = "center" 
    self.width = "100%"
    self.height = "100%"
    
  def ajouteTexte(self, texte):
    """Ajoute une ligne dans le log"""
    self.haut.text=self.centre.text
    self.centre.text=self.bas.text
    self.bas.text=texte
    

class Bas(Form):
  """
  Cadre qui contient les élément de la barre du bas
  s'il n'y a pas de joueur la structure est ainsi :
  [[zone de textes informatifs]]
  s'il y a un joueur :
  [[détails du joueur][zone de textes informatifs]]
  """
  style = "default"
  
  def __init__(self, gui):
    self.gui = gui
    Form.__init__(self)
    
    self.droite = self.add(BasDroite(gui))
    
    #On positionne la Form
    self.x = "center" 
    self.y = "bottom" 
    self.width = "80%"
    self.height = "60px"

class Interface:
  joueur = None
  def __init__(self):
    #Fabrique le GUI de base
    self.gui = Gui(theme = rtheme.RTheme())
    self.bas = Bas(self)
    self.gui.add(self.bas)
    
  def ajouteJoueur(self, joueur):
    """Indique qu'on passe du mode chargement au mode joueur"""
    self.joueur = joueur
    
    #On ajoute les composants manquants
    self.droite = Droite(self)
    self.gui.add(self.droite)
    self.gauche = Gauche(self)
    self.gui.add(self.gauche)
    #On insère la zone d'infos dans la barre du bas
    self.bas.gauche = self.bas.add(BasGauche(self))
    self.bas.droite.x = "80px"
    #On place un bouton quitter en haut à droite de l'écran
    self.quit = self.gui.add(Icon("rtheme/twotone/x.png", x="right", y="top"))
    self.quit.onClick = sys.exit
    
    
  def afficheTexte(self, texte, forceRefresh=False):
    """Affiche le texte sur l'écran, si texte==None, alors efface le dernier texte affiché"""
    if texte!=None:
      #On affiche une ligne dans le log
      print texte
      self.bas.droite.ajouteTexte(texte)
        
    if forceRefresh:
      #On force le recalcul du GUI
      self.gui._doMouse()
      self.gui._doDrag()
      self.gui._reSize()
      self.gui._layout()
      self.gui._draw()
      #On force le rendu
      base.graphicsEngine.renderFrame()
    