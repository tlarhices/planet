#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandac.PandaModules import *

import sys
import general
import math

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

class MenuCirculaire():
  boutons = None
  retour = None
  besoinRetour = None
  
  def __init__(self, gui):
    self.gui = gui
    self.purge()
    self.besoinRetour = True
    
  def purge(self):
    self.boutons = [[],[]]
    
  def ajouteGauche(self, bouton):
    self.boutons[0].append(bouton)
    return bouton
    
  def ajouteDroite(self, bouton):
    self.boutons[1].append(bouton)
    return bouton

  def cercle(self, centre, rayon, angleOuverture, nbelemsG, nbelemsD):
    elements = [[],[]]
    
    if nbelemsG==1:
      angleG=angleOuverture
    else:
      angleG = float(angleOuverture)/(nbelemsG-1)
    if nbelemsD==1:
      angleD=angleOuverture
    else:
      angleD = float(angleOuverture)/(nbelemsD-1)
    dep = -float(angleOuverture)/2.0
    for i in range(0, max(nbelemsG, nbelemsD)):
      if i<nbelemsD:
        x=rayon*math.cos((dep + angleD*i)/180*math.pi)
        y=rayon*math.sin((dep + angleD*i)/180*math.pi)
        elements[1].append((centre[0]+x,centre[1]+y))
      if i<nbelemsG:
        x=rayon*math.cos((dep + angleG*i)/180*math.pi)
        y=rayon*math.sin((dep + angleG*i)/180*math.pi)
        elements[0].append((centre[0]-x,centre[1]+y))
        
    elements.append((centre[0],centre[1]+rayon))
        
    return elements
    
  def fabrique(self):
    bg, bd = self.boutons
    nbBoutonsG = len(bg)
    nbBoutonsD = len(bd)
    
    coords = self.cercle((base.win.getXSize()/2,base.win.getYSize()/2), base.win.getYSize()/2 - HAUTEUR_BOUTON, 120.0, nbBoutonsG, nbBoutonsD)
    i=0
    for i in range(0, max(nbBoutonsG, nbBoutonsD)):
      if i<len(bg):
        bouton = bg[i]
        x, y = coords[0][i]
        bouton.doPlacement({"x":x-bouton.width, "y":y})
        self.gui.gui.add(bouton)
      
      if i<len(bd):
        bouton = bd[i]
        x, y = coords[1][i]
        bouton.doPlacement({"x":x, "y":y})
        self.gui.gui.add(bouton)
      i+=1
      
    if self.besoinRetour:
      self.retour = self.gui.add(Icon("rtheme/twotone/rotate_node.png", x=coords[2][0], y=coords[2][1]))
      self.retour.onClick = self.back
    else:
      self.retour = None
    
  def back(self):
    self.gui.changeMenuVers(MenuPrincipal)
    
  def MAJ(self):
    tmp = self.boutons[:]
    self.efface()
    self.boutons = tmp
    self.fabrique()
    
  def efface(self):
    for bouton in self.boutons[0]:
      self.gui.remove(bouton)
    for bouton in self.boutons[1]:
      self.gui.remove(bouton)
      
    if self.retour!=None:
      self.gui.remove(self.retour)
      
    self.boutons = [[],[]]
    self.retour = None
      
  def retour(self):
    self.gui.changeMenuVers(MenuPrincipal)
    
class EnJeu(MenuCirculaire):
  """Contient la liste des unitées que l'on peut construire"""
  select = None
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.besoinRetour = False
    self.fabrique()
    
  def fabrique(self):
    self.purge()
    
    liste=general.configuration.getConfigurationSprite()
    for elem in liste:
      #paneau = self.ajouteGauche(Pane(width=90))
      #check = paneau.add(PictureRadio(elem[3], elem[4], elem[0].capitalize()))
      check = self.ajouteGauche(PictureRadio(elem[3], elem[4], elem[0].capitalize(), width=90))
      check.style = "DEFAULT"
      
      if elem[0].lower==self.select:
        check.icon = check.picOn
        check.value=True
      else:
        check.icon = check.picOff
        check.value=True
      check.callback = self.clic
    
    MenuCirculaire.fabrique(self)
    
  def clic(self, bouton, etat):
    """
    On a cliqué sur un bouton de construction d'unité
    bouton : le texte du bouton
    etat : si True alors le bouton est actif (ce devrait toujours être le cas de figure)
    """
    self.select = bouton.lower()
        

class Informations(Pane):
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
    self.l1 = self.add(Label("", x=20, y=0)) #Texte
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
    self.y = "bottom" 
    self.width = "100%"
    self.height = "70px"
    
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
    
class MenuPrincipal(MenuCirculaire):
  """Le menu principal"""
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.besoinRetour = False
    
    self.purge()
    self.ajouteGauche(Button(u"Nouvelle planète", self.gui.nouvellePlanete, width=190))
    
    cpt = 0
    for fich in os.listdir(os.path.join(".", "data", "planetes")):
      if fich.endswith(".pln"):
        cpt+=1
    if cpt==0:
      self.ajouteGauche(Label(u"Utiliser un planète vierge", width=190))
    else:
      self.ajouteGauche(Button(u"Utiliser un planète vierge", self.gui.planeteVierge, width=190))
    
    cpt = 0
    for fich in os.listdir(os.path.join(".", "sauvegardes")):
      if fich.endswith(".pln"):
        cpt+=1
    if cpt==0:
      self.ajouteGauche(Label(u"Charger une partie", width=190))
    else:
      self.ajouteGauche(Button(u"Charger une partie", self.gui.chargerPartie, width=190))

    self.ajouteGauche(Button(u"Configuration", self.gui.configurer, width=190))
    self.fabrique()
    
