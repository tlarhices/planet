#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandac.PandaModules import *

import sys
import general

import treegui
from treegui.components import *
from treegui.widgets import *
from treegui.core import Gui
import rtheme
import os

PAD = 4
HAUTEUR_BOUTON = 28
HAUTEUR_CHECK = 15
HAUTEUR_TEXTE = 15
TAILLE_ICONE = 15

class Gauche(Form):
  """Contient la liste des unitées que l'on peut construire"""
  style = "default"
  
  def clic(self, bouton, etat):
    """
    On a cliqué sur un bouton de construction d'unité
    bouton : le texte du bouton
    etat : si True alors le bouton est actif (ce devrait toujours être le cas de figure)
    """
    print bouton.lower(), etat
  
  def __init__(self, gui):
    self.gui=gui
    Form.__init__(self, u"Unitées")
    
    #On place les boutons d'achat de gugusse
    self.boutons = []
    i=PAD+HAUTEUR_BOUTON
    liste=general.configuration.getConfigurationSprite()
    for elem in liste:
      check = self.add(PictureRadio(elem[3], elem[4], elem[0].capitalize(), x=3, y = i))
      check.callback = self.clic
      self.boutons.append(check)
      i+=HAUTEUR_CHECK
    
    #On positionne la Form
    self.x = "left" 
    self.y = "top" 
    self.width = "110px"
    self.height = "80%"
        
class BasGauche(Pane):
  """Informations sur le joueur"""
  style = "default"
  
  def __init__(self, gui):
    self.gui = gui
    Pane.__init__(self)
    
    self.haut = self.add(Label(self.gui.joueur.nom, y=0))
    #Statistiques
    self.bas = self.add(Label("bois : 0\r\nbouffe : 0", y=HAUTEUR_TEXTE+PAD/2))
    
    #On positionne la Form
    self.x = "left" 
    self.y = "center" 
    self.width = "80px"
    self.height = "100%"

class BasDroite(Pane):
  """Boite de message"""
  style = "default"
  lignes = None
  position = None
  
  def __init__(self, gui):
    self.gui = gui
    Pane.__init__(self)
    self.lignes = []
    self.position = 0
    
    y=0
    #On garde 6 lignes de texte
    self.l1 = self.add(Label("", x=0, y=0)) #Texte
    self.i1 = self.add(Icon("rtheme/twotone/blank.png", x=20, y=y)) #Icone
    self.i1.visable = False #On cache l'icone
    y+=HAUTEUR_TEXTE
    self.l2 = self.add(Label("", x=20, y=y))
    self.i2 = self.add(Icon("rtheme/twotone/blank.png", x=20, y=y))
    self.i2.visable = False
    y+=HAUTEUR_TEXTE
    self.l3 = self.add(Label("", x=20, y=y))
    self.i3 = self.add(Icon("rtheme/twotone/blank.png", x=20, y=y))
    self.i3.visable = False
    y+=HAUTEUR_TEXTE
    self.l4 = self.add(Label("", x=20, y=y))
    self.i4 = self.add(Icon("rtheme/twotone/blank.png", x=20, y=y))
    self.i4.visable = False
    
    #Bare de défilement
    self.plus = self.add(Icon("rtheme/twotone/arrow-up.png", x="left", y="top"))
    self.plus.onClick = self.logHaut
    self.plus = self.add(Icon("rtheme/twotone/arrow-down.png", x="left", y="bottom"))
    self.plus.onClick = self.logBas
    self.curseur = self.add(Icon("rtheme/twotone/blank.png", x="left", y=HAUTEUR_TEXTE))
    
    #On positionne la Form
    self.x = "left" 
    self.y = "center" 
    self.width = "100%"
    self.height = "100%"
    
  def logHaut(self):
    """Fait défiler le log vers le haut"""
    self.position-=1
    if self.position < 0:
      self.position = 0
    self.refresh()
    
  def logBas(self):
    """Fait défiler le log vers le bas"""
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
      
    self.lignes.insert(0,(icone, texte))
    self.refresh()
    
  def refresh(self):
    """Met à jour le texte dans la zone d'affichage"""
    #On extrait les 4 que l'on veut afficher
    lignes = self.lignes[self.position:self.position+4]
    
    #On calcule la position du curseur de la barre de défilement
    prct = float(self.position)/float(len(self.lignes))*10
    self.curseur.y = HAUTEUR_TEXTE + int(prct)
    
    if len(lignes) >= 1:
      self.MAJObjet(self.i1, self.l1, lignes[0][0], lignes[0][1])
      print self.l1.getSize()
    else:
      self.MAJObjet(self.i1, self.l1, None, None)
      
    if len(lignes) >= 2:
      self.MAJObjet(self.i2, self.l2, lignes[1][0], lignes[1][1])
    else:
      self.MAJObjet(self.i2, self.l2, None, None)

    if len(lignes) >= 3:
      self.MAJObjet(self.i3, self.l3, lignes[2][0], lignes[2][1])
    else:
      self.MAJObjet(self.i3, self.l3, None, None)

    if len(lignes) >= 4:
      self.MAJObjet(self.i4, self.l4, lignes[3][0], lignes[3][1])
    else:
      self.MAJObjet(self.i4, self.l4, None, None)

    
  icones = {
  "inconnu":"rtheme/twotone/q.png",
  "mort":"rtheme/twotone/skull.png",
  "chat":"rtheme/twotone/phone.png",
  "info":"rtheme/twotone/info.png",
  "avertissement":"rtheme/twotone/caution.png"
  }
    
  def MAJObjet(self, objeti, objett, type, texte):
    #On met à jour le contenu
      
    if texte!=None:
      
      if type==None:
        icone = None
      elif type in self.icones.keys():
        icone = self.icones[type]
      else:
        icone = self.icones["inconnu"]
      
      #Si on a une icone, on pousse le texte un peu
      if icone != None:
        texte="   "+texte

      if icone != None:
        objeti.visable = True #On affiche l'icone si on doit en afficher une
        objeti.icon = icone #On change l'icone
      else:
        objeti.visable = False #On cache l'icone s'il n'y en a pas à afficher
      objett.text = texte #On change le texte
    else:
      #Il n'y a pas de texte, ni d'icone
      objeti.visable = False
      objett.text = ""
      
class Bas(Pane):
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
    Pane.__init__(self)
    
    self.droite = self.add(BasDroite(gui))
    
    #On positionne la Form
    self.x = "center" 
    self.y = "bottom" 
    self.width = "80%"
    self.height = "60px"
    
class Chargement(Pane):
  """
  Bandeau qui dit "chargement..."
  """
  style = "default"
  
  def __init__(self):
    Pane.__init__(self)
    
    self.label = self.add(Label("Chargement en cours...", x="left", y=PAD))
    
    #On positionne la Form
    self.x = "center" 
    self.y = "center" 
    self.width = "80%"
    self.height = "20px"
    
class EcranTitre(Pane):
  """Le menu principal"""
  style = "default"
  
  def __init__(self, gui):
    Pane.__init__(self)
    self.gui = gui
    self.label = self.add(Label(u"Vertes & plaisantes contrées", x="left", y=PAD))
    
    #On positionne la Form
    self.x = "center" 
    self.y = "center" 
    self.width = "80%"
    self.height = "20px"
    taskMgr.doMethodLater(0.5, self.gui.effaceEcranTitre, 'effaceEcranTitre')
    
class MenuPrincipal(Form):
  """Le menu principal"""
  style = "default"
  
  def __init__(self, gui):
    Form.__init__(self, "Menu principal")
    self.gui = gui
    
    y=PAD + HAUTEUR_BOUTON
    self.boutonNouveau = self.add(Button(u"Nouvelle planète", self.gui.nouvellePlanete, x="center", y=y, width="190px"))
    
    y+=PAD/2 + HAUTEUR_BOUTON
    cpt = 0
    for fich in os.listdir(os.path.join(".", "data", "planetes")):
      if fich.endswith(".pln"):
        cpt+=1
    if cpt==0:
      self.boutonVierge = self.add(Label(u"Utiliser un planète vierge", x="center", y=y, width="190px"))
    else:
      self.boutonVierge = self.add(Button(u"Utiliser un planète vierge", self.gui.planeteVierge, x="center", y=y, width="190px"))
    
    y+=PAD/2 + HAUTEUR_BOUTON
    cpt = 0
    for fich in os.listdir(os.path.join(".", "sauvegardes")):
      if fich.endswith(".pln"):
        cpt+=1
    if cpt==0:
      self.boutonCharger = self.add(Label(u"Charger une partie", x="center", y=y, width="190px"))
    else:
      self.boutonCharger = self.add(Button(u"Charger une partie", self.gui.chargerPartie, x="center", y=y, width="190px"))

    y+=PAD/2 + HAUTEUR_BOUTON
    self.boutonNouveau = self.add(Button(u"Configuration", self.gui.configurer, x="center", y=y, width="190px"))
    
    y+=PAD/2 + HAUTEUR_BOUTON
    #On positionne la Form
    self.x = "center" 
    self.y = "center" 
    self.width = "80%"
    self.height = y
    
  def back(self):
    self.gui.changeMenuVers(MenuPrincipal)
    
