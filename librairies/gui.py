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
    liste=general.configurationSprite.getConfigurationSprite()
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
  lignes = None
  position = None
  
  def __init__(self, gui):
    self.gui = gui
    Form.__init__(self)
    self.lignes = []
    self.position = 0
    
    #On garde 6 lignes de texte
    self.l1 = self.add(Label("", x=20, y=0))
    self.i1 = self.add(Icon("rtheme/twotone/blank.png", x=20, y=0))
    self.i1.visable = False
    self.l2 = self.add(Label("", x=20, y=15))
    self.i2 = self.add(Icon("rtheme/twotone/blank.png", x=20, y=15))
    self.i2.visable = False
    self.l3 = self.add(Label("", x=20, y=30))
    self.i3 = self.add(Icon("rtheme/twotone/blank.png", x=20, y=30))
    self.i3.visable = False
    self.l4 = self.add(Label("", x=20, y=45))
    self.i4 = self.add(Icon("rtheme/twotone/blank.png", x=20, y=45))
    self.i4.visable = False
    self.plus = self.add(Icon("rtheme/twotone/arrow-up.png", x="left", y="top"))
    self.plus.onClick = self.logHaut
    self.plus = self.add(Icon("rtheme/twotone/arrow-down.png", x="left", y="bottom"))
    self.plus.onClick = self.logBas
    self.curseur = self.add(Icon("rtheme/twotone/blank.png", x="left", y=15))
    
    #On positionne la Form
    self.x = "left" 
    self.y = "center" 
    self.width = "100%"
    self.height = "100%"
    
  def logHaut(self):
    self.position-=1
    if self.position < 0:
      self.position = 0
    self.refresh()
    
  def logBas(self):
    self.position+=1
    if self.position >= len(self.lignes)-6:
      self.position = len(self.lignes)-7
    self.refresh()
    
  def ajouteTexte(self, icone, texte):
    """Ajoute une ligne dans le log"""
    
    #Si on est pas à la tête du log, on laisse la boite sur le texte en cours bien qu'on ajoute une nouvelle ligne
    #Sinon on fait scroller le texte automatiquement
    if self.position !=0:
      self.position+=1
      
    #Si on a une icone, on pousse le texte un peu
    if icone != None:
      texte="   "+texte

    self.lignes.insert(0,(icone, texte))
    self.refresh()
    
  def refresh(self):
    lignes = self.lignes[self.position:self.position+4]
    prct = float(self.position)/float(len(self.lignes))*10
    self.curseur.y = 15 + int(prct)
    
    if len(lignes) >= 1:
      if lignes[0][0] != None:
        self.i1.visable = True
        self.i1.icon = lignes[0][0]
      else:
        self.i1.visable = False
      self.l1.text = lignes[0][1]
    else:
      self.i1.visable = False
      self.l1.text = ""
      
    if len(lignes) >= 2:
      if lignes[1][0] != None:
        self.i2.visable = True
        self.i2.icon = lignes[1][0]
      else:
        self.i2.visable = False
      self.l2.text = lignes[1][1]
    else:
      self.i2.visable = False
      self.l2.text = ""
      
    if len(lignes) >= 3:
      if lignes[2][0] != None:
        self.i3.visable = True
        self.i3.icon = lignes[2][0]
      else:
        self.i3.visable = False
      self.l3.text = lignes[2][1]
    else:
      self.i3.visable = False
      self.l3.text = ""
      
    if len(lignes) >= 4:
      if lignes[3][0] != None:
        self.i4.visable = True
        self.i4.icon = lignes[3][0]
      else:
        self.i4.visable = False
      self.l4.text = lignes[3][1]
    else:
      self.i4.visable = False
      self.l4.text = ""

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
    
    
  def afficheTexte(self, texte, icone=None, forceRefresh=False):
    """Affiche le texte sur l'écran, si texte==None, alors efface le dernier texte affiché"""
    if texte!=None:
      #On affiche une ligne dans le log
      print texte
      self.bas.droite.ajouteTexte(icone, texte)
        
    if forceRefresh:
      #On force le recalcul du GUI
      self.gui._doMouse()
      self.gui._doDrag()
      self.gui._reSize()
      self.gui._layout()
      self.gui._draw()
      #On force le rendu
      base.graphicsEngine.renderFrame()
    