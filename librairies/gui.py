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
from treegui.customwidgets import *
from treegui.core import Gui
import theme
import os
import zipfile

PAD = 4 #Taille de l'espace entre les composants
HAUTEUR_BOUTON = 28 #Hauteur d'un bouton
LARGEUR_BOUTON = 190 #Largeur d'un bouton
HAUTEUR_CHECK = 15 #Hauteur d'une checkbox
HAUTEUR_TEXTE = 15 #Hauteur d'une ligne de texte
TAILLE_ICONE = 15 #Hauteur==Largeur d'une icone

class Console(Pane):
  """Une console qui permet d'exécuter du code python sans quitter l'appli"""
  style = "default"
  commandes = []
  lignes = []
  
  def __init__(self):
    Pane.__init__(self)
    self.ligne1 = self.add(Label(general.i18n.getText("Ligne %i") %1, x=PAD, y=PAD*1+HAUTEUR_TEXTE*0))
    self.ligne2 = self.add(Label(general.i18n.getText("Ligne %i") %2, x=PAD, y=PAD*2+HAUTEUR_TEXTE*1))
    self.ligne3 = self.add(Label(general.i18n.getText("Ligne %i") %3, x=PAD, y=PAD*3+HAUTEUR_TEXTE*2))
    self.ligne4 = self.add(Label(general.i18n.getText("Ligne %i") %4, x=PAD, y=PAD*4+HAUTEUR_TEXTE*3))
    self.texte = self.add(EntryHistory(general.i18n.getText("Texte..."), x=PAD, y=PAD*5+HAUTEUR_TEXTE*4, width="100%"))
    #On positionne la Form
    self.x = "left" 
    self.y = "top" 
    self.width = "100%"
    self.height = PAD*7+HAUTEUR_TEXTE*5
    self.texte.onEnter = self.execute
    self.texte.history = self.history
    self.positionHistorique = 0
    
  def history(self, mouvement):
    self.positionHistorique=self.positionHistorique+mouvement
    self.positionHistorique = min(self.positionHistorique, len(self.commandes))
    self.positionHistorique = max(0, self.positionHistorique)
    if self.positionHistorique == len(self.commandes):
      return ""
    return self.commandes[self.positionHistorique]
    
  def macros(self, texte):
    texte = texte.replace("_g_", "general")
    texte = texte.replace("_getConf_", "general.configuration.getConfiguration")
    texte = texte.replace("_setConf_", "general.configuration.setConfiguration")
    texte = texte.replace("_\\n_", "\n")
    return texte
    
  def execute(self, texte):
    texte = self.macros(texte)
    self.ligne1.text = self.ligne3.text
    self.ligne2.text = self.ligne4.text
    self.ligne3.text = texte
    try:
      test=eval(texte)
    except Exception, e:
      test=str(e)
    self.ligne4.text = ">>> "+str(test)
    self.commandes.append(texte)
    self.positionHistorique=len(self.commandes)
    self.lignes.append(texte)
    self.lignes.append(">>> "+str(test))
    
  def efface(self):
    pass
    
class MenuCirculaire:
  """Affiche des boutons positionnés sur un anneau"""
  boutons = None #Liste des instances de boutons
  composants = None #Liste des instances de boutons (utilisé pour l'animation)
  retour = None #Un bouton qui ramène au menu précédent
  besoinRetour = True #Si True, alors de l'appel à fabrique un bouton ramenant au menu précédent sera crée
  angleOuverture = None #L'angle sur lequel les boutons s'étalent (en degrés)
  decalageOuverture = None
  
  animation = None #La position actuelle dans l'animation (en degrés)
  vitesseAnimation = None #Le nombre de degrés par seconde à parcourir
  directionAnimation = None #si <0 les boutons s'éloignent, si >0 les boutons se resserent et si ==0, pas d'animation
  exit = None #La classe de menu à produire quand on quitte
  exiting = None #Si True, alors se menu est en cours de destruction
  
  dureeMessage = None #Le temps durant lequel on garde un message à l'écran
  
  lastDraw = None #Heure à laquelle on a affiché le menu en dernier
  
  miniMap = None
  
  def __init__(self, gui):
    """gui: l'instance de Interface en cours d'utilisation"""
    self.gui = gui
    #Par défaut les boutons s'étalent sur 120°
    self.angleOuverture = 80.0
    self.decalageOuverture = 0.0
    self.animation = 80.0
    self.directionAnimation = -1
    self.exiting = False
    self.boutons=[[],[],[],[]]
    self.composants = []
    self.lastDraw = None
    self.vitesseAnimation = general.configuration.getConfiguration("affichage", "General", "vitesseAnimationMenus", "75.0", float)
    self.dureeMessage = general.configuration.getConfiguration("affichage", "General", "dureeMessage", "30.0", float)
    
  def ajouteGauche(self, bouton):
    """Ajoute un bouton dans la colonne de gauche"""
    self.boutons[0].append(bouton)
    return bouton
    
  def ajouteDroite(self, bouton):
    """Ajoute un bouton dans la colonne de droite"""
    self.boutons[1].append(bouton)
    return bouton

  def ajouteHaut(self, bouton):
    """Ajoute un bouton dans la colonne du haut"""
    self.boutons[2].append(bouton)
    return bouton
    
  def ajouteBas(self, bouton):
    """Ajoute un bouton dans la colonne du bas"""
    self.boutons[3].append(bouton)
    return bouton
    
  def cercle(self, rayon, centre, angleOuvertureCercle, angleOuvertureElipse, boutons):
    """Calcul les positions des boutons à placer sur le cercle"""
    elements = [[],[],[],[]]
    bg, bd, bh, bb = boutons
    rayon=abs(rayon[0]), abs(rayon[1])
    
    ratio = float(centre[0])/float(centre[1])
    
    def calculAngles(taille, angleOuverture):
      """Calcul l'angle entre 2 éléments (a) et l'angle à partir duquel on dessine (b)"""
      a=0.0
      b=0.0
      if taille>1:
        a = angleOuverture/(taille-1)
        b = -angleOuverture/2
      else:
        a = angleOuverture
        b = 0.0
      return a, b
        
    anglebg, angleObg = calculAngles(len(bg), angleOuvertureCercle)
    anglebd, angleObd = calculAngles(len(bd), angleOuvertureCercle)
    anglebh, angleObh = calculAngles(len(bh), angleOuvertureElipse)
    anglebb, angleObb = calculAngles(len(bb), angleOuvertureElipse)
      
    def calculPosition(rayon, centre, angle, ratio):
      """Calcul la valeur en x,y du point sur l'elipse decrite"""
      x = rayon[0]*math.cos(angle/180*math.pi)*ratio
      y = rayon[1]*math.sin(angle/180*math.pi)
      return (centre[0]+x, centre[1]+y)
      
    #On calcul l'angle de chaque objet et sa position
    for i in range(0, max(len(bg), len(bd), len(bh), len(bb))):
      if i<len(bg):
        angle = 180.0 + angleObg + anglebg*i + self.decalageOuverture
        position = calculPosition(rayon, centre, angle, 1.0)
        taille = boutons[0][i].width, boutons[0][i].height
        elements[0].append((position[0], position[1]-taille[1]/2))
      if i<len(bd):
        angle = angleObd + anglebd*i + self.decalageOuverture
        position = calculPosition(rayon, centre, angle, 1.0)
        taille = boutons[1][i].width, boutons[1][i].height
        elements[1].append((position[0]-taille[0]-PAD, position[1]-taille[1]/2))
      if i<len(bh):
        angle = 270.0 + angleObh + anglebh*i - self.decalageOuverture
        position = calculPosition(rayon, centre, angle, ratio)
        taille = boutons[2][i].width, boutons[2][i].height
        elements[2].append((position[0]-taille[0]/2, position[1]))
      if i<len(bb):
        angle = 90.0 + angleObb + anglebb*i + self.decalageOuverture
        position = calculPosition(rayon, centre, angle, ratio)
        taille = boutons[3][i].width, boutons[3][i].height
        elements[3].append((position[0]-taille[0]/2, position[1]-taille[1]-PAD - general.interface.tooltip.height-PAD))
        
    elements[0].reverse()
    elements[1].reverse()
    elements[2].reverse()
    elements[3].reverse()
    return elements

  def anime(self, temps):
    """Déplacent les boutons selon l'heure pour produire l'animation"""
    self.animation += self.directionAnimation * temps * self.vitesseAnimation
    
    if self.animation<0:
      self.animation=0.0
    if self.animation>80:
      self.animation=80.0
      if self.exit != None:
        self.clear()
        if isinstance(self.gui.menuCourant, EnJeu):
          self.gui.menuCourant.listeCommandes = self.exit(self.gui)
        else:
          self.gui.menuCourant = self.exit(self.gui)

    coords = self.cercle(self.getRayon(), self.getCentre(), self.angleOuverture-abs(self.animation), self.angleOuverture-abs(self.animation), self.boutons)
    
    for composant, indice, cote in self.composants:
      if indice<len(coords[cote]):
        x, y = coords[cote][indice]
        composant.doPlacement({"x":x, "y":y, "width":composant.width})
    
  def getCentre(self):
    """Retourne le centre de la fenêtre"""
    return (base.win.getXSize()/2,base.win.getYSize()/2)
    
  def getRayon(self):
    """Retourne le rayon maximal qui peut être obtenu pour cette taille de fenêtre"""
    return (base.win.getXSize()/2, base.win.getYSize()/2)
    
  def fabrique(self):
    """Construit le menu et l'affiche"""
    if self.besoinRetour:
      self.retour = self.ajouteBas(Icon("icones/rotate_node.png", x="center", y="bottom"))
      self.retour.onClick = self.back
    else:
      self.retour = None

    bg, bd, bh, bb = self.boutons
    self.composants = []
    nbBoutonsG = len(bg)
    nbBoutonsD = len(bd)
    nbBoutonsH = len(bh)
    nbBoutonsB = len(bb)
    
    i=0
    for i in range(0, max(nbBoutonsG, nbBoutonsD, nbBoutonsH, nbBoutonsB)):
      if i<len(bg):
        bouton = bg[i]
        #bouton.width = 190
        self.gui.gui.add(bouton)
        self.composants.append((bouton, i, 0))
      
      if i<len(bd):
        bouton = bd[i]
        #bouton.width = 190
        self.gui.gui.add(bouton)
        self.composants.append((bouton, i, 1))

      if i<len(bh):
        bouton = bh[i]
        #bouton.width = 190
        self.gui.gui.add(bouton)
        self.composants.append((bouton, i, 2))
        
      if i<len(bb):
        bouton = bb[i]
        #bouton.width = 190
        self.gui.gui.add(bouton)
        self.composants.append((bouton, i, 3))
      i+=1
      
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
      self.animation = 80.0
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
    while self.boutons[2].count(composant)>0:
      self.boutons[2].remove(composant)
    while self.boutons[3].count(composant)>0:
      self.boutons[3].remove(composant)
    self.anime(0.0)
      
  def clear(self):
    """Supprime tous les composants"""
    for bouton, indice, cote in self.composants:
      self.gui.remove(bouton)
      
    self.boutons = [[],[],[],[]]
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
  None:None,
  "inconnu": "icones/q.png",
  "mort": "icones/skull.png",
  "ai": "icones/reinforcement.png",
  "carte": "icones/stealth2.png",
  "construction": "icones/armor1.png",
  "chat": "icones/phone.png",
  "obscurite": "icones/clock.png",
  "info": "icones/info.png",
  "avertissement": "icones/caution.png",
  "sauvegarde": "icones/diskette.png"
  }
  
  def __init__(self, gui):
    self.messages = []
    MenuCirculaire.__init__(self, gui)
    self.angleOuverture = 80.0
    self.besoinRetour = False
    self.fabrique()
  
  def ajouteMessage(self, type, message, position=None):
    """
    Ajoute un nouveau message
    type : le type de message (voir self.icones)
    message : le contenu du message (doit être passé à getText avant !)
    position : le point au dessus duquel la caméra doit aller lors d'un clic sur l'icône
    """
    self.animation = 0
    self.tailleHistorique = 10
    self.messages.append((self.dureeMessage, type, message, self.ajouteBas(self.fabriqueMessage(type, message))))
    general.interface.tip(self.icones.get(type, self.icones["inconnu"]), message)
    deb = self.messages[:-self.tailleHistorique]
    for message in deb:
      self.remove(message[3])
    self.messages = self.messages[-self.tailleHistorique:]
    #self.clear()
    #for msg in self.messages:
    #  self.ajouteBas(self.fabriqueMessage(msg[1], msg[2], compact=True))
      
    if position!=None:
      self.messages[-1][3].callback = general.io.placeCameraAuDessusDe
      self.messages[-1][3].callbackParams = {"point":position}
    self.fabrique()
    
  def fabriqueMessage(self, type, message):
    """
    Construit un composant pour le message
    type : le type de message (voir self.icones)
    message : le message associé
    """
    if type not in self.icones.keys():
      general.TODO("Il manque l'icone "+type+" pour l'affichage des message")
      type="inconnu"
    cmp = Icon(self.icones[type], width=LARGEUR_BOUTON)
    cmp.tooltip = message
    cmp.__onHover__ = cmp.onHover
    cmp.onHover = general.interface.hover
    return cmp
    
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
        composant.color = (composant.color[0], composant.color[1], composant.color[2], abs(restant%2-1))
      self.messages[i] = (restant, type, message, composant)
      
    for message in aVirer:
      while self.messages.count(message)>0:
        self.messages.remove(message)
        
    MenuCirculaire.MAJ(self, temps)
    
  def clear(self):
    for restant, type, message, composant in self.messages:
      self.remove(composant)
    MenuCirculaire.clear(self)
    
class FondCarte:
  carte = None
  image = None
  
  def __init__(self, tailleX, tailleY):
    #La zone où on affiche l'image:
    cardMaker = CardMaker('sprite')
    cardMaker.setFrame(0.0, 1.0, 0.0, 1.0)
    cardMaker.setHasNormals(True)
    #Construit une carte (un plan)
    self.node = NodePath("node")
    self.node.reparentTo(render2d)
    self.carte = self.node.attachNewNode(cardMaker.generate())
    self.tailleX, self.tailleY = tailleX, tailleY
    self.carte.setScale(self.tailleX, 1.0, self.tailleY)
    self.carte.setPos(0.0, 0.0, 0.0)
    texture = loader.loadTexture("./theme/centre.png")
    self.setImage(texture)
    taskMgr.add(self.resize,"resize",20)
    taskMgr.add(self.draw,"draw",40)
    self.resize(None)
    self.draw(None)
    
  def clear(self):
    self.node.detachNode()
    self.node.removeNode()
    self.node = None
    self.carte = None
  
  def resize(self, task):
    """ resize the window via panda3d internal events"""
    if not self.node:
      return task.done
      
    self.windowsize = base.win.getXSize(),base.win.getYSize()
    self.size = Vec2(*self.windowsize)
    self.aspect  = float(self.windowsize[0]) / float(self.windowsize[1])         
    self.node.setScale(2./base.win.getXSize(), 1, -2./base.win.getYSize())
    self.node.setPos(-1, 0, 1)
    self.node.reparentTo(render2d)    
    self.carte.setPos(self.size[0]-self.tailleX, 0.0, 0.0)
    if task!=None:
      return task.cont
    
  def draw(self, task=None):
    """ resize the window via panda3d internal events"""
    if not self.carte:
      return task.done
      
    if self.image!=None:
      self.carte.setTexture(self.image)
    if task!=None:
      return task.cont
    
  def setImage(self, image):
    self.image = image

class MiniMap(Pane):
  """Affiche une carte miniature de la planète"""
  gui = None #l'instance de la classe Interface en cours d'utilisation
  tailleMiniMapX = None #La taille de la carte en pixels (la carte est carrée)
  tailleMiniMapY = None #La taille de la carte en pixels (la carte est carrée)
  points = None #La liste des points à afficher
  blips = None #La liste des composants représentants les points
  
  camBlip = None #Le blip laissé par la caméra
  
  derniereMAJ = None #l'heure de la dernière MAJ
  carteARedessiner = None #vaut True si la carte a été modifiée
  carteSoleilARedessiner = None #vaut True si la zone d'ombre a été modifiée
  
  carte = None

  def __init__(self, gui):
    Pane.__init__(self)
    self.gui = gui
    
    #On positionne la carte
    self.x = "right" 
    self.y = "top"
    self.style = "VIDE"
    
    #On charge les préférences utilisateur
    self.tailleMiniMapX, self.tailleMiniMapY = general.configuration.getConfiguration("affichage", "Minimap", "taille", "256 256", str).split(" ")
    self.tailleMiniMapX, self.tailleMiniMapY = float(self.tailleMiniMapX), float(self.tailleMiniMapY)
    #Force la carte à une puissance de 2
    self.tailleMiniMapX = 2**int(math.log(self.tailleMiniMapX, 2)+0.5)
    self.tailleMiniMapY = 2**int(math.log(self.tailleMiniMapY, 2)+0.5)
    
    self.width = self.tailleMiniMapX
    self.height = self.tailleMiniMapY
    
    self.points={}
    self.blips={}
    
    self.derniereMAJ = None
    self.carteARedessiner = True
    self.carteSoleilARedessiner = True
    
    self.carte = FondCarte(self.tailleMiniMapX, self.tailleMiniMapY)
    
    taskMgr.add(self.ping, "Boucle minimap")
    
  def onClick(self):
    general.io.placeCameraAuDessusDe(general.cartographie.carteVersPoint3D(self.souris, (256, 128)))
    
  souris = [-1,-1]
  def mouseEvent(self,event,x,y):
    self.souris=[x,y]
    Pane.mouseEvent(self, event, x, y)
    
  def ajoutePoint(self, point, icone, couleur):
    """Ajout un point2D à la carte, retourne un indice servant à l'effacer plus tard"""
    if point==None:
      print "Point sur un pôle, coordonnées non calculables..."
      return None
    if len(point)!=2:
      print "La mini carte n'accepte que des points en 2D !"
      return None
    
    for id, (pointT, iconeT, couleurT) in self.points.iteritems():
      if pointT==point and iconeT==icone and couleurT==couleur:
        return id
    for i in range(0, len(self.points)):
      if not i in self.points.keys():
        self.points[i]=(point, icone, couleur)
        return i
    self.points[len(self.points)+1]=(point, icone, couleur)
    return len(self.points)
    
  def ajoutePoint3D(self, point, icone, couleur):
    """Ajout un point3D à la carte, retourne un indice servant à l'effacer plus tard"""
    return self.ajoutePoint(general.cartographie.point3DVersCarte(point, (self.tailleMiniMapX, self.tailleMiniMapY)), icone, couleur)
      
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
      if self.blips[id] in self.children:
        self.remove(self.blips[id])
      del self.blips[id]
      
  def majBlip(self, blipid, point, icone, couleur):
    """Change les coordonnées d'un point"""
    point = general.cartographie.point3DVersCarte(point, (self.tailleMiniMapX, self.tailleMiniMapY))
    self.points[blipid]=(point, icone, couleur)
    if blipid in self.blips.keys():
      self.blips[blipid].doPlacement({"x":point[0], "y":point[1]})
      self.blips[blipid].icon = icone
      self.blips[blipid].color = couleur

  textureMiniMap=None
  def ping(self, task):
    """Boucle qui met à jour la carte"""
    if self.textureMiniMap==None or (general.miniMapAchangee and task.time-self.derniereMAJ>1.0):
      if self.textureMiniMap!=None:
        loader.unloadTexture(self.textureMiniMap)
      self.textureMiniMap = loader.loadTexture("data/cache/minimap.png")
      general.miniMapAchangee = False
      self.carte.setImage(self.textureMiniMap)
      
      self.derniereMAJ=task.time
      
    if self.camBlip==None:
      self.camBlip = self.ajoutePoint3D(general.io.camera.getPos(),"icones/camera.png",(1.0, 1.0, 1.0, 1.0))
    else:
      self.majBlip(self.camBlip, general.io.camera.getPos(),"icones/camera.png",(1.0, 1.0, 1.0, 1.0))
    for id in self.points.keys():
      if id not in self.blips.keys():
        #Ce point n'a pas de représentation sur la carte, on en fabrique un nouveau
        self.blips[id] = self.add(Icon(self.points[id][1],x=self.points[id][0][0], y=self.points[id][0][1]))
        self.blips[id].color=self.points[id][2]
        self.blips[id].onClick = self.onClick
    return task.cont
    
  def clear(self):
    Pane.clear(self)
    self.carte.clear()
                
class ListeCommandes(MenuCirculaire):
  select = None #L'unité sélctionnée en ce moment
  liste = None
  dicoUnite = None
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.besoinRetour = False
    self.animation = 0
    self.angleOuverture = 40
    btn = self.ajouteGauche(Label("Hubert Gardaniek"))
    btn.style = "DEFAULT"
    btn.width = LARGEUR_BOUTON
    btn = self.ajouteGauche(Label("Bucheron"))
    btn.style = "DEFAULT"
    btn.width = LARGEUR_BOUTON
    btn = self.ajouteGauche(Label(general.i18n.getText("Vie : %i%%")%72))
    btn.style = "DEFAULT"
    btn.width = LARGEUR_BOUTON
    btn = self.ajouteGauche(Label(general.i18n.getText("Occupation : %s")%"Coupe un arbre"))
    btn.style = "DEFAULT"
    btn.width = LARGEUR_BOUTON
    grp = self.ajouteGauche(Groupe())
    btn = grp.add(Icon("icones/gear.png"))
    btn = grp.add(Icon("icones/move.png"))
    btn = grp.add(Icon("icones/target.png"))
    btn = grp.add(Icon("icones/rangearrow.png"))
    self.fabrique()
    
class ListeUnite(MenuCirculaire):
  select = None #L'unité sélctionnée en ce moment
  liste = None
  dicoUnite = None
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.angleOuverture = 30.0
    self.decalageOuverture = 15
    self.besoinRetour = False
    self.liste = []
    self.dicoUnite = {}
    self.fabrique()
    
  def fabrique(self):
    self.clear()
    if self.dicoUnite:
      for nom in self.dicoUnite.keys():
        groupe = self.ajouteHaut(Groupe())
        liste = self.dicoUnite[nom]
        for icone, couleur, sprite in liste:
          ic = groupe.add(IconButton(icone))
          ic.color = couleur
          ic.callback = self.clic
          ic.callbackParams = {"bouton":sprite.id, "etat":sprite}
    MenuCirculaire.fabrique(self)
           
  def calculDicoUnite(self):
    self.dicoUnite = {}
    for sprite in self.liste:
      courant = self.dicoUnite.get(sprite.definition["nom"], None)
      if courant == None:
        courant = []
      if sprite.vie>=50:
        couleur = (0.5, 1.0, 0.5, 1.0)
      else:
        couleur = (1.0, 0.5, 0.5, 1.0)
      courant.append((sprite.icone, couleur, sprite))
      self.dicoUnite[sprite.definition["nom"]]=courant
            
  def anime(self, temps):
    if self.liste != general.io.selection:
      self.liste = general.io.selection[:]
      self.calculDicoUnite()
      self.fabrique()
    MenuCirculaire.anime(self, temps)

  def clic(self, bouton, etat):
    """
    On a cliqué sur un bouton de construction d'unité
    bouton : le texte du bouton
    etat : si True alors le bouton est actif (ce devrait toujours être le cas de figure)
    """
    #shift + control + clic : déselectionne l'unité sous le curseur
    #control + clic : déselectionne toutes les unités de ce type
    #clic : ne garde que les unités de ce type
    if "control" in general.io.touchesControles:
      if "shift" in general.io.touchesControles:
        general.io.selection.remove(etat)
        self.fabrique()
        return
            
      del self.dicoUnite[etat.definition["nom"]]
    else:
      for cat in self.dicoUnite.keys():
        if cat != etat.definition["nom"]:
          del self.dicoUnite[cat]
    general.io.selection=[]
    for cat in self.dicoUnite.keys():
      for icone, couleur, sprite in self.dicoUnite[cat]:
        general.io.selection.append(sprite)
    self.fabrique()
        

class EnJeu():
  """Contient la liste des unitées que l'on peut construire"""
  listeUnite = None #La liste des icones des unités sélectionnées
  listeCommandes = None
  miniMap = None #La carte
  
  def __init__(self, gui):
    self.gui = gui
    #self.gui.historique = Historique(self.gui)
    self.listeUnite = ListeUnite(self.gui)
    self.listeCommandes = ListeCommandes(self.gui)
    self.miniMap = self.gui.gui.add(MiniMap(self.gui))
    
  def alerte(self, type, message, coord):
    """Ajoute un nouveau message"""
    self.gui.historique.ajouteMessage(type, message, coord)
    
  def MAJ(self, temps):
    self.gui.historique.MAJ(temps)
    self.listeUnite.MAJ(temps)
    self.listeCommandes.MAJ(temps)
    
  def efface(self, classe):
    self.clear()
    self.gui.menuCourant = classe(self.gui)
    
  def clear(self):
    if self.gui.historique !=None:
      self.gui.historique.clear()
    self.listeUnite.clear()
    #Purge tous les points de la carte
    self.miniMap.clear()
    self.listeCommandes.clear()
    self.gui.gui.remove(self.miniMap)
    
  def changeMenu(self):
    if isinstance(self.listeCommandes, ListeCommandes):
      self.gui.changeMenuVers(MenuPrincipal)
    else:
      self.gui.changeMenuVers(ListeCommandes)
        
class Chargement(Pane):
  """
  Bandeau qui dit "chargement..."
  """
  style = "default"
  
  def __init__(self):
    Pane.__init__(self)
    
    self.label = self.add(Label(general.i18n.getText("Chargement en cours..."), x="left", y=PAD))
    
    #On positionne la Form
    self.x = "center" 
    self.y = "center" 
    self.width = "80%"
    self.height = "20px"
    
class MenuPrincipal(MenuCirculaire):
  """Le menu principal"""
  enJeu = None
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.besoinRetour = False
    
    self.enJeu = isinstance(self.gui.menuCourant, EnJeu)
    
    if not self.enJeu:
      self.ajouteGauche(Button(general.i18n.getText(u"Nouvelle planète"), self.gui.nouvellePlanete, width=LARGEUR_BOUTON))
    
    cpt = 0
    for fich in os.listdir(os.path.join(".", "sauvegardes")):
      if fich.endswith(".pln"):
        cpt+=1
    if cpt>0:
      self.ajouteGauche(Button(general.i18n.getText(u"Charger une partie"), self.gui.chargerPartie, width=LARGEUR_BOUTON))
      
    if self.enJeu:
      self.ajouteGauche(Button(general.i18n.getText(u"Sauvegarder la partie"), self.gui.sauvegarderPartie, width=LARGEUR_BOUTON))

    self.ajouteGauche(Button(general.i18n.getText(u"Configuration"), self.gui.configurer, width=LARGEUR_BOUTON))

    if self.enJeu:
      self.ajouteGauche(Button(general.i18n.getText(u"Retour en Jeu"), self.gui.retourJeu, width=LARGEUR_BOUTON))
      self.ajouteGauche(Button(general.i18n.getText(u"Quitter la partie"), self.gui.retourPrincipal, width=LARGEUR_BOUTON))
    if not self.enJeu:
      self.ajouteGauche(Button(general.i18n.getText(u"Quitter le jeu"), self.gui.quitter, width=LARGEUR_BOUTON))
    self.fabrique()
    
class MenuDepuisFichier(MenuCirculaire):
  select = None
  nomMenu = None #Le nom du fichier de menu chargé
  menu = None #La structure de donnée contenant les infos du menu
  
  def __init__(self, menu, gui):
    MenuCirculaire.__init__(self, gui)
    self.nomMenu = menu
    self.menu = general.configuration.chargeMenu(menu)
    
    if self.menu == None:
      print "Erreur : MenuDepuisFichier, menu invalide", self.nomMenu
      self.back()
      return
      
    #On ouvre le menu dans la première section
    self.changeMenu(self.menu[0][2]["nom"])
    
  def changeMenu(self, select, fabrique=True):
    """Affiche le menu à la section "select" """
    
    #On garde une trace de quelle section on affiche en ce moment
    self.select = select.lower()
    
    #On force l'animation dans le sens "ouverture"
    self.directionAnimation = -1.0
    
    #On kicke tous les boutons du menu
    self.clear()
    
    #On parcours les sections
    for nomSection, contenuSection, dicoSection in self.menu:
      #On ajoute les boutons de section
      btn = self.ajouteGauche(PictureRadio(dicoSection["iconeactif"], dicoSection["iconeinactif"], general.i18n.getText(dicoSection["nom"]), width=LARGEUR_BOUTON))
      btn.callback = self.clicSection
      btn.style = "button"
      btn.upStyle = "button"
      btn.overStyle = "button_over"
      btn.downStyle = "button_down"
      btn.tooltip = dicoSection["infobulle"]
      btn.__onHover__ = btn.onHover
      btn.onHover = general.interface.hover

      #On regarde si la section que l'on construit est celle à afficher
      if self.select == dicoSection["nom"].lower().strip():
        #Si c'est le cas, on met à jour l'état actif/inactif du bouton
        btn.callback = self.clicVide
        btn.onClick()
        btn.callback = self.clicSection
        
        #On ajoute les boutons de la section active
        for nomElement, contenuElement in contenuSection:
          #Les booleens passe entre True et False, l'état est indiqué par l'icone active/inactive (attention aux boutons qui n'ont pas d'état actif !)
          if contenuElement["type"] == "bool":
            btn = self.ajouteDroite(PictureRadio(contenuElement["iconeactif"], contenuElement["iconeinactif"], general.i18n.getText(contenuElement["nom"]), width=LARGEUR_BOUTON))
            if contenuElement["valeur"]:
              btn.callback = self.clicVide
              btn.onClick()
            btn.callback = self.clicValeur
            
          #Les int et les float ont des boutons +/-
          elif contenuElement["type"] in ["int", "float"] and "valeurmin" in contenuElement.keys() and "valeurmax" in contenuElement.keys():
            #Le fond du bouton
            btn = self.ajouteDroite(Pane(width=LARGEUR_BOUTON, height=HAUTEUR_BOUTON+HAUTEUR_TEXTE))
            pr = PictureRadio(contenuElement["iconeactif"], contenuElement["iconeinactif"], general.i18n.getText(contenuElement["nom"]))
            btn.add(pr)
            pr.__onHover__ = pr.onHover
            pr.onHover = general.interface.hover
            #Le bouton moins
            pr = IconButton("icones/minus.png", y=HAUTEUR_TEXTE+PAD)
            pr.callbackParams = {"bouton":"moins-"+contenuElement["nom"], "etat":True}
            pr.callback = self.clicValeur
            btn.add(pr)
            pr.__onHover__ = pr.onHover
            pr.onHover = general.interface.hover
            #Le bouton plus
            pr = IconButton("icones/plus.png", y=HAUTEUR_TEXTE+PAD, x=HAUTEUR_TEXTE+PAD)
            pr.callbackParams = {"bouton":"plus-"+contenuElement["nom"], "etat":True}
            pr.callback = self.clicValeur
            btn.add(pr)
            pr.__onHover__ = pr.onHover
            pr.onHover = general.interface.hover
            valeur = 100*(float(contenuElement["valeur"])-float(contenuElement["valeurmin"]))/(float(contenuElement["valeurmax"])-float(contenuElement["valeurmin"]))
            if contenuElement["type"]=="int":
              texte = "%i [%s; %s]" %(float(contenuElement["valeur"]), str(contenuElement["valeurmin"]), str(contenuElement["valeurmax"]))
            else:
              texte = "%.3f [%s; %s]" %(float(contenuElement["valeur"]), str(contenuElement["valeurmin"]), str(contenuElement["valeurmax"]))
            pr = SetterBar(texte, valeur, y=HAUTEUR_TEXTE+PAD*2, x=HAUTEUR_TEXTE*2+PAD*3, width=LARGEUR_BOUTON-PAD*4-HAUTEUR_TEXTE*2, height=10)
            pr.callbackParams = {"bouton":"progr-"+contenuElement["nom"],"etat":valeur}
            pr.callback = self.clicValeur
            #Le texte de la forme "valeur [min;max]"
            #pr = Label(str(contenuElement["valeur"])+" ["+str(contenuElement["valeurmin"])+";"+str(contenuElement["valeurmax"])+"]", y=HAUTEUR_TEXTE+PAD, x=HAUTEUR_TEXTE*2+PAD*2)
            btn.add(pr)
            pr.__onHover__ = pr.onHover
            pr.onHover = general.interface.hover
            
          #Les listes et les labels sont justes affichés sous la forme
          #
          #icone nom
          #      valeur
          else:
            btn = self.ajouteDroite(PictureRadio(contenuElement["iconeactif"], contenuElement["iconeinactif"], general.i18n.getText(contenuElement["nom"])+"\n   "+general.i18n.getText(str(contenuElement["valeur"])), width=LARGEUR_BOUTON))
            btn.callback = self.clicValeur
            
          #On change le style des composant pour avoir un fond de bouton
          btn.style = "button"
          btn.upStyle = "button"
          btn.overStyle = "button_over"
          btn.downStyle = "button_down"
          btn.tooltip = contenuElement["infobulle"]
          btn.__onHover__ = btn.onHover
          btn.onHover = general.interface.hover
      
    if fabrique:
      #On construit les boutons
      MenuCirculaire.fabrique(self)
      
  def clicVide(self, bouton, etat):
    """Une fonction qui ne fait rien, permet de lancer de onClick sans pour autant activer le bouton"""
    pass
      
  def clicSection(self, bouton, etat):
    """Clic sur un bouton de section (colonne de gauche)"""
    #On réinitialise l'animation pour refaire une ouverture de menu
    self.animation = self.angleOuverture
    #On change de section
    self.changeMenu(bouton)

  def clicValeur(self, bouton, etat):
    """Clic sur un bouton de configuration (colonne de droite)"""
    #On ne garde que la première ligne de texte pour les boutons de la forme :
    #blah blah blah\r\n
    #valeur du bouton
    bouton=bouton.split("\n")[0].strip()
    
    #Quand on modifie des valeurs int ou float, on utilise des boutons +/-, attrape les infos de boutons
    #Elles sont passées sous la forme plus-nom_du_bouton et moins-nom_du_bouton
    modificateur = None
    if bouton.startswith("plus-"):
      modificateur = +1
      bouton=bouton[5:]
    elif bouton.startswith("moins-"):
      modificateur = -1
      bouton=bouton[6:]
    elif bouton.startswith("progr-"):
      modificateur = 0
      bouton=bouton[6:]
      
    #On recherche dans la liste des boutons de quel bouton il sagit
    for nomSection, contenuSection, dicoSection in self.menu:
      if self.select == dicoSection["nom"].lower().strip():
        for nomElement, contenuElement in contenuSection:
          if contenuElement["nom"].lower().split("\n")[0].strip()==bouton.lower():
            #On a trouvé le bouton, on extrait le chemin de configuration qui lui correspond
            sect, soussect, clef = contenuElement["chemin"].split("/")
            
            #Les float varient entre valeurMin et valeurMax par pas de 1/20 de l'espace à parcourir
            if contenuElement["type"] == "float":
              delta = (float(contenuElement["valeurmax"])-float(contenuElement["valeurmin"]))/100
              if modificateur!=0:
                nvVal = float(contenuElement["valeur"])+delta*modificateur
              else:
                nvVal = float(etat)/100*(float(contenuElement["valeurmax"])-float(contenuElement["valeurmin"]))+float(contenuElement["valeurmin"])
              if nvVal<float(contenuElement["valeurmin"]):
                nvVal = float(contenuElement["valeurmin"])
              if nvVal>float(contenuElement["valeurmax"]):
                nvVal = float(contenuElement["valeurmax"])
              #Met à jour la configuration
              general.configuration.setConfiguration(sect, soussect, clef, nvVal)
              
            #Les int varient entre valeurMin et valeurMax par pas de 1
            elif contenuElement["type"] == "int":
              if modificateur!=0:
                nvVal = int(float(contenuElement["valeur"]))+modificateur
              else:
                nvVal = int(float(etat)/100*(float(contenuElement["valeurmax"])-float(contenuElement["valeurmin"]))+float(contenuElement["valeurmin"])+0.5)
              
              if nvVal<int(contenuElement["valeurmin"]):
                nvVal = int(contenuElement["valeurmin"])
              if nvVal>int(contenuElement["valeurmax"]):
                nvVal = int(contenuElement["valeurmax"])
              #Met à jour la configuration
              general.configuration.setConfiguration(sect, soussect, clef, nvVal)
              
            #Pour les listes, à chaque clic on passe à l'élément suivant de façon circulaire
            #Si l'élément courant n'est pas dans la liste (modification manuelle du fichier de config)
            #On commence avec l'élément 0
            elif contenuElement["type"] == "liste":
              if contenuElement["valeur"] in contenuElement["valeurs"]:
                idx = contenuElement["valeurs"].index(contenuElement["valeur"])
              else:
                idx=-1 #Element pas dans la liste, on commence à l'indice 0 (-1 +1)
                print contenuElement["valeur"],"n'est pas dans",contenuElement["valeurs"]
              idx+=1
              if idx>=len(contenuElement["valeurs"]):
                idx-=len(contenuElement["valeurs"])
              #Met à jour la configuration
              general.configuration.setConfiguration(sect, soussect, clef, contenuElement["valeurs"][idx])
              
            #Pour les booléens, on inverse leur valeur
            elif contenuElement["type"] == "bool":
              #Met à jour la configuration
              general.configuration.setConfiguration(sect, soussect, clef, str(not contenuElement["valeur"])[0])
              
            #On sauvegarde les changements
            general.configuration.sauve(os.path.join(".","configuration","utilisateur.cfg"))
            #On recharge le menu (pour avoir les nouvelles variables de config à jour)
            self.menu = general.configuration.chargeMenu(self.nomMenu)
            #On reconstruit le menu sans l'animer
            self.changeMenu(self.select)
            return
    print "Pas trouvé", bouton.lower()

class MenuConfigurationPlanete(MenuDepuisFichier):
  """Le menu de configuration de nouvelle planete"""
  
  def __init__(self, gui):
    MenuDepuisFichier.__init__(self, "nouvelleplanete", gui)
    
  def changeMenu(self, select):
    MenuDepuisFichier.changeMenu(self, select, fabrique=False)
    btn = self.ajouteGauche(PictureRadio("icones/plus-over.png", "icones/plus.png", "Go !", width=LARGEUR_BOUTON))
    btn.callback = self.go
    btn.style = "button"
    btn.upStyle = "button"
    btn.overStyle = "button_over"
    btn.downStyle = "button_down"
    MenuCirculaire.fabrique(self)
    
  def go(self, bouton, etat):
    general.interface._nouvellePlanete()

class MenuConfiguration(MenuDepuisFichier):
  """Le menu de configuration"""
  
  def __init__(self, gui):
    if isinstance(gui.menuCourant, EnJeu):
      MenuDepuisFichier.__init__(self, "configuration-enjeu", gui)
    else:
      MenuDepuisFichier.__init__(self, "configuration", gui)
      
    #Ajoute la liste de langue au menu
    self.ajouteListeLangue()
    #On ouvre le menu dans la première section
    self.changeMenu(self.menu[0][2]["nom"])
      
  def ajouteListeLangue(self):
    """Force la liste de langue dans le menu"""
    #On parcours les sections
    for section in self.menu:
      nomSection, contenuSection, dicoSection = section
      #On cherche la section "langues"
      if "langues" == dicoSection["nom"].lower().strip():
        #Prototype de langue
        for element in contenuSection:
          nomElement, contenuElement = element
          if nomElement.lower().strip()=="choixlangue":
            contenuElement["type"]="liste"
            contenuElement["valeurs"]=general.i18n.listeLangues()
          
  def clicValeur(self, bouton, etat):
    """Ajoute la liste de langue à chaque rechargement du menu"""
    MenuDepuisFichier.clicValeur(self, bouton, etat)
    self.ajouteListeLangue()
    self.changeMenu(self.select)
    
class MenuVierge(MenuCirculaire):
  """Contient la liste des planètes vierges que l'on peut charger"""
  style = "default"
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    cmp = self.ajouteHaut(Label("Nouvelle partie"))
    cmp.style = "DEFAULT"
    cmp.width = LARGEUR_BOUTON
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
      #Lecture depuis le zip
      zip = zipfile.ZipFile(os.path.join(".", "sauvegardes",elem[1]), "r")
      if zip.testzip()!=None:
        print "Charge :: Erreur : Fichier de sauvegarde corrompu !"
      data = zip.read(os.path.basename(elem[1]))
      zip.close()
      lignes = data.split("\r\n")

      date = ""
      nomPlanete = ""
      for ligne in lignes:
        if ligne.lower().strip().startswith("details:"):
          type, infos, inutile = ligne.lower().strip().split(":")[1:]
          if type=="datesauvegarde":
            date = infos.replace("-",":")
          elif type=="nomplanete":
            nomPlanete = infos.capitalize()
            
      nom = elem[0].capitalize()
      
      if nomPlanete != "":
        nom = nomPlanete
      if date != "":
        nom += " "+date
            
      check = self.ajouteGauche(PictureRadio("icones/diskette-over.png", "icones/diskette.png", nom, width=LARGEUR_BOUTON))
      check.style = "button"
      check.upStyle = "button"
      check.overStyle = "button_over"
      check.downStyle = "button_down"
      #      else:
#        check = self.ajouteDroite(PictureRadio("icones/diskette-over.png", "icones/diskette.png", elem[0].capitalize(), width=LARGEUR_BOUTON))
      check.callback = self.clic
      i+=1
      
    self.fabrique()
    
class Interface:
  joueur = None
  menuCourant = None
  historique = None
  console = None
  tooltip = None
  rectangleDrag = None
  
  def __init__(self):
    #Fabrique le GUI de base
    self.gui = Gui(theme = theme.Theme())
    general.io = IO()
    ##On place un bouton quitter en haut à droite de l'écran
    #self.quit = self.gui.add(Icon("icones/x.png", x="right", y="top"))
    #self.quit.onClick = sys.exit
    taskMgr.add(self.ping, "Boucle GUI", 10)
    self.tooltip = self.gui.add(Label("", x=0, y="bottom", width="100%"))
    self.tooltip.style="DEFAULT"
    self.makeMain()
    
  def lanceInterface(self):
    self.removeMain()
    #On affiche le manu principal
    self.menuCourant = MenuPrincipal(self)    
    
  def add(self, pouet):
    """Racourcis pour gui.gui.add"""
    return self.gui.add(pouet)
    
  def remove(self, pouet):
    """Racourcis pour gui.gui.remove"""
    return self.gui.remove(pouet)
    
  def quitter(self):
    """Quitte l'application"""
    if isinstance(self.menuCourant, MenuPrincipal):
      sys.exit(0)
    elif isinstance(self.menuCourant, EnJeu):
      self.menuCourant.changeMenu()
    else:
      self.menuCourant.back()
    
  def ping(self, task):
    if self.menuCourant!=None:
      self.menuCourant.MAJ(task.time)
    if self.historique!=None:
      self.historique.MAJ(task.time)
    return task.cont
    
  def changeMenuVers(self, classe):
    """Passe d'un menu à un autre"""
    if self.menuCourant != None:
      if isinstance(self.menuCourant, EnJeu):
        self.menuCourant.listeCommandes.efface(classe)
      else:
        self.menuCourant.efface(classe)
      
  def nouvellePlanete(self):
    """Affiche le menu de configuration de planete"""
    self.changeMenuVers(MenuConfigurationPlanete)
      
  def _nouvellePlanete(self):
    """Construit une nouvelle planète aléatoirement"""
    self.makeMain()
    general.start.fabriquePlanete()
    general.start.start()
    
  def removeMain(self):
    """Supprime les éléments de l'interface utilisés lors du chargement"""
    self.changeMenuVers(None)
    if self.historique != None:
      self.historique.clear()
      self.historique = None
    if self.chargement != None:
      self.gui.remove(self.chargement)
      self.chargement = None
    
  def makeMain(self):
    """Construit les éléments de l'interface lors du chargement"""
    self.changeMenuVers(None)
    if self.historique!=None:
      raw_input("Zmoops !")
    self.historique = Historique(self)
    self.chargement = self.gui.add(Chargement())
    
  def configurer(self):
    """Passe au menu de configuration"""
    self.changeMenuVers(MenuConfiguration)
    
  def planeteVierge(self, fichier):
    """Charge un prototype de planète pré-construit"""
    self.makeMain()
    general.start.chargePlanete(os.path.join(".", "data", "planetes", fichier))
    general.start.start()
    
  def sauvegarderPartie(self):
    self.changeMenuVers(MenuPrincipal)
    
  def sauvegarderPartie(self):
    self.changeMenuVers(MenuPrincipal)

  def chargerPartie(self):
    """Charge un partie sauvegardée"""
    self.changeMenuVers(MenuCharge)
    
  def chargerPartie2(self, fichier):
    """Charge une partie en cours"""
    self.makeMain()
    general.start.chargePlanete(os.path.join(".", "sauvegardes", fichier))
    general.start.start()
    
  def retourJeu(self):
    """Ferme le menu en jeu et retourne à la partie"""
    self.changeMenuVers(ListeCommandes)
    
  def retourPrincipal(self):
    """Quitte la partie et retour au menu principal"""
    jeu = self.menuCourant
    self.menuCourant = None
    self.historique.clear()
    self.historique = None
    jeu.efface(MenuPrincipal)
    general.planete.detruit()
    general.start.fabriqueSystemeSolaire()
    
  def ajouteJoueur(self, joueur):
    """Indique qu'on passe du mode chargement au mode joueur"""
    self.joueur = joueur
    
    #On ajoute les composants manquants
    self.menuCourant = EnJeu(self)
    self.gui.remove(self.chargement)
    self.chargement = None
    
  def getText(self, texte):
    return general.i18n.getText(texte)
    
  def alerte(self, message, parametres, type, coord):
    """Ajoute un nouveau message"""
    message = general.i18n.getText(message)
    message = message %parametres
    self.historique.ajouteMessage(type, message, coord)
    
  def afficheConsole(self):
    if not self.console:
      self.console = self.gui.add(Console())
    else:
      self.console.visable = not self.console.visable
      
    if self.console.visable:
      general.interface.gui.keys.focus = self.console.texte
      self.console.texte.onFocus()
      
  def tip(self, icone, message):
    if icone==None:
      self.tooltip.text = general.i18n.getText(message)
      self.tooltip.icon = None
    else:
      #On laisse de la place pour l'icône
      self.tooltip.text = "     "+general.i18n.getText(message)
      self.tooltip.icon = icone
      
  def afficheTexte(self, texte, parametres, type="normal", forceRefresh=False):
    """Affiche le texte sur l'écran, si texte==None, alors efface le dernier texte affiché"""
    texte = self.getText(texte)
    parametres = self.getText(parametres)
    
    texte = texte %parametres
    if texte!=None:
      #On affiche une ligne dans le log
      if type == None:
        print general.i18n.utf8ise(texte).encode("UTF-8")
      else:
        chaine = u"["+general.i18n.utf8ise(type)+u"]"+" "+general.i18n.utf8ise(texte)
        print chaine.encode("UTF-8")
      if self.historique !=None:
        self.historique.ajouteMessage(type, texte)
        
    if forceRefresh:
      #On force le recalcul du GUI
      self.gui._doMouse()
      self.gui._doDrag()
      self.gui._reSize()
      self.gui._layout()
      self.gui._draw()
      #On force le rendu
      base.graphicsEngine.renderFrame()
      
  def hover(self):
    composant = self.gui.hoveringOver
    if composant != None:
      self.tip(composant.icon, composant.tooltip)
      if composant.__onHover__:
        composant.__onHover__()