class MenuConfiguration(MenuCirculaire):
  """Le menu de configuration"""
  
  select = u"affichage"
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.fabrique()
    
  def fabrique(self):
    self.select = self.select.lower()
    
    self.purge()
    
    btn = self.ajouteGauche(PictureRadio("rtheme/twotone/gear-over.png", "rtheme/twotone/gear.png", u"Affichage"))
    btn.callback = self.clic
    if self.select == u"affichage":
      btn.style = "CHECKON"
      btn.value = True
      
      btnD = self.ajouteDroite(Label(u"Résolution : "+general.configuration.getConfiguration("affichage-general", "resolution","640 480")))
      btnD = self.ajouteDroite(Check(u"Bloom"))
      if general.configuration.getConfiguration("affichage-effets", "utiliseBloom","0")=="1":
        btnD.style = "CHECKON"
        btnD.value = True
    btn = self.ajouteGauche(PictureRadio("rtheme/twotone/move-over.png", "rtheme/twotone/move.png", u"Contrôles"))
    btn.callback = self.clic
    if self.select == u"contrôles":
      btn.style = "CHECKON"
      btn.value = True
      touches = general.configuration.getConfigurationClavier()
      for element in touches.keys():
        btnD = self.ajouteDroite(Label(touches[element]+u" : "+element))
    btn = self.ajouteGauche(PictureRadio("rtheme/twotone/radio-off-over.png", "rtheme/twotone/radio-off.png", u"Planètes"))
    btn.callback = self.clic
    if self.select == u"planètes":
      btn.style = "CHECKON"
      btn.value = True
    btn = self.ajouteGauche(PictureRadio("rtheme/twotone/target-over.png", "rtheme/twotone/target.png", u"Debug"))
    btn.callback = self.clic
    if self.select == u"debug":
      btn.style = "CHECKON"
      btn.value = True
    
    MenuCirculaire.fabrique(self)
    
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
    self.select = bouton
    
    
class MenuVierge(MenuCirculaire):
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
    MenuCirculaire.__init__(self, gui)
    
    self.liste=[]
    for element in os.listdir(os.path.join(".", "data", "planetes")):
      if element.endswith(".pln"):
        self.liste.append((element.lower(), element))
    i=0
    for elem in self.liste:
      if i<len(self.liste)/2:
        check = self.ajouteGauche(PictureRadio("rtheme/twotone/news-over.png", "rtheme/twotone/news.png", elem[0].capitalize()))
      else:
        check = self.ajouteDroite(PictureRadio("rtheme/twotone/news-over.png", "rtheme/twotone/news.png", elem[0].capitalize()))
      check.callback = self.clic
      i+=1
      
    self.fabrique()
    
class MenuCharge(MenuCirculaire):
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
    MenuCirculaire.__init__(self, gui)
    
    self.liste=[]
    for element in os.listdir(os.path.join(".", "sauvegardes")):
      if element.endswith(".pln"):
        self.liste.append((element.lower(), element))
    i=0
    for elem in self.liste:
      if i<len(self.liste)/2:
        check = self.ajouteGauche(PictureRadio("rtheme/twotone/diskette-over.png", "rtheme/twotone/diskette.png", elem[0].capitalize()))
      else:
        check = self.ajouteDroite(PictureRadio("rtheme/twotone/diskette-over.png", "rtheme/twotone/diskette.png", elem[0].capitalize()))
      check.callback = self.clic
      i+=1
      
    self.fabrique()
    
class Interface:
  joueur = None
  menuCourant = None
  
  def __init__(self, start):
    #Fabrique le GUI de base
    self.start = start
    self.gui = Gui(theme = rtheme.RTheme())
    #On affiche l'écran de titre
    self.menuCourant = MenuPrincipal(self)
    #On place un bouton quitter en haut à droite de l'écran
    self.quit = self.gui.add(Icon("rtheme/twotone/x.png", x="right", y="top"))
    self.quit.onClick = sys.exit
    taskMgr.add(self.ping, "Boucle GUI", 10)
    
  def add(self, pouet):
    return self.gui.add(pouet)
    
  def remove(self, pouet):
    return self.gui.remove(pouet)
    
  def ping(self, task):
    if self.menuCourant!=None:
      self.menuCourant.MAJ()
    return task.cont
    
  def changeMenuVers(self, classe):
    if self.menuCourant != None:
      self.menuCourant.efface()
      if classe != None:
        self.menuCourant = classe(self)
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
    self.informations = self.gui.add(Informations(self))
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
    self.menuCourant = EnJeu(self)
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
      self.informations.ajouteTexte(type, texte)
        
    if forceRefresh:
      #On force le recalcul du GUI
      self.gui._doMouse()
      self.gui._doDrag()
      self.gui._reSize()
      self.gui._layout()
      self.gui._draw()
      #On force le rendu
      base.graphicsEngine.renderFrame()
    