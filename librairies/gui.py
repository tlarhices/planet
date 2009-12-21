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
import theme
import os

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
    self.boutons=[[],[]]
    self.composants = []
    self.lastDraw = None
    self.vitesseAnimation = float(general.configuration.getConfiguration("affichage", "General", "vitesseAnimationMenus","75.0"))
    self.dureeMessage = float(general.configuration.getConfiguration("affichage", "General", "dureeMessage","30.0"))
    
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
      self.retour = self.gui.add(Icon("theme/icones/rotate_node.png", x="center", y="bottom"))
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
  "inconnu":"theme/icones/q.png",
  "mort":"theme/icones/skull.png",
  "chat":"theme/icones/phone.png",
  "obscurite":"theme/icones/clock.png",
  "info":"theme/icones/info.png",
  "avertissement":"theme/icones/caution.png",
  "sauvegarde":"theme/icones/diskette.png"
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
  
  fond = None
  fondFlou = None
  soleil = None
  soleilFlou = None
  
  carte = None

  def __init__(self, gui):
    Pane.__init__(self)
    self.gui = gui
    
    #On positionne la carte
    self.x = "right" 
    self.y = "top"
    self.style = "VIDE"
    
    #On charge les préférences utilisateur
    self.tailleMiniMapX, self.tailleMiniMapY = general.configuration.getConfiguration("affichage", "Minimap", "taille","256 256").split(" ")
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
    
    #L'image de fond
    self.fond = PNMImage(self.tailleMiniMapX,self.tailleMiniMapY)
    self.fond.fillVal(0, 0, 0)
    self.fondFlou = PNMImage(self.tailleMiniMapX,self.tailleMiniMapY)
    self.fondFlou.fillVal(0, 0, 0)
    self.soleilFlou = PNMImage(self.tailleMiniMapX,self.tailleMiniMapY)
    self.soleilFlou.fillVal(255, 255, 255)
    self.soleil = PNMImage(self.tailleMiniMapX,self.tailleMiniMapY)
    self.soleil.fillVal(255, 255, 255)
    
    self.fondRendu = PNMImage(self.tailleMiniMapX,self.tailleMiniMapY)
    self.fondRendu.fillVal(255, 0, 0)
    self.fusion = PNMImage(self.tailleMiniMapX,self.tailleMiniMapY)
    self.fusion.fillVal(0, 255, 0)
    self.soleilRendu = PNMImage(self.tailleMiniMapX,self.tailleMiniMapY)
    self.soleilRendu.fillVal(0, 0, 255)
    
    taskMgr.add(self.ping, "Boucle minimap")
    
  def onClick(self):
    self.gui.io.placeCameraAuDessusDe(self.carteVersPoint3D(self.souris))
    
  souris = [-1,-1]
  def mouseEvent(self,event,x,y):
    self.souris=[x,y]
    Pane.mouseEvent(self, event, x, y)
    
  def ajoutePoint(self, point, icone):
    """Ajout un point2D à la carte, retourne un indice servant à l'effacer plus tard"""
    if point==None:
      print "Point sur un pôle, coordonnées non calculables..."
      return None
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
    return len(self.points)
    
  def dessineCarte(self, p1, p2, p3, c1, c2, c3, estSoleil=False):
    if p1.length()<=self.gui.start.planete.niveauEau:
      c1=(0.0,0.0,1.0)
    if p2.length()<=self.gui.start.planete.niveauEau:
      c2=(0.0,0.0,1.0)
    if p3.length()<=self.gui.start.planete.niveauEau:
      c3=(0.0,0.0,1.0)
    if len(p1)==3:
      p1 = self.point3DVersCarte(p1)
    if len(p2)==3:
      p2 = self.point3DVersCarte(p2)
    if len(p3)==3:
      p3 = self.point3DVersCarte(p3)
    if p1==None or p2==None or p3==None:
      return
    minx = min(p1[0], p2[0], p3[0])
    maxx = max(p1[0], p2[0], p3[0])
    miny = min(p1[1], p2[1], p3[1])
    maxy = max(p1[1], p2[1], p3[1])
    
    def signe(p1, p2, p3):
      return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1]);
    def estDansTriangle(pt, s1, s2, s3):
      b1 = signe(pt, s1, s2) < 0.0
      b2 = signe(pt, s2, s3) < 0.0
      b3 = signe(pt, s3, s1) < 0.0
      return ((b1 == b2) and (b2 == b3))
    
    #Test des points à cheval sur les bords, s'il y en a, on dessine 2 triangles qui débordent de chaque coté de la carte
    if maxx-minx>float(self.tailleMiniMapX)*2.0/3.0:
      p1min = Vec2(p1)
      p2min = Vec2(p2)
      p3min = Vec2(p3)
      if p1min[0]<float(self.tailleMiniMapX)/2.0:
        p1min[0]=p1min[0]+float(self.tailleMiniMapX)
      if p2min[0]<float(self.tailleMiniMapX)/2.0:
        p2min[0]=p2min[0]+float(self.tailleMiniMapX)
      if p3min[0]<float(self.tailleMiniMapX)/2.0:
        p3min[0]=p3min[0]+float(self.tailleMiniMapX)
      
      if p1!=p1min or p2!=p2min or p3!=p3min:
        self.dessineCarte(p1min, p2min, p3min, c1, c2, c3, estSoleil)

      p1max = Vec2(p1)
      p2max = Vec2(p2)
      p3max = Vec2(p3)
      if p1max[0]>float(self.tailleMiniMapX)/2.0:
        p1max[0]=p1max[0]-float(self.tailleMiniMapX)
      if p2max[0]>float(self.tailleMiniMapX)/2.0:
        p2max[0]=p2max[0]-float(self.tailleMiniMapX)
      if p3max[0]>float(self.tailleMiniMapX)/2.0:
        p3max[0]=p3max[0]-float(self.tailleMiniMapX)
      
      if p1!=p1max or p2!=p2max or p3!=p3max:
        self.dessineCarte(p1max, p2max, p3max, c1, c2, c3, estSoleil)
      return
      
    if maxy-miny>float(self.tailleMiniMapY)*2.0/3.0:
      p1min = Vec2(p1)
      p2min = Vec2(p2)
      p3min = Vec2(p3)
      if p1min[1]<float(self.tailleMiniMapY)/2.0:
        p1min[1]=p1min[1]+float(self.tailleMiniMapY)
      if p2min[1]<float(self.tailleMiniMapY)/2.0:
        p2min[1]=p2min[1]+float(self.tailleMiniMapY)
      if p3min[1]<float(self.tailleMiniMapY)/2.0:
        p3min[1]=p3min[1]+float(self.tailleMiniMapY)
      print p1,p2,p3,"min ->", p1min, p2min, p3min
      if p1!=p1min or p2!=p2min or p3!=p3min:
        self.dessineCarte(p1min, p2min, p3min, c1, c2, c3, estSoleil)

      p1max = Vec2(p1)
      p2max = Vec2(p2)
      p3max = Vec2(p3)
      if p1max[1]>float(self.tailleMiniMapY)/2.0:
        p1max[1]=p1max[1]-float(self.tailleMiniMapY)
      if p2max[1]>float(self.tailleMiniMapY)/2.0:
        p2max[1]=p2max[1]-float(self.tailleMiniMapY)
      if p3max[1]>float(self.tailleMiniMapY)/2.0:
        p3max[1]=p3max[1]-float(self.tailleMiniMapY)
      print p1,p2,p3,"max ->", p1max, p2max, p3max
      if p1!=p1max or p2!=p2max or p3!=p3max:
        self.dessineCarte(p1max, p2max, p3max, c1, c2, c3, estSoleil)
      return
      
      
    #Dessine le triangle
    for x in range(int(minx+0.5), int(maxx+0.5)):
      if x in range(0, self.tailleMiniMapX):
        for y in range(int(miny+0.5), int(maxy+0.5)):
          if y in range(0, self.tailleMiniMapY):
            d1=(Vec2(x,y)-Vec2(p1[0], p1[1])).length()
            d2=(Vec2(x,y)-Vec2(p2[0], p2[1])).length()
            d3=(Vec2(x,y)-Vec2(p3[0], p3[1])).length()
            fact=(d1+d2+d3)/2
            d1=1-d1/fact
            d2=1-d2/fact
            d3=1-d3/fact
            
            couleur=c1[0]*d1+c2[0]*d2+c3[0]*d3, c1[1]*d1+c2[1]*d2+c3[1]*d3, c1[2]*d1+c2[2]*d2+c3[2]*d3
            if not estSoleil:
              self.fondFlou.setXel(x, y, couleur[0], couleur[1], couleur[2])
            else:
              self.soleilFlou.setXel(x, y, couleur[0], couleur[1], couleur[2])
            if estDansTriangle((x,y),p1,p2,p3):
              if not estSoleil:
                self.fond.setXel(x, y, couleur[0], couleur[1], couleur[2])
                self.carteARedessiner = True
              else:
                self.soleil.setXel(x, y, couleur[0], couleur[1], couleur[2])
                self.carteSoleilARedessiner = True
    
  def ajoutePoint3D(self, point, icone):
    """Ajout un point3D à la carte, retourne un indice servant à l'effacer plus tard"""
    return self.ajoutePoint(self.point3DVersCarte(point), icone)
      
  def point3DVersCarte(self, point):
    point = Vec3(point)
    point.normalize()
    x,y,z = point
    lon = math.acos(z)
    
    tmp = Vec2(x,y)
    tmp.normalize()
    x,y=tmp
    
    if x==0.0 and y==0.0:
      lat=0.0
    elif y>=0:
      if x==0:
        lat=math.acos(0.0)
      else:
        lat=math.acos(x/math.sqrt(x*x+y*y))
    else:
      lat=2 * math.pi - math.acos(x/math.sqrt(x*x+y*y))
    lat=lat*float(self.tailleMiniMapX)/(2*math.pi)
    
    z=(-z*self.tailleMiniMapY/2+self.tailleMiniMapY/2)
    return int(lat+0.5), int(z+0.5)
    
  def carteVersPoint3D(self, point):
    if point==None:
      return None
      
    lat, z = point
    z=-(float(z)-float(self.tailleMiniMapY)/2)/(float(self.tailleMiniMapY)/2)
    
    lat = float(lat)*(2*math.pi)/float(self.tailleMiniMapX)
    x=math.cos(lat)
    y=math.sin(lat)
    if z==1.0 or z==-1.0:
      x=0.0
      y=0.0
    return (x, y, z)
  
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
      
  def majBlip(self, blipid, point, icone):
    """Change les coordonnées d'un point"""
    point = self.point3DVersCarte(point)
    self.points[blipid]=(point, icone)
    if blipid in self.blips.keys():
      self.blips[blipid].doPlacement({"x":point[0], "y":point[1]})
      self.blips[blipid].icon = icone

  def ping(self, task):
    """Boucle qui met à jour la carte"""
    #Le fond de carte
    if self.derniereMAJ==None or task.time-self.derniereMAJ>10.0:
      if self.carteARedessiner:
        for x in range(0, self.tailleMiniMapX):
          for y in range(0, self.tailleMiniMapY):
            px = self.fond.getXel(x,y)
            if px[0]==0.0 and px[1]==0.0 and px[2]==0.0:
              self.fondRendu.setXel(x,y, self.fondFlou.getXel(x,y))
            else:
              self.fondRendu.setXel(x,y, px)
        #fond.gaussianFilter(2.0)
        #self.fondRendu.write(Filename("./carte.png"))
      #La zone d'ombre
      if self.carteSoleilARedessiner and general.configuration.getConfiguration("affichage","minimap","affichesoleil","t")=="t":
        for x in range(0, self.tailleMiniMapX):
          for y in range(0, self.tailleMiniMapY):
            spx = self.soleil.getXel(x,y)
            if spx[0]==1.0 and spx[1]==1.0 and spx[2]==1.0:
              self.soleilRendu.setXel(x,y, self.soleilFlou.getXel(x,y))
            else:
              self.soleilRendu.setXel(x,y, spx)
        #On la rends floue pour qu'elle soit plus jolie
        self.soleilRendu.gaussianFilter(5.0)
        #self.soleilRendu.write(Filename("./soleil.png"))
      #La fusion fond + ombre
      if general.configuration.getConfiguration("affichage","minimap","affichesoleil","t")=="t":
        if self.carteARedessiner or self.carteSoleilARedessiner:
          for x in range(0, self.tailleMiniMapX):
            for y in range(0, self.tailleMiniMapY):
              px = self.fondRendu.getXel(x,y)
              spx = self.soleilRendu.getXel(x,y)
              self.fusion.setXel(x, y, px[0]*spx[0], px[1]*spx[1], px[2]*spx[2])
          #self.fusion.write(Filename("./fusion.png"))
          texture = Texture("fusion")
          texture.load(self.fusion)
          self.carte.setImage(texture)
      elif self.carteARedessiner:
        texture = Texture("fond")
        texture.load(self.fondRendu)
        self.carte.setImage(texture)
        
      self.carteARedessiner = False
      self.carteSoleilARedessiner = False
      self.derniereMAJ=task.time
      
    self.enlevePoint(self.camBlip)
    self.camBlip = self.ajoutePoint3D(self.gui.io.camera.getPos(),"theme/icones/camera.png")
    for id in self.points.keys():
      if id not in self.blips.keys():
        #Ce point n'a pas de représentation sur la carte, on en fabrique un nouveau
        self.blips[id] = self.add(Icon(self.points[id][1],x=self.points[id][0][0], y=self.points[id][0][1]))
        self.blips[id].color=(1.0,0.0,0.0,1.0)
        self.blips[id].onClick = self.onClick
    return task.cont
            
class ListeUnite(MenuCirculaire):
  select = None #L'unité sélctionnée en ce moment
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.angleOuverture = 80.0
    self.besoinRetour = False
    
    tmp=os.listdir(os.path.join(".","data","sprites"))
    for elem in tmp:
      if elem.endswith(".spr"):
        sprite = general.configuration.parseSprite(os.path.join(".","data","sprites", elem))
        if sprite["constructible"]:
          check = self.ajouteGauche(PictureRadio(sprite["icone-actif"], sprite["icone-inactif"], sprite["nom"].capitalize(), width=LARGEUR_BOUTON))
          check.alpha = 0.5
          check.style = "DEFAULT"
          check.callback = self.clic
    self.fabrique()
            
  def anime(self, temps):
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
    self.i1 = self.add(Icon("theme/icones/blank.png", x=20, y=y)) #Icone
    self.i1.visable = False #On cache l'icone
    y+=HAUTEUR_TEXTE
    self.l2 = self.add(Label("", x=20, y=y))
    self.i2 = self.add(Icon("theme/icones/blank.png", x=20, y=y))
    self.i2.visable = False
    y+=HAUTEUR_TEXTE
    self.l3 = self.add(Label("", x=20, y=y))
    self.i3 = self.add(Icon("theme/icones/blank.png", x=20, y=y))
    self.i3.visable = False
    y+=HAUTEUR_TEXTE
    self.l4 = self.add(Label("", x=20, y=y))
    self.i4 = self.add(Icon("theme/icones/blank.png", x=20, y=y))
    self.i4.visable = False
    
    #Bare de défilement
    self.plus = self.add(Icon("theme/icones/arrow-up.png", x="left", y="top"))
    self.plus.onClick = self.logHaut
    self.plus = self.add(Icon("theme/icones/arrow-down.png", x="left", y="bottom"))
    self.plus.onClick = self.logBas
    self.curseur = self.add(Icon("theme/icones/blank.png", x="left", y=HAUTEUR_TEXTE))
    
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
  "inconnu":"theme/icones/q.png",
  "mort":"theme/icones/skull.png",
  "chat":"theme/icones/phone.png",
  "info":"theme/icones/info.png",
  "obscurite":"theme/icones/clock.png",
  "avertissement":"theme/icones/caution.png",
  "sauvegarde":"theme/icones/diskette.png"
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
    
    self.enJeu = isinstance(self.gui.menuCourant, EnJeu)
    
    if not self.enJeu:
      self.ajouteGauche(Button(u"Nouvelle planète", self.gui.nouvellePlanete, width=LARGEUR_BOUTON))
    
    if not self.enJeu:
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
    
class MenuConfiguration(MenuCirculaire):
  """Le menu de configuration"""
  
  select = None
  
  def __init__(self, gui):
    MenuCirculaire.__init__(self, gui)
    self.changeMenu("")
    
  def changeMenu(self, select):
    self.select = select.lower()
    self.directionAnimation = -1.0
    self.clear()
    
    for section in general.configuration.configuration.keys():
      aAfficher = general.configuration.getConfiguration(section, "gui", "dansGUI", "f")=="t"
      if aAfficher:
        iconeactif=general.configuration.getConfiguration(section, "gui", "icone-actif", "theme/icones/q-over.png")
        iconeinactif=general.configuration.getConfiguration(section, "gui", "icone-inactif", "theme/icones/q.png")
        nom=general.configuration.getConfiguration(section, "gui", "menu", section).capitalize()
        btn = self.ajouteGauche(PictureRadio(iconeactif, iconeinactif, nom, width=LARGEUR_BOUTON))
        btn.callback = self.clic
        btn.style = "button"
        btn.upStyle = "button"
        btn.overStyle = "button_over"
        btn.downStyle = "button_down"
        if self.select.lower().strip() == nom.lower().strip():
#          btn.style = "CHECKON"
#          btn.value = True
          
          for soussection in general.configuration.configuration[section].keys():
            if soussection!="gui":
              btn = self.ajouteDroite(PictureRadio(iconeinactif, iconeinactif, soussection.capitalize(), width=LARGEUR_BOUTON))
              btn.style = "button"
              btn.upStyle = "button"
              btn.overStyle = "button_over"
              btn.downStyle = "button_down"
              for element in general.configuration.configuration[section][soussection].keys():
                valeur = general.configuration.getConfiguration(section, soussection, element,"Erreur 164")
                if valeur=="t" or valeur=="f":
                  btnD = self.ajouteDroite(PictureCheck("theme/icones/checkmark.png","theme/icones/blank.png",element.capitalize()+" : "+valeur, width=LARGEUR_BOUTON))
                  if valeur=="t":
                    btnD.value = True
                    btnD.icon = btnD.picOn
                  else:
                    btnD.value = False
                    btnD.icon = btnD.picOff
                else:
                  btnD = self.ajouteDroite(Label(element.capitalize()+" : "+valeur, width=LARGEUR_BOUTON))
                btnD.style = "button"
                btnD.upStyle = "button"
                btnD.overStyle = "button_over"
                btnD.downStyle = "button_down"
    
    MenuCirculaire.fabrique(self)
    
  resolutions = ["160 120", "320 240", "640 480", "800 600", "1024 768"]
    
  def resolutionPlus(self):
    res = general.configuration.getConfiguration("affichage", "general", "resolution", "640 480")
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
    res = general.configuration.getConfiguration("affichage", "general", "resolution", "640 480")
    if res in self.resolutions:
      idx = self.resolutions.index(res)
      idx-=1
      while idx<0:
        idx+= len(self.resolutions)
    else:
      idx=0
    general.configuration.setConfiguration("affichage", "general", "resolution", self.resolutions[idx])
    self.clic("affichage", True)
    
  def clic(self, bouton, etat):
    """
    On a cliqué sur un bouton de changement de panneau de configuration
    bouton : le texte du bouton
    etat : si True alors le bouton est actif (ce devrait toujours être le cas de figure)
    """
    self.changeMenu(bouton)
    
  def anime(self, temps):
    MenuCirculaire.anime(self, temps)
    for composant, indice, cote in self.composants:
      if cote==0:
        composant.doPlacement({"x":composant.x-composant.width})
    
    
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
        check = self.ajouteGauche(PictureRadio("theme/icones/news-over.png", "theme/icones/news.png", elem[0].capitalize()))
      else:
        check = self.ajouteDroite(PictureRadio("theme/icones/news-over.png", "theme/icones/news.png", elem[0].capitalize()))
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
      check = self.ajouteGauche(PictureRadio("theme/icones/diskette-over.png", "theme/icones/diskette.png", elem[0].capitalize(), width=LARGEUR_BOUTON))
#      else:
#        check = self.ajouteDroite(PictureRadio("theme/icones/diskette-over.png", "theme/icones/diskette.png", elem[0].capitalize(), width=LARGEUR_BOUTON))
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
    self.gui = Gui(theme = theme.Theme())
    self.io = IO(self)
    ##On place un bouton quitter en haut à droite de l'écran
    #self.quit = self.gui.add(Icon("theme/icones/x.png", x="right", y="top"))
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
    """Construit une nouvelle planète aléatoirement"""
    self.makeMain()
    self.start.fabriquePlanete()
    self.start.start()
    
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
    self.start.chargePlanete(os.path.join(".", "data", "planetes", fichier))
    self.start.start()
    
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
    self.start.chargePlanete(os.path.join(".", "sauvegardes", fichier))
    self.start.start()
    
  def retourJeu(self):
    """Ferme le menu en jeu et retourne à la partie"""
    self.changeMenuVers(ListeUnite)
    
  def retourPrincipal(self):
    """Quitte la partie et retour au menu principal"""
    jeu = self.menuCourant
    self.menuCourant = None
    
    #On indique que la planète à l'écran n'est pas en jeu, mais est un fond de menu
    self.start.tmp = self.start.planete
    self.start.planete = None
    jeu.efface(MenuPrincipal)
    
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