class MenuConfiguration(Form):
  """Le menu principal"""
  style = "default"
  
  def __init__(self, gui):
    Form.__init__(self, "Configuration")
    self.gui = gui
    
    self.colonneGauche = self.add(Pane(x="left", y=PAD+HAUTEUR_BOUTON, width="30%", height="100%"))
    self.colonneDroite = self.add(Pane(x="right", y=PAD+HAUTEUR_BOUTON, width="70%", height="100%"))
    
    y=PAD
    self.colonneGauche.add(PictureRadio("rtheme/twotone/gear-over.png", "rtheme/twotone/gear.png", u"Affichage", x="left", y=y)).callback = self.clic
    y+=HAUTEUR_TEXTE + PAD/2
    self.colonneGauche.add(PictureRadio("rtheme/twotone/move-over.png", "rtheme/twotone/move.png", u"Contrôles", x="left", y=y)).callback = self.clic
    y+=HAUTEUR_TEXTE + PAD/2
    self.colonneGauche.add(PictureRadio("rtheme/twotone/radio-off-over.png", "rtheme/twotone/radio-off.png", u"Planètes", x="left", y=y)).callback = self.clic
    y+=HAUTEUR_TEXTE + PAD/2
    self.colonneGauche.add(PictureRadio("rtheme/twotone/target-over.png", "rtheme/twotone/target.png", u"Debug", x="left", y=y)).callback = self.clic

    self.add(Icon("rtheme/twotone/rotate_node.png", x="right", y="bottom")).onClick = self.back
    
    #On positionne la Form
    self.x = "center" 
    self.y = "center" 
    self.width = "80%"
    self.height = PAD*4+HAUTEUR_BOUTON+HAUTEUR_TEXTE*4
    
  resolutions = ["160 120", "320 240", "640 480", "800 600", "1024 768"]
    
  def resolutionPlus(self):
    res = general.configuration.getConfiguration("affichage-general", "resolution","640 480")
    if res in self.resolutions:
      idx = self.resolutions.index(res)
      idx+=1
      while idx>=len(self.resolutions):
        idx-= len(self.resolutions)
    else:
      idx=0
    general.configuration.setConfiguration("affichage-general", "resolution", self.resolutions[idx])
    self.clic("affichage", True)
    
  def resolutionMoins(self):
    res = general.configuration.getConfiguration("affichage-general", "resolution","640 480")
    if res in self.resolutions:
      idx = self.resolutions.index(res)
      idx-=1
      while idx<0:
        idx+= len(self.resolutions)
    else:
      idx=0
    general.configuration.setConfiguration("affichage-general", "resolution", self.resolutions[idx])
    self.clic("affichage", True)
    
  def clic(self, bouton, etat):
    """
    On a cliqué sur un bouton de changement de panneau de configuration
    bouton : le texte du bouton
    etat : si True alors le bouton est actif (ce devrait toujours être le cas de figure)
    """
    self.remove(self.colonneDroite)
    self.colonneDroite = self.add(Pane(x="right", y=PAD+HAUTEUR_BOUTON, width="70%", height="100%"))
    if bouton.lower() == "affichage":
      w=PAD/2
      w+= self.colonneDroite.add(Label(u"Résolution  ", x=PAD, y=PAD)).getSize()[1] + PAD / 2
      self.colonneDroite.add(Icon("rtheme/twotone/arrow-left.png", x=w, y=PAD)).onClick = self.resolutionMoins
      w+=TAILLE_ICONE + PAD/2
      w += self.colonneDroite.add(Label(general.configuration.getConfiguration("affichage-general", "resolution","640 480"), x=w, y=PAD)).getSize()[1]
      self.colonneDroite.add(Icon("rtheme/twotone/arrow-right.png", x=w, y=PAD)).onClick = self.resolutionPlus
      tmp = self.colonneDroite.add(Check(u"Bloom", x=4, y=20))
      if general.configuration.getConfiguration("affichage-effets", "utiliseBloom","0")=="1":
        tmp.onClick()
    elif bouton.lower() == u"contrôles":
      self.remove(self.colonneDroite)
      self.colonneDroite = self.add(ScrollPane(x="right", y=PAD+HAUTEUR_BOUTON, width="70%", height="100%"))
      y=4
      touches = general.configuration.getConfigurationClavier()
      for element in touches.keys():
        self.colonneDroite.add(Label(touches[element]+u" : "+element, x=4, y=y))
        y+=16
    elif bouton.lower() == u"planètes":
      self.colonneDroite.add(Label(u"Résolution : "+general.configuration.getConfiguration("affichage-general", "resolution","640 480"), x=4, y=4))
      tmp = self.colonneDroite.add(Check(u"Bloom", x=4, y=20))
      if general.configuration.getConfiguration("affichage-effets", "utiliseBloom","0")=="1":
        tmp.onClick()
    elif bouton.lower() == u"debug":
      self.colonneDroite.add(Label(u"Résolution : "+general.configuration.getConfiguration("affichage-general", "resolution","640 480"), x=4, y=4))
      tmp = self.colonneDroite.add(Check(u"Bloom", x=4, y=20))
      if general.configuration.getConfiguration("affichage-effets", "utiliseBloom","0")=="1":
        tmp.onClick()
      
      
    
    
  def back(self):
    self.gui.changeMenuVers(MenuPrincipal)
    
    
class MenuVierge(Form):
  """Contient la liste des planètes vierges que l'on peut charger"""
  style = "default"
  
  def clic(self, bouton, etat):
    """
    On a cliqué sur un bouton de construction d'unité
    bouton : le texte du bouton
    etat : si True alors le bouton est actif (ce devrait toujours être le cas de figure)
    """
    for element in self.liste:
      if element[0].lower() == bouton.lower():
        self.gui.planeteVierge2(element[1])
  
  def __init__(self, gui):
    self.gui=gui
    Form.__init__(self, u"Planètes :")
    
    #On place les boutons d'achat de gugusse
    self.boutons = []
    i=2
    self.liste=[]
    for element in os.listdir(os.path.join(".", "data", "planetes")):
      if element.endswith(".pln"):
        self.liste.append((element.lower(), element))
    for elem in self.liste:
      check = self.add(PictureRadio("rtheme/twotone/news-over.png", "rtheme/twotone/news.png", elem[0].capitalize(), x=3, y = 17*i))
      check.callback = self.clic
      self.boutons.append(check)
      i+=1
      
    self.add(Icon("rtheme/twotone/rotate_node.png", x="right", y="bottom")).onClick = self.back
    
    #On positionne la Form
    self.x = "center" 
    self.y = "center" 
    self.width = "80%"
    self.height = "80%"
    
  def back(self):
    self.gui.changeMenuVers(MenuPrincipal)
    
