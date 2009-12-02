#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandac.PandaModules import *

import sys
import general
import math

from inout import IO

import treegui
from treegui.components import *
from treegui.widgets import *
from treegui.core import Gui
import rtheme
import os

PAD = 4 #Taille de l'espace entre les composants
HAUTEUR_BOUTON = 28 #Hauteur d'un bouton
LARGEUR_BOUTON = 190 #Largeur d'un bouton
HAUTEUR_CHECK = 15 #Hauteur d'une checkbox
HAUTEUR_TEXTE = 15 #Hauteur d'une ligne de texte
TAILLE_ICONE = 15 #Hauteur==Largeur d'une icone
TEMPS_ICONE = 30.0 #Durée durant laquelle une icone reste affichée à l'écran

class InfoBulle(Pane):
  """Zone de texte qui disparait après un certain temps"""
  def __init__(self, gui, message, timeout, x, y, callback=None):
    """
    gui : l'instance de la classe Interface en cours d'utilisation
    message : le message à afficher
    timeout : la durée après laquelle l'infobulle doit disparaitre
    x,y : la position de l'infobulle à l'écran
    callback : la fonction à appeler une fois que la bulle disparait
    """
    Pane.__init__(self)
    #Crée le label
    label = self.add(Label(message))
    #Positionne et dimentionne le fond de la bulle
    self.width, self.height = label.getSize(gui.gui)
    self.x, self.y = x, y
    
    #La fonction de fin
    if callback != None:
      self.callback = callback
      
    #La fonction qui va supprimer l'infobulle une fois le timeout passé
    taskMgr.doMethodLater(timeout, self.exit, 'effaceInfoBulle')
    
  def exit(self, task=None):
    """
    Fonction qui détruit l'infobulle
    task : paramètre renvoyé par taskMgr
    """
    self.parent.remove(self)
    self.callback()
    if task!=None:
      return task.done
    
  def callback(self):
    """Cette fonction est appelée quand la bulle est détruite"""
    pass
    
class MenuCirculaire:
  """Affiche des boutons positionnés sur un anneau"""
  boutons = None #Liste des instances de boutons
  composants = None #Liste des instances de boutons (utilisé pour l'animation)
  retour = None #Un bouton qui ramène au menu précédent
  besoinRetour = True #Si True, alors de l'appel à fabrique un bouton ramenant au menu précédent sera crée
  angleOuverture = None #L'angle sur lequel les boutons s'étalent (en degrés)
  
  animation = None #La position actuelle dans l'animation (en degrés)
  directionAnimation = None #si <0 les boutons s'éloignent, si >0 les boutons se resserent et si ==0, pas d'animation
  exit = None #La classe de menu à produire quand on quitte
  exiting = None #Si True, alors se menu est en cours de destruction
  
  lastDraw = None #Heure à laquelle on a affiché le menu en dernier
  
  def __init__(self, gui):
    """gui: l'instance de Interface en cours d'utilisation"""
    self.gui = gui
    #Par défaut les boutons s'étalent sur 120°
    self.angleOuverture = 120.0
    self.animation = 120.0
    self.directionAnimation = -1
    self.exiting = False
    self.boutons=[[],[]]
    self.composants = []
    self.lastDraw = None
    
  def ajouteGauche(self, bouton):
    """Ajoute un bouton dans la colonne de gauche"""
    self.boutons[0].append(bouton)
    return bouton
    
  def ajouteDroite(self, bouton):
    """Ajoute un bouton dans la colonne de droite"""
    self.boutons[1].append(bouton)
    return bouton

  def cercle(self, centre, rayon, angleOuverture, nbelemsG, nbelemsD):
    """
    Calcul les positions des boutons à placer sur le cercle
    centre : le centre du cercle
    rayon : le rayon du cercle
    angleOuverture : l'angle sur lequel les boutons l'étalent
    nbelemS, bnelemsD : le nombre d'éléments dans la colonne de gauche / de droite
    """
    elements = [[],[]]
    rayon=abs(rayon)
    if nbelemsG==1:
      angleG=angleOuverture
    else:
      angleG = abs(float(angleOuverture)/(nbelemsG-1))
    if nbelemsD==1:
      angleD=angleOuverture
    else:
      angleD = abs(float(angleOuverture)/(nbelemsD-1))
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
        
    return elements

  def anime(self, temps):
    """Déplacent les boutons selon l'heure pour produire l'animation"""
    self.animation += self.directionAnimation * temps * 75
    
    if self.animation<0:
      self.animation=0.0
    if self.animation>120:
      self.animation=120.0
      if self.exit != None:
        self.clear()
        self.gui.menuCourant = self.exit(self.gui)

    bg, bd = self.boutons
    nbBoutonsG = len(bg)
    nbBoutonsD = len(bd)
    coords = self.cercle(self.getCentre(), self.getRayon(), self.angleOuverture-abs(self.animation), nbBoutonsG, nbBoutonsD)
    for composant, indice, cote in self.composants:
      x, y = coords[cote][indice]
      composant.doPlacement({"x":x, "y":y, "width":composant.width})
    
  def getCentre(self):
    """Retourne le centre de la fenêtre"""
    return (base.win.getXSize()/2,base.win.getYSize()/2)
    
  def getRayon(self):
    """Retourne le rayon maximal qui peut être obtenu pour cette taille de fenêtre"""
    return min(base.win.getXSize()/2 - LARGEUR_BOUTON, base.win.getYSize()/2 - HAUTEUR_BOUTON)
    
  def fabrique(self):
    """Construit le menu et l'affiche"""
    bg, bd = self.boutons
    self.composants = []
    nbBoutonsG = len(bg)
    nbBoutonsD = len(bd)
    
    i=0
    for i in range(0, max(nbBoutonsG, nbBoutonsD)):
      if i<len(bg):
        bouton = bg[i]
        bouton.width = 190
        self.gui.gui.add(bouton)
        self.composants.append((bouton, i, 0))
      
      if i<len(bd):
        bouton = bd[i]
        bouton.width = 190
        self.gui.gui.add(bouton)
        self.composants.append((bouton, i, 1))
      i+=1
      
    if self.besoinRetour:
      self.retour = self.gui.add(Icon("rtheme/twotone/rotate_node.png", x="center", y="bottom"))
      self.retour.onClick = self.back
    else:
      self.retour = None
      
    self.anime(0.0)
    
  def MAJ(self, temps):
    """Met à jour l'affichage"""
    if self.lastDraw == None:
      self.lastDraw = temps
      
    tps = temps - self.lastDraw
    self.lastDraw = temps
    
    self.anime(tps)
    
  def efface(self, cible):
    """
    Lance l'animation de repliage du menu
    cible : la classe du menu qui sera produite après la disparition complète (si None, quitte sans animation)
    """
    self.directionAnimation = 1.0
    self.exit = cible
    if cible==None:
      self.animation = 120.0
      self.clear()

  def remove(self, composant):
    """Retire un bouton du menu"""
    cible = None
    for bouton, indice, cote in self.composants:
      if composant == bouton:
        self.gui.remove(bouton)
        cible = bouton, indice, cote
    if cible!=None:
      self.composants.remove(cible)
    while self.boutons[0].count(composant)>0:
      self.boutons[0].remove(composant)
    while self.boutons[1].count(composant)>0:
      self.boutons[1].remove(composant)
    self.fabrique()
      
  def clear(self):
    """Supprime tous les composants"""
    for bouton, indice, cote in self.composants:
      self.gui.remove(bouton)
      
    if self.retour!=None:
      self.gui.remove(self.retour)
      
    self.boutons = [[],[]]
    self.composants = []
    self.retour = None
    return True
      
  def back(self):
    """Retourne au menu précédent"""
    self.gui.changeMenuVers(MenuPrincipal)
    
class Historique(MenuCirculaire):
  """Affiche les messages sous forme d'icones s'empilant sur le coté droit de l'écran"""
  messages = None
  
  #Liste des icones pour chaque type de message
  icones = {
  "inconnu":"rtheme/twotone/q.png",
  "mort":"rtheme/twotone/skull.png",
  "chat":"rtheme/twotone/phone.png",
  "obscurite":"rtheme/twotone/clock.png",
  "info":"rtheme/twotone/info.png",
  "avertissement":"rtheme/twotone/caution.png",
  "sauvegarde":"rtheme/twotone/diskette.png"
  }
  
  def __init__(self, gui):
    self.messages = []
    MenuCirculaire.__init__(self, gui)
    self.besoinRetour = False
    self.fabrique()
  
  def ajouteMessage(self, type, message, position=None):
    """
    Ajoute un nouveau message
    type : le type de message (voir self.icones)
    message : le contenu du message
    position : le point au dessus duquel la caméra doit aller lors d'un clic sur l'icône
    """
    self.messages.append((TEMPS_ICONE, type, message, self.ajouteDroite(self.fabriqueMessage(type, message))))
    if position!=None:
      self.messages[-1][3].callback = self.gui.io.placeCameraAuDessusDe
      self.messages[-1][3].callbackParams = {"point":position}
    self.fabrique()
    
  def fabriqueMessage(self, type, message):
    """
    Construit un composant pour le message
    type : le type de message (voir self.icones)
    message : le message associé
    """
    if type not in self.icones.keys():
      type="inconnu"
    return Icon(self.icones[type])
    
  def MAJ(self, temps):
    """Gère la pulsation des icones et supprime les icones périmées"""
    if self.lastDraw == None:
      self.lastDraw = temps
      
    tps = temps - self.lastDraw
    aVirer = []
        
    for i in range(0, len(self.messages)):
      restant, type, message, composant = self.messages[i]
      restant = max(0.0, restant-tps)
      if restant == 0:
        #Composant périmé
        self.remove(composant)
        aVirer.append(self.messages[i])
      else:
        #Fait pulser
        composant.alpha = abs(restant%2-1)
      self.messages[i] = (restant, type, message, composant)
      
    for message in aVirer:
      while self.messages.count(message)>0:
        self.messages.remove(message)
        
    MenuCirculaire.MAJ(self, temps)
    
class MiniMap(Pane):
  """Affiche une carte miniature de la planète"""
  gui = None #l'instance de la classe Interface en cours d'utilisation
  tailleMiniMap = 150 #La taille de la carte en pixels (la carte est carrée)
  points = None #La liste des points à afficher
  blips = None #La liste des composants représentants les points
  echelle = None #Le facteur d'échelle entre le monde réel et la miniCarte
  
  def __init__(self, gui):
    Pane.__init__(self)
    self.gui = gui
    self.echelle = 0.5
    
    #On positionne la carte
    self.x = "right" 
    self.y = "top" 
    self.width = self.tailleMiniMap
    self.height = self.tailleMiniMap
    
    self.points={}
    self.blips={}
    taskMgr.add(self.ping, "Boucle minimap")
    
  def ajoutePoint(self, point, icone):
    """Ajout un point2D à la carte, retourne un indice servant à l'effacer plus tard"""
    if len(point)!=2:
      print "La mini carte n'accepte que des points en 2D !"
      return None
      
    for id, (pointT, iconeT) in self.points.iteritems():
      if pointT==point and iconeT==icone:
        return id
    for i in range(0, len(self.points)):
      if not i in self.points.keys():
        self.points[i]=(point, icone)
        return i
    self.points[len(self.points)+1]=(point, icone)
    return len(self.points)+1
    
  def ajoutePoint3D(self, point, icone):
    """Ajout un point3D à la carte, retourne un indice servant à l'effacer plus tard"""
    #On calcul le point derrière la caméra, super loin
    camNorm = general.normaliseVecteur(self.gui.io.camera.getPos())
    mCam = general.multiplieVecteur(camNorm, self.gui.start.planete.distanceSoleil)
    #On regarde si le point est bien en vue et pas derrière la planète
    if general.ligneCroiseSphere(point, mCam, (0.0,0.0,0.0), 1.0)==None:
      test = NodePath("cam")
      test.reparentTo(self.gui.start.planete.racine)
      test.setPos(*mCam)
      test.lookAt(self.gui.start.planete.racine)
      pt = test.getRelativePoint(self.gui.start.planete.racine, Point3(*point))
      test.detachNode()
      test.removeNode()
      return self.ajoutePoint((pt[0] ,pt[2]), icone)
    else:
      return None
    
  def enlevePoint(self, id):
    """
    Supprime un point de la carte
    id : le résultat produit lors de ajoutePoint ou ajoutePoint3D
    """
    if id==None:
      return
    if id not in self.points.keys():
      print "Erreur, impossible d'effacer le point : point pas sur la carte", id
      return
    del self.points[id]
    if id in self.blips.keys():
      self.remove(self.blips[id])
      del self.blips[id]

  def ping(self, task):
    """Boucle qui met à jour la carte"""
    for id in self.points.keys():
      if id not in self.blips.keys():
        #Ce point n'a pas de représentation sur la carte, on en fabrique un nouveau
        self.blips[id] = self.add(Icon(self.points[id][1],x=self.points[id][0][0]*self.echelle, y=self.points[id][0][1]*self.echelle))
    return task.cont
        
  def changeEchelle(self, nouvelleEchelle):
    """Change l'échelle de la carte"""
    self.echelle = nouvelleEchelle
    for blib in self.blips.values():
      self.remove(blib)
    self.blips = {}
    
class EnJeu(MenuCirculaire):
  """Contient la liste des unitées que l'on peut construire"""
  select = None #L'unité sélctionnée en ce moment
  historique = None #La liste des icones d'information
  miniMap = None #La carte
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.angleOuverture = 80.0
    self.besoinRetour = False
    
    liste=general.configuration.getConfigurationSprite()
    for elem in liste:
      check = self.ajouteGauche(PictureRadio(elem[3], elem[4], elem[0].capitalize(), width=LARGEUR_BOUTON))
      check.alpha = 0.5
      check.style = "DEFAULT"
      check.callback = self.clic
    self.fabrique()
    self.historique = Historique(self.gui)
    self.miniMap = self.gui.gui.add(MiniMap(self.gui))
    
  def anime(self, temps):
    MenuCirculaire.anime(self, temps)
    for composant, indice, cote in self.composants:
      composant.doPlacement({"x":composant.x-composant.width})
    
  def alerte(self, type, message, coord):
    """Ajoute un nouveau message"""
    self.historique.ajouteMessage(type, message, coord)
    self.gui.informations.ajouteTexte(type, message)
 
  def clic(self, bouton, etat):
    """
    On a cliqué sur un bouton de construction d'unité
    bouton : le texte du bouton
    etat : si True alors le bouton est actif (ce devrait toujours être le cas de figure)
    """
    self.select = bouton.lower()
    
  def MAJ(self, temps):
    self.historique.MAJ(temps)
    MenuCirculaire.MAJ(self, temps)
    
  def clear(self):
    self.historique.clear()
    #Purge tous les points de la carte
    self.miniMap.changeEchelle(0.0)
    self.gui.gui.remove(self.miniMap)
    MenuCirculaire.clear(self)
        

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
  "obscurite":"rtheme/twotone/clock.png",
  "avertissement":"rtheme/twotone/caution.png",
  "sauvegarde":"rtheme/twotone/diskette.png"
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
    
class MenuPrincipal(MenuCirculaire):
  """Le menu principal"""
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.besoinRetour = False
    
    self.ajouteGauche(Button(u"Nouvelle planète", self.gui.nouvellePlanete, width=LARGEUR_BOUTON))
    
    cpt = 0
    for fich in os.listdir(os.path.join(".", "data", "planetes")):
      if fich.endswith(".pln"):
        cpt+=1
    if cpt==0:
      self.ajouteGauche(Label(u"Utiliser un planète vierge", width=LARGEUR_BOUTON))
    else:
      self.ajouteGauche(Button(u"Utiliser un planète vierge", self.gui.planeteVierge, width=LARGEUR_BOUTON))
    
    cpt = 0
    for fich in os.listdir(os.path.join(".", "sauvegardes")):
      if fich.endswith(".pln"):
        cpt+=1
    if cpt==0:
      self.ajouteGauche(Label(u"Charger une partie", width=LARGEUR_BOUTON))
    else:
      self.ajouteGauche(Button(u"Charger une partie", self.gui.chargerPartie, width=LARGEUR_BOUTON))

    self.ajouteGauche(Button(u"Configuration", self.gui.configurer, width=LARGEUR_BOUTON))
    self.fabrique()
    
  def anime(self, temps):
    MenuCirculaire.anime(self, temps)
    for composant, indice, cote in self.composants:
      composant.doPlacement({"x":composant.x-composant.width})
    
class MenuConfiguration(MenuCirculaire):
  """Le menu de configuration"""
  
  select = None
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.changeMenu(u"affichage")
    
  def changeMenu(self, select):
    self.select = select.lower()
    self.directionAnimation = -1.0
    self.clear()
    
    btn = self.ajouteGauche(PictureRadio("rtheme/twotone/gear-over.png", "rtheme/twotone/gear.png", u"Affichage", width=LARGEUR_BOUTON))
    btn.callback = self.clic
    if self.select == u"affichage":
      btn.style = "CHECKON"
      btn.value = True
      
      btnD = self.ajouteDroite(Label(u"Résolution : "+general.configuration.getConfiguration("affichage-general", "resolution","640 480"), width=LARGEUR_BOUTON))
      btnD = self.ajouteDroite(Check(u"Bloom", width=LARGEUR_BOUTON))
      if general.configuration.getConfiguration("affichage-effets", "utiliseBloom","0")=="1":
        btnD.style = "CHECKON"
        btnD.value = True
    btn = self.ajouteGauche(PictureRadio("rtheme/twotone/move-over.png", "rtheme/twotone/move.png", u"Contrôles", width=LARGEUR_BOUTON))
    btn.callback = self.clic
    if self.select == u"contrôles":
      btn.style = "CHECKON"
      btn.value = True
      touches = general.configuration.getConfigurationClavier()
      for element in touches.keys():
        btnD = self.ajouteDroite(Label(touches[element]+u" : "+element))
    btn = self.ajouteGauche(PictureRadio("rtheme/twotone/radio-off-over.png", "rtheme/twotone/radio-off.png", u"Planètes", width=LARGEUR_BOUTON))
    btn.callback = self.clic
    if self.select == u"planètes":
      btn.style = "CHECKON"
      btn.value = True
    btn = self.ajouteGauche(PictureRadio("rtheme/twotone/target-over.png", "rtheme/twotone/target.png", u"Debug", width=LARGEUR_BOUTON))
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
    self.changeMenu(bouton)
    
    
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
        self.gui.chargerPartie2(element[1])
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    
    self.liste=[]
    for element in os.listdir(os.path.join(".", "sauvegardes")):
      if element.endswith(".pln"):
        self.liste.append((element.lower(), element))
    i=0
    for elem in self.liste:
#      if i<len(self.liste)/2:
      check = self.ajouteGauche(PictureRadio("rtheme/twotone/diskette-over.png", "rtheme/twotone/diskette.png", elem[0].capitalize(), width=LARGEUR_BOUTON))
#      else:
#        check = self.ajouteDroite(PictureRadio("rtheme/twotone/diskette-over.png", "rtheme/twotone/diskette.png", elem[0].capitalize(), width=LARGEUR_BOUTON))
      check.callback = self.clic
      i+=1
      
    self.fabrique()
    
class Interface:
  joueur = None
  menuCourant = None
  informations = None
  io = None
  start = None
  
  def __init__(self, start):
    #Fabrique le GUI de base
    self.start = start
    self.gui = Gui(theme = rtheme.RTheme())
    self.io = IO(self)
    #On affiche l'écran de titre
    self.menuCourant = MenuPrincipal(self)
    ##On place un bouton quitter en haut à droite de l'écran
    #self.quit = self.gui.add(Icon("rtheme/twotone/x.png", x="right", y="top"))
    #self.quit.onClick = sys.exit
    taskMgr.add(self.ping, "Boucle GUI", 10)
    
  def add(self, pouet):
    """Racourcis pour gui.gui.add"""
    return self.gui.add(pouet)
    
  def remove(self, pouet):
    """Racourcis pour gui.gui.remove"""
    return self.gui.remove(pouet)
    
  def ping(self, task):
    if self.menuCourant!=None:
      self.menuCourant.MAJ(task.time)
    return task.cont
    
  def changeMenuVers(self, classe):
    """Passe d'un menu à un autre"""
    if self.menuCourant != None:
      self.menuCourant.efface(classe)
      
  def nouvellePlanete(self):
    """Construit une nouvelle planète aléatoirement"""
    self.makeMain()
    self.start.fabriquePlanete(os.path.join(".", "configuration", "planete.cfg"))
    self.start.start()
    
  def makeMain(self):
    """Construit les éléments de l'interface lors du chargement"""
    self.changeMenuVers(None)
    self.informations = self.gui.add(Informations(self))
    self.chargement = self.gui.add(Chargement())
    
  def configurer(self):
    """Passe au menu de configuration"""
    self.changeMenuVers(MenuConfiguration)
    
  def planeteVierge(self):
    """Lance une planète "vierge" """
    self.changeMenuVers(MenuVierge)
    
  def planeteVierge2(self, fichier):
    """Charge un prototype de planète pré-construit"""
    self.makeMain()
    self.start.chargePlanete(os.path.join(".", "data", "planetes", fichier))
    self.start.start()
    
  def chargerPartie(self):
    """Charge un partie sauvegardée"""
    self.changeMenuVers(MenuCharge)
    
  def chargerPartie2(self, fichier):
    """Charge une partie en cours"""
    self.makeMain()
    self.start.chargePlanete(os.path.join(".", "sauvegardes", fichier))
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
      if self.informations !=None:
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
