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
    
class Console(Pane):
  style = "default"
  def __init__(self):
    Pane.__init__(self)
    self.ligne1 = self.add(Label("Ligne 1", x=PAD, y=PAD*1+HAUTEUR_TEXTE*0))
    self.ligne2 = self.add(Label("Ligne 2", x=PAD, y=PAD*2+HAUTEUR_TEXTE*1))
    self.ligne3 = self.add(Label("Ligne 3", x=PAD, y=PAD*3+HAUTEUR_TEXTE*2))
    self.ligne4 = self.add(Label("Ligne 4", x=PAD, y=PAD*4+HAUTEUR_TEXTE*3))
    self.texte = self.add(TextArea("Texte...", x=PAD, y=PAD*5+HAUTEUR_TEXTE*4, width="100%"))
    #On positionne la Form
    self.x = "left" 
    self.y = "top" 
    self.width = "100%"
    self.height = PAD*7+HAUTEUR_TEXTE*5
    
  def efface(self):
    pass
    
    
    
class MenuCirculaire:
  """Affiche des boutons positionnés sur un anneau"""
  boutons = None #Liste des instances de boutons
  composants = None #Liste des instances de boutons (utilisé pour l'animation)
  retour = None #Un bouton qui ramène au menu précédent
  besoinRetour = True #Si True, alors de l'appel à fabrique un bouton ramenant au menu précédent sera crée
  angleOuverture = None #L'angle sur lequel les boutons s'étalent (en degrés)
  
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
    self.angleOuverture = 120.0
    self.animation = 120.0
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
    """Ajoute un bouton dans la colonne de gauche"""
    self.boutons[2].append(bouton)
    return bouton
    
  def ajouteBas(self, bouton):
    """Ajoute un bouton dans la colonne de droite"""
    self.boutons[3].append(bouton)
    return bouton

  def cercle(self, centre, rayon, angleOuverture, nbelemsG, nbelemsD, nbelemsH, nbelemsB):
    """
    Calcul les positions des boutons à placer sur le cercle
    centre : le centre du cercle
    rayon : le rayon du cercle
    angleOuverture : l'angle sur lequel les boutons l'étalent
    nbelemS, bnelemsD : le nombre d'éléments dans la colonne de gauche / de droite
    """
    elements = [[],[],[],[]]
    rayon=abs(rayon)
    if nbelemsG==1:
      angleG=angleOuverture
    else:
      angleG = abs(float(angleOuverture)/(nbelemsG-1))
      
    if nbelemsD==1:
      angleD=angleOuverture
    else:
      angleD = abs(float(angleOuverture)/(nbelemsD-1))

    if nbelemsH==1:
      angleH=angleOuverture
    else:
      angleH = abs(float(angleOuverture)/(nbelemsH-1))
      
    if nbelemsB==1:
      angleB=angleOuverture
    else:
      angleB = abs(float(angleOuverture)/(nbelemsB-1))

    dep = -float(angleOuverture)/2.0
    
    for i in range(0, max(nbelemsG, nbelemsD, nbelemsH, nbelemsB)):
      if i==0 and nbelemsB==1:
        x=rayon*math.cos((90.0)/180*math.pi)
        y=rayon*math.sin((90.0)/180*math.pi)
        elements[3].append((centre[0]+x,centre[1]+y))
      elif i<nbelemsB:
        x=rayon*math.cos((90 + angleB*(i-nbelemsB/2) - dep)/180*math.pi)
        y=rayon*math.sin((90 + angleB*(i-nbelemsB/2) - dep)/180*math.pi)
        elements[3].append((centre[0]+x,centre[1]+y))
      if i==0 and nbelemsH==1:
        x=rayon*math.cos((90.0)/180*math.pi)
        y=rayon*math.sin((90.0)/180*math.pi)
        elements[2].append((centre[0]-x,centre[1]-y))
      elif i<nbelemsH:
        x=rayon*math.cos((90 + angleH*(i-nbelemsH/2) - dep)/180*math.pi)
        y=rayon*math.sin((90 + angleH*(i-nbelemsH/2) - dep)/180*math.pi)
        elements[2].append((centre[0]-x,centre[1]-y))
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
    self.animation += self.directionAnimation * temps * self.vitesseAnimation
    
    if self.animation<0:
      self.animation=0.0
    if self.animation>120:
      self.animation=120.0
      if self.exit != None:
        self.clear()
        if isinstance(self.gui.menuCourant, EnJeu):
          self.gui.menuCourant.listeUnite = self.exit(self.gui)
        else:
          self.gui.menuCourant = self.exit(self.gui)

    bg, bd, bh, bb = self.boutons
    nbBoutonsG = len(bg)
    nbBoutonsD = len(bd)
    nbBoutonsH = len(bh)
    nbBoutonsB = len(bb)
    coords = self.cercle(self.getCentre(), self.getRayon(), self.angleOuverture-abs(self.animation), nbBoutonsG, nbBoutonsD, nbBoutonsH, nbBoutonsB)
    
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
    if self.besoinRetour:
      self.retour = self.ajouteBas(Icon("icones/rotate_node.png", x="center", y="bottom"))
      #self.retour = self.ajouteBas(Icon("icones/rotate_node.png", x="center", y="bottom"))
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
        bouton.width = 190
        self.gui.gui.add(bouton)
        self.composants.append((bouton, i, 0))
      
      if i<len(bd):
        bouton = bd[i]
        bouton.width = 190
        self.gui.gui.add(bouton)
        self.composants.append((bouton, i, 1))

      if i<len(bh):
        bouton = bh[i]
        bouton.width = 190
        self.gui.gui.add(bouton)
        self.composants.append((bouton, i, 2))
        
      if i<len(bb):
        bouton = bb[i]
        bouton.width = 190
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
    while self.boutons[2].count(composant)>0:
      self.boutons[2].remove(composant)
    while self.boutons[3].count(composant)>0:
      self.boutons[3].remove(composant)
    self.fabrique()
      
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
    message : le contenu du message
    position : le point au dessus duquel la caméra doit aller lors d'un clic sur l'icône
    """
    self.messages.append((self.dureeMessage, type, message, self.ajouteDroite(self.fabriqueMessage(type, message))))
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
        composant.color = (composant.color[0], composant.color[1], composant.color[2], abs(restant%2-1))
      self.messages[i] = (restant, type, message, composant)
      
    for message in aVirer:
      while self.messages.count(message)>0:
        self.messages.remove(message)
        
    MenuCirculaire.MAJ(self, temps)
    
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
  
  def resize(self, task):
    """ resize the window via panda3d internal events"""
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
            
class ListeUnite(MenuCirculaire):
  select = None #L'unité sélctionnée en ce moment
  liste = None
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.angleOuverture = 80.0
    self.besoinRetour = False
    self.liste = []
    self.fabrique()
    
  def fabrique(self):
    self.clear()
    for sprite in self.liste:
      check = self.ajouteGauche(PictureRadio(sprite.definition["icone-actif"], sprite.definition["icone-inactif"], sprite.definition["nom"].capitalize()+" "+str(int(sprite.vie))+"%", width=LARGEUR_BOUTON))
      check.color = (sprite.joueur.couleur[0]*1.2, sprite.joueur.couleur[1]*1.2, sprite.joueur.couleur[2]*1.2, 0.5)
      check.style = "DEFAULT"
      check.callback = self.clic
    MenuCirculaire.fabrique(self)
            
  def anime(self, temps):
    if self.liste != general.io.selection:
      self.liste = general.io.selection[:]
      print "la sélection a changée"
      self.fabrique()
    MenuCirculaire.anime(self, temps)
    for composant, indice, cote in self.composants:
      composant.doPlacement({"x":composant.x-composant.width})

  def clic(self, bouton, etat):
    """
    On a cliqué sur un bouton de construction d'unité
    bouton : le texte du bouton
    etat : si True alors le bouton est actif (ce devrait toujours être le cas de figure)
    """
    self.select = bouton.lower()

class EnJeu():
  """Contient la liste des unitées que l'on peut construire"""
  listeUnite = None #La liste des icone d'unités constructibles
  historique = None #La liste des icones d'information
  miniMap = None #La carte
  
  def __init__(self, gui):
    self.gui = gui
    self.historique = Historique(self.gui)
    self.listeUnite = ListeUnite(self.gui)
    self.miniMap = self.gui.gui.add(MiniMap(self.gui))
    
  def alerte(self, type, message, coord):
    """Ajoute un nouveau message"""
    self.historique.ajouteMessage(type, message, coord)
    self.gui.informations.ajouteTexte(type, message)
    
  def MAJ(self, temps):
    self.historique.MAJ(temps)
    self.listeUnite.MAJ(temps)
    
  def efface(self, classe):
    self.clear()
    self.gui.menuCourant = classe(self.gui)
    
  def clear(self):
    self.historique.clear()
    self.listeUnite.clear()
    #Purge tous les points de la carte
    self.miniMap.clear()
    self.gui.gui.remove(self.miniMap)
    
  def changeMenu(self):
    if isinstance(self.listeUnite, ListeUnite):
      self.gui.changeMenuVers(MenuPrincipal)
    else:
      self.gui.changeMenuVers(ListeUnite)
        
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
    self.i1 = self.add(Icon("icones/blank.png", x=20, y=y)) #Icone
    self.i1.visable = False #On cache l'icone
    y+=HAUTEUR_TEXTE
    self.l2 = self.add(Label("", x=20, y=y))
    self.i2 = self.add(Icon("icones/blank.png", x=20, y=y))
    self.i2.visable = False
    y+=HAUTEUR_TEXTE
    self.l3 = self.add(Label("", x=20, y=y))
    self.i3 = self.add(Icon("icones/blank.png", x=20, y=y))
    self.i3.visable = False
    y+=HAUTEUR_TEXTE
    self.l4 = self.add(Label("", x=20, y=y))
    self.i4 = self.add(Icon("icones/blank.png", x=20, y=y))
    self.i4.visable = False
    
    #Bare de défilement
    self.plus = self.add(Icon("icones/arrow-up.png", x="left", y="top"))
    self.plus.onClick = self.logHaut
    self.plus = self.add(Icon("icones/arrow-down.png", x="left", y="bottom"))
    self.plus.onClick = self.logBas
    self.curseur = self.add(Icon("icones/blank.png", x="left", y=HAUTEUR_TEXTE))
    
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
  "inconnu":"icones/q.png",
  "mort":"icones/skull.png",
  "chat":"icones/phone.png",
  "info":"icones/info.png",
  "obscurite":"icones/clock.png",
  "avertissement":"icones/caution.png",
  "sauvegarde":"icones/diskette.png"
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
  enJeu = None
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.besoinRetour = False
    
    if not os.path.exists(os.path.join(".", "sauvegardes")):
      os.makedirs(os.path.join(".", "sauvegardes"))
    if not os.path.join(".", "data", "planetes"):
      os.makedirs(os.path.join(".", "data", "planetes"))

    self.enJeu = isinstance(self.gui.menuCourant, EnJeu)
    
    if not self.enJeu:
      self.ajouteGauche(Button(u"Nouvelle planète", self.gui.nouvellePlanete, width=LARGEUR_BOUTON))
    
    if not self.enJeu:
      cpt = 0
      for fich in os.listdir(os.path.join(".", "data", "planetes")):
        if fich.endswith(".pln"):
          cpt+=1
      if cpt>0:
        self.ajouteGauche(Button(u"Utiliser un planète vierge", self.gui.planeteVierge, width=LARGEUR_BOUTON))
      
      
    cpt = 0
    for fich in os.listdir(os.path.join(".", "sauvegardes")):
      if fich.endswith(".pln"):
        cpt+=1
    if cpt>0:
      self.ajouteGauche(Button(u"Charger une partie", self.gui.chargerPartie, width=LARGEUR_BOUTON))
      
    if self.enJeu:
      self.ajouteGauche(Button(u"Sauvegarder la partie", self.gui.sauvegarderPartie, width=LARGEUR_BOUTON))

    self.ajouteGauche(Button(u"Configuration", self.gui.configurer, width=LARGEUR_BOUTON))

    if self.enJeu:
      self.ajouteGauche(Button(u"Retour en Jeu", self.gui.retourJeu, width=LARGEUR_BOUTON))
      self.ajouteGauche(Button(u"Quitter la partie", self.gui.retourPrincipal, width=LARGEUR_BOUTON))
    if not self.enJeu:
      self.ajouteGauche(Button(u"Quitter le jeu", self.gui.quitter, width=LARGEUR_BOUTON))
    self.fabrique()
    
  def anime(self, temps):
    MenuCirculaire.anime(self, temps)
    for composant, indice, cote in self.composants:
      composant.doPlacement({"x":composant.x-composant.width})
    
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
      btn = self.ajouteGauche(PictureRadio(dicoSection["iconeactif"], dicoSection["iconeinactif"], dicoSection["nom"], width=LARGEUR_BOUTON))
      btn.callback = self.clicSection
      btn.style = "button"
      btn.upStyle = "button"
      btn.overStyle = "button_over"
      btn.downStyle = "button_down"
      
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
            btn = self.ajouteDroite(PictureRadio(contenuElement["iconeactif"], contenuElement["iconeinactif"], contenuElement["nom"], width=LARGEUR_BOUTON))
            if contenuElement["valeur"]:
              btn.callback = self.clicVide
              btn.onClick()
            btn.callback = self.clicValeur
            
          #Les int et les float ont des boutons +/-
          elif contenuElement["type"] in ["int", "float"] and "valeurmin" in contenuElement.keys() and "valeurmax" in contenuElement.keys():
            #Le fond du bouton
            btn = self.ajouteDroite(Pane(width=LARGEUR_BOUTON, height=HAUTEUR_BOUTON+HAUTEUR_TEXTE))
            pr = PictureRadio(contenuElement["iconeactif"], contenuElement["iconeinactif"], contenuElement["nom"])
            btn.add(pr)
            #Le bouton moins
            pr = Icon("icones/minus.png", y=HAUTEUR_TEXTE+PAD)
            pr.callbackParams = {"bouton":"moins-"+contenuElement["nom"], "etat":True}
            pr.callback = self.clicValeur
            btn.add(pr)
            #Le bouton plus
            pr = Icon("icones/plus.png", y=HAUTEUR_TEXTE+PAD, x=HAUTEUR_TEXTE+PAD)
            pr.callbackParams = {"bouton":"plus-"+contenuElement["nom"], "etat":True}
            pr.callback = self.clicValeur
            btn.add(pr)
            #Le texte de la forme "valeur [min;max]"
            pr = Label(str(contenuElement["valeur"])+" ["+str(contenuElement["valeurmin"])+";"+str(contenuElement["valeurmax"])+"]", y=HAUTEUR_TEXTE+PAD, x=HAUTEUR_TEXTE*2+PAD*2)
            btn.add(pr)
            
          #Les listes et les labels sont justes affichés sous la forme
          #
          #icone nom
          #      valeur
          else:
            btn = self.ajouteDroite(PictureRadio(contenuElement["iconeactif"], contenuElement["iconeinactif"], contenuElement["nom"]+"\n   "+str(contenuElement["valeur"]), width=LARGEUR_BOUTON))
            btn.callback = self.clicValeur
            
          #On change le style des composant pour avoir un fond de bouton
          btn.style = "button"
          btn.upStyle = "button"
          btn.overStyle = "button_over"
          btn.downStyle = "button_down"
      
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
      
    #On recherche dans la liste des boutons de quel bouton il sagit
    for nomSection, contenuSection, dicoSection in self.menu:
      if self.select == dicoSection["nom"].lower().strip():
        for nomElement, contenuElement in contenuSection:
          if contenuElement["nom"].lower().split("\n")[0].strip()==bouton.lower():
            #On a trouvé le bouton, on extrait le chemin de configuration qui lui correspond
            sect, soussect, clef = contenuElement["chemin"].split("/")
            
            #Les float varient entre valeurMin et valeurMax par pas de 1/20 de l'espace à parcourir
            if contenuElement["type"] == "float":
              delta = (float(contenuElement["valeurmax"])-float(contenuElement["valeurmin"]))/20
              nvVal = float(contenuElement["valeur"])+delta*modificateur
              if nvVal<float(contenuElement["valeurmin"]):
                nvVal = float(contenuElement["valeurmin"])
              if nvVal>float(contenuElement["valeurmax"]):
                nvVal = float(contenuElement["valeurmax"])
              #Met à jour la configuration
              general.configuration.setConfiguration(sect, soussect, clef, nvVal)
              
            #Les int varient entre valeurMin et valeurMax par pas de 1
            elif contenuElement["type"] == "int":
              nvVal = int(float(contenuElement["valeur"]))+modificateur
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
    
  def anime(self, temps):
    MenuCirculaire.anime(self, temps)
    for composant, indice, cote in self.composants:
      if cote==0:
        composant.doPlacement({"x":composant.x-composant.width})

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
      
      zip = zipfile.ZipFile(os.path.join(".", "data", "planetes", elem[1]), "r")
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
      
      if i<len(self.liste)/2:
        check = self.ajouteGauche(PictureRadio("icones/news-over.png", "icones/news.png", nom))
      else:
        check = self.ajouteDroite(PictureRadio("icones/news-over.png", "icones/news.png", nom))
      check.style = "button"
      check.upStyle = "button"
      check.overStyle = "button_over"
      check.downStyle = "button_down"
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
  informations = None
  console = None
  
  def __init__(self):
    #Fabrique le GUI de base
    self.gui = Gui(theme = theme.Theme())
    general.io = IO()
    ##On place un bouton quitter en haut à droite de l'écran
    #self.quit = self.gui.add(Icon("icones/x.png", x="right", y="top"))
    #self.quit.onClick = sys.exit
    taskMgr.add(self.ping, "Boucle GUI", 10)
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
    return task.cont
    
  def changeMenuVers(self, classe):
    """Passe d'un menu à un autre"""
    if self.menuCourant != None:
      if isinstance(self.menuCourant, EnJeu):
        self.menuCourant.listeUnite.efface(classe)
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
    if self.informations != None:
      self.gui.remove(self.informations)
      self.informations = None
    if self.chargement != None:
      self.gui.remove(self.chargement)
      self.chargement = None
    
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
    self.changeMenuVers(ListeUnite)
    
  def retourPrincipal(self):
    """Quitte la partie et retour au menu principal"""
    jeu = self.menuCourant
    self.menuCourant = None
    
    jeu.efface(MenuPrincipal)
    
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
    self.gui.informations.ajouteTexte(type, message)
    
  def afficheConsole(self):
    if self.console != None:
      self.gui.remove(self.console)
      self.console.efface()
      self.console = None
    else:
      self.console = self.gui.add(Console())
    
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