class MenuCharge(Form):
  """Contient la liste des planètes vierges que l'on peut charger"""
  style = "default"
  
  def clic(self, bouton, etat):
    """
    On a cliqué sur un bouton de construction d'unité
    bouton : le texte du bouton
    etat : si True alors le bouton est actif (ce devrait toujours être le cas de figure)
    """
    for element in self.liste:
      if element[0].lower() == bouton.lower():
        self.gui.planeteVierge2(element[1])
  
  def __init__(self, gui):
    self.gui=gui
    Form.__init__(self, u"Sauvegardes")
    
    #On place les boutons d'achat de gugusse
    self.boutons = []
    i=2
    self.liste=[]
    for element in os.listdir(os.path.join(".", "sauvegardes")):
      if element.endswith(".pln"):
        self.liste.append((element.lower(), element))
    for elem in self.liste:
      check = self.add(PictureRadio("rtheme/twotone/diskette-over.png", "rtheme/twotone/diskette.png", elem[0].capitalize(), x=3, y = 17*i))
      check.callback = self.clic
      self.boutons.append(check)
      i+=1
      
    self.add(Icon("rtheme/twotone/rotate_node.png", x="right", y="bottom")).onClick = self.back
    
    #On positionne la Form
    self.x = "center" 
    self.y = "center" 
    self.width = "80%"
    self.height = "80%"
    
  def back(self):
    self.gui.changeMenuVers(MenuPrincipal)
    
class Interface:
  joueur = None
  menuCourant = None
  
  def __init__(self, start):
    #Fabrique le GUI de base
    self.start = start
    self.gui = Gui(theme = rtheme.RTheme())
    #On affiche l'écran de titre
    self.menuCourant = self.gui.add(EcranTitre(self))
    
  def changeMenuVers(self, classe):
    if self.menuCourant != None:
      self.gui.remove(self.menuCourant)
      if classe != None:
        self.menuCourant = self.gui.add(classe(self))
      else:
        self.menuCourant = None
      
  def effaceEcranTitre(self, task):
    #Supprime l'écran de titre, charge le menu principal
    self.changeMenuVers(MenuPrincipal)
    return task.done
      
  def nouvellePlanete(self):
    #Construit une nouvelle planète aléatoirement
    self.makeMain()
    self.start.fabriquePlanete(os.path.join(".", "configuration", "planete.cfg"))
    self.start.start()
    
  def makeMain(self):
    #Construit les éléments principaux de l'interface
    self.changeMenuVers(None)
    self.bas = Bas(self)
    self.gui.add(self.bas)
    self.chargement = self.gui.add(Chargement())
    
  def configurer(self):
    self.changeMenuVers(MenuConfiguration)
    
  def planeteVierge(self):
    self.changeMenuVers(MenuVierge)
    
  def planeteVierge2(self, fichier):
    #Charge un prototype de planète pré-construit
    self.makeMain()
    self.start.chargePlanete(os.path.join(".", "data", "planetes", fichier))
    self.start.start()
    
  def chargerPartie(self):
    self.changeMenuVers(MenuCharge)
    
  def chargerPartie2(self):
    #Charge une partie en cours
    self.makeMain()
    self.start.chargePlanete(os.path.join(".", "sauvegardes", "1.pln"))
    self.start.start()
    
  def ajouteJoueur(self, joueur):
    """Indique qu'on passe du mode chargement au mode joueur"""
    self.joueur = joueur
    
    #On ajoute les composants manquants
    self.gauche = Gauche(self)
    self.gui.add(self.gauche)
    #On insère la zone d'infos dans la barre du bas
    self.bas.gauche = self.bas.add(BasGauche(self))
    self.bas.droite.x = "80px"
    #On place un bouton quitter en haut à droite de l'écran
    self.quit = self.gui.add(Icon("rtheme/twotone/x.png", x="right", y="top"))
    self.quit.onClick = sys.exit
    self.gui.remove(self.chargement)
    self.chargement = None
    
    
  def afficheTexte(self, texte, type="normal", forceRefresh=False):
    """Affiche le texte sur l'écran, si texte==None, alors efface le dernier texte affiché"""
    if texte!=None:
      #On affiche une ligne dans le log
      if type == None:
        print texte
      else:
        print "["+str(type)+"]",texte
      self.bas.droite.ajouteTexte(type, texte)
        
    if forceRefresh:
      #On force le recalcul du GUI
      self.gui._doMouse()
      self.gui._doDrag()
      self.gui._reSize()
      self.gui._layout()
      self.gui._draw()
      #On force le rendu
      base.graphicsEngine.renderFrame()
    