#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandac.PandaModules import *

import general
import sys
import math

class IO:
  preImage = None #L'heure à laquelle la précédente image a été rendue
  select = None #Le sprite sélectionné
  
  #Gestion de la caméra
  camera = None
  cameraRayon = 6.0 #Distance de la caméra au centre de la planète
  cameraAngleX = 0.0 #Angle de rotation de la planète selon la verticale
  cameraAngleY = 0.0 #Angle de rotation de la planète selon l'horizontale
  cameraPasRotation = general.degVersRad(1.0) #Angle entre 2 positions de la caméra
  cameraPasZoom = 0.005 #Pas de zoom
  cameraAngleSurface = 50 #L'angle de la caméra à la surface
  
  #Gestion du clavier
  touches = None #Liste des touches pressées en ce moment 
  configClavier = None #Dictionnaire des affectations de commandes
                       #De la forme ["nom de touche"]="action"
                       #Par exemple ["escape"]="quitter"
  actions = None #Dictionnaire des actions accessibles via touches
                 #De la frome ["action"]=(fonction à exécuter,X)
                 #X peut être None
                 #X peut être un tuple (0, 1) ou (0, ) ou (a, b ,c)...
                 #X peut être une liste [a, g]...
                 #X peut être un dictionnaire {"nom parametre":valeur, ...}
                 
  def __init__(self):
    #On donne des alias à certaines fonctions
    self.lierActionsFonctions()
    
    #On associe des touches à des actions
    self.touches = []
    self.configClavier = general.configuration.getConfigurationClavier()

    #On place la caméra dans un noeud facile à secouer
    self.camera = NodePath("cam")
    self.camera.reparentTo(render)
    base.camera.reparentTo(self.camera)
    
    #Désactive la gestion par défaut de la souris
    base.disableMouse() 
    #Place la caméra à sa position
    self.camera.setPos(self.cameraRayon,0,0)
    self.positionneCamera(render)

    if base.mouseWatcherNode != None:
      #Normalement panda envoie des evenements du type "arrow_left"
      #ou "alt_arrow_left", avec ça il envoie "alt" et "arow_left" tout seul
      base.mouseWatcherNode.setModifierButtons(ModifierButtons())
      base.buttonThrowers[0].node().setModifierButtons(ModifierButtons())
      #On redirige toutes les événements de touches vers 2 fonctions magiques
      base.accept('wheel_up', self.presseTouche, ['wheel_up'])
      base.accept('wheel_down', self.presseTouche, ['wheel_down'])
      base.buttonThrowers[0].node().setButtonDownEvent('presseTouche')
      base.buttonThrowers[0].node().setButtonUpEvent('relacheTouche')
      base.accept('presseTouche', self.presseTouche)
      base.accept('relacheTouche', self.relacheTouche)
      
      #Ajout du rayon magique de la souris
      base.cTrav = CollisionTraverser()
      self.myHandler = CollisionHandlerQueue()
      self.pickerNode=CollisionNode('mouseRay')
      self.pickerNP=camera.attachNewNode(self.pickerNode)
      self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
      self.pickerRay=CollisionRay()
      self.pickerNode.addSolid(self.pickerRay)
      base.cTrav.addCollider(self.pickerNP, self.myHandler)
      taskMgr.add(self.ping, "Boucle IO")
      
  def ping(self, task):
    #Calculs du temps écoulé depuis l'image précédente
    if self.preImage != None:
      deltaT = task.time - self.preImage
    else:
      deltaT = task.time
    self.preImage = task.time
    
    if base.mouseWatcherNode !=None:
      #Teste de la position de la souris
      if base.mouseWatcherNode.hasMouse():
        mpos=base.mouseWatcherNode.getMouse()
        x=mpos.getX()
        y=mpos.getY()
        seuil = 0.8
        #Regarde si la caméra est proche d'un bord et fait tourner la planète le cas échéant
        if x<-seuil:
          self.tourneCamera(self.cameraPasRotation*(x+seuil)/(1.0-seuil), 0.0)
        if x>seuil:
          self.tourneCamera(self.cameraPasRotation*(x-seuil)/(1.0-seuil), 0.0)
        if y<-seuil:
          self.tourneCamera(0.0, self.cameraPasRotation*(y+seuil)/(1.0-seuil))
        if y>seuil:
          self.tourneCamera(0.0, self.cameraPasRotation*(y-seuil)/(1.0-seuil))
      
    #Clavier
    self.gereTouche()
    return task.cont
    
  ### Gestion de la caméra ---------------------------------------------
  def positionneCamera(self, racine=None):
    """Place la caméra dans l'univers"""
    try:
      planete = general.planete
    except AttributeError:
      planete = None
      
    if planete == None:
      racine = render
      delta = 0.1
    else:
      delta = planete.geoide.delta
      
    if racine == None:
      racine = planete.geoide.racine
      
    self.camera.reparentTo(racine)
    
    #La position de la caméra est gérée en coordonnées sphériques
    if self.camera.getPos().lengthSquared()!=self.cameraRayon*self.cameraRayon:
      coord = self.camera.getPos()
      coord.normalize()
      coord=coord*self.cameraRayon
    
      self.camera.setPos(coord)
    
    #La caméra regarde toujours le centre de la planète
    self.camera.lookAt(Point3(0,0,0), racine.getRelativeVector(self.camera, Vec3(0,0,1)))
    angle = self.cameraAngleSurface-self.cameraAngleSurface*(-0.5+(self.cameraRayon-1.0)/(1.2))
    angle = min(max(0.0, angle),self.cameraAngleSurface)
    base.camera.setP(angle)

  def zoomPlus(self):
    """Approche la caméra de la planète"""
    planete = general.planete
      
    self.cameraRayon -= self.cameraRayon*self.cameraPasZoom
    self.cameraRayon = max(self.cameraRayon, 1.0 + planete.geoide.delta + 0.001)
    self.positionneCamera()

  def zoomMoins(self):
    """Éloigne la caméra de la planète"""
    planete = general.planete
      
    self.cameraRayon += self.cameraRayon*self.cameraPasZoom
    #On empèche la caméra de passer derrière le soleil
    self.cameraRayon = min(self.cameraRayon, planete.distanceSoleil-0.01)
    self.positionneCamera()
    
  def tourneCamera(self, anglex, angley):
    """Tourne la caméra autour de la planète"""
    self.camera.setPos(self.camera, anglex*self.cameraRayon, 0, angley*self.cameraRayon)
    self.positionneCamera()
    
  def deplaceHaut(self):
    self.tourneCamera(0.0,-self.cameraPasRotation)
  def deplaceGauche(self):
    self.tourneCamera(self.cameraPasRotation,0.0)
  def deplaceDroite(self):
    self.tourneCamera(-self.cameraPasRotation,0.0)
  def deplaceBas(self):
    self.tourneCamera(0.0,self.cameraPasRotation)
  def placeCameraAuDessusDe(self, point):
    point = Vec3(point)
    point.normalize()
    self.camera.setPos(point * self.cameraRayon)
    self.positionneCamera()
  ### Fin Gestion de la caméra -----------------------------------------
    
  ### Gestion du clavier/souris ----------------------------------------
  def presseTouche(self, touche):
    """Une touche a été pressée, on l'ajoute a la liste des touches"""
    if general.interface.gui.hoveringOver and touche.startswith("mouse"):
      return
    self.touches.append(touche)
    self.gereTouche()
    
  def relacheTouche(self, touche):
    """Une touche a été relâchée, on l'enlève de la liste des touches"""
    while self.touches.count(touche)>0:
      self.touches.remove(touche)
      
  def gereTouche(self):
    """Gère les touches clavier"""
    for touche in self.touches:
      #On regarde si clique pas sur l'interface
      if not (general.interface.gui.hoveringOver and touche.startswith("mouse")):
        #La touche est configurée
        if touche in self.configClavier.keys():
          action = self.configClavier[touche]
          if action not in self.actions.keys():
            #La touche a été configurée pour faire un truc mais on saît pas ce que c'est
            print "Type d'action inconnue : ", action
          else:
            #On lance la fonction
            self.appelFonction(*self.actions[action])
      
  def lierActionsFonctions(self):
    """On donne des noms gentils à des appels de fonction moins sympas"""
    self.actions = {}
    self.actions["quitter"] = (self.quitter,None)
    self.actions["tournecameraverslagauche"] = (self.tourneCamera,(self.cameraPasRotation,0.0))
    self.actions["tournecameraversladroite"] = (self.tourneCamera,(-self.cameraPasRotation,0.0))
    self.actions["tournecameraverslehaut"] = (self.tourneCamera,(0.0,-self.cameraPasRotation))
    self.actions["tournecameraverslebas"] = (self.tourneCamera,(0.0,self.cameraPasRotation))
    self.actions["zoomplus"] = (self.zoomPlus,None)
    self.actions["zoommoins"] = (self.zoomMoins,None)
    self.actions["modifiealtitude+"] = (general.start.modifieAltitude,(1.0,))
    self.actions["modifiealtitude-"] = (general.start.modifieAltitude,(-1.0,))
    self.actions["affichestat"] = (general.start.afficheStat,None)
    self.actions["screenshot"] = (general.start.screenShot,None)
    
  def appelFonction(self, fonction, parametres):
    """Appel la fonction fonction en lui passant les paramètres décris"""
    if parametres==None:
      fonction()
    elif isinstance(parametres, dict):
      fonction(**parametres)
    elif isinstance(parametres, list) or isinstance(parametres, tuple):
      fonction(*parametres)
    else:
      print "ERREUR : Start.appelFonction, parametres doit être None, un tuple, une liste ou un dictionnaire"
      fonction[parametre]
  ### Fin gestion du clavier/souris ------------------------------------
  
  def quitter(self):
    """Quitte l'application"""
    general.gui.quitter()
  
  def testeSouris(self):
    """Teste ce qui se trouve sous le curseur de la souris"""
    
    planete = general.planete
    
    if base.mouseWatcherNode.hasMouse():
      mpos=base.mouseWatcherNode.getMouse()
      x=mpos.getX()
      y=mpos.getY()
      
      #Test du survol de la souris  
      self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
      base.cTrav.traverse(render)
      if self.myHandler.getNumEntries() > 0:
        self.myHandler.sortEntries()
        objet = self.myHandler.getEntry(0).getIntoNodePath().findNetPythonTag('type')
        if objet.getPythonTag('type') == "sol":
          coord = self.myHandler.getEntry(0).getSurfacePoint(planete.geoide.racine)
          if self.select != None:
            self.select.marcheVers(coord)
            self.select = None
          else:
            idsommet = general.planete.geoide.trouveSommet(coord)
            planete.geoide.survol = idsommet
        elif objet.getPythonTag('type') == "sprite":
            general.interface.afficheTexte("Clic sur le sprite : "+str(objet.getPythonTag('id'))+" cliquez sur le sol où vous voulez qu'il aille", "info")
            self.select = objet.getPythonTag('instance')
        elif objet.getPythonTag('type') == "eau":
            general.interface.afficheTexte("clic dans l'eau", "info")
        else:
          general.interface.afficheTexte("Clic sur un objet au tag inconnu : "+str(objet.getPythonTag('type')), "info")
      else:
        planete.geoide.survol = None
