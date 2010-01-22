#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandac.PandaModules import *

import general
import sys
import math

#Pour l'affichage du Drag&Drop
from treegui.components import Pane

from systemesolaire import SystemeSolaire

class IO:
  preImage = None #L'heure à laquelle la précédente image a été rendue
  
  #Gestion de la caméra
  camera = None
  cameraRayon = 6.0 #Distance de la caméra au centre de la planète
  cameraAngleX = 0.0 #Angle de rotation de la planète selon la verticale
  cameraAngleY = 0.0 #Angle de rotation de la planète selon l'horizontale
  cameraPasRotation = None #Angle entre 2 positions de la caméra
  cameraPasZoom = 0.005 #Pas de zoom
  cameraAngleSurface = 50 #L'angle de la caméra à la surface
  
  #Gestion du clavier
  touches = None #Liste des touches pressées en ce moment
  touchesControles = None #Liste des alt, control, shift, ...
  configClavier = None #Dictionnaire des affectations de commandes
                       #De la forme ["nom de touche"]="action"
                       #Par exemple ["escape"]="quitter"
  actions = None #Dictionnaire des actions accessibles via touches
                 #De la frome ["action"]=(fonction à exécuter,X)
                 #X peut être None
                 #X peut être un tuple (0, 1) ou (0, ) ou (a, b ,c)...
                 #X peut être une liste [a, g]...
                 #X peut être un dictionnaire {"nom parametre":valeur, ...}
                 
  selection = None #Ce que le joueur a sélectionné
  _selection = None #Ce que le joueur avait sélectionné le pind précédent
  groupesUnites = None #Le dictionnaire des groupes d'unités
                 
  def __init__(self):
    #On a rien de sélectionné
    self.selection = []
    
    #On n'a pas de groupes
    self.groupesUnites = {}
    
    #On attrape les valeurs de sensibilités de déplacement de la caméra
    self.seuilMouvementCamera = general.configuration.getConfiguration("Commandes", "parametres", "seuilMouvementCamera", "0.8", float)
    self.rotationCameraX=general.configuration.getConfiguration("Commandes", "parametres", "rotationCameraX", "10.0", float)
    self.rotationCameraY=general.configuration.getConfiguration("Commandes", "parametres", "rotationCameraY", "5.0", float)
    self.cameraPasRotation = general.degVersRad(general.configuration.getConfiguration("Commandes", "parametres", "cameraPasRotation", "1.0", float))

    #On donne des alias à certaines fonctions
    self.lierActionsFonctions()
    
    #On associe des touches à des actions
    self.touches = []
    self.touchesControles = []
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
      #base.buttonThrowers[0].node().setKeystrokeEvent('printTouche')
      base.accept('presseTouche', self.presseTouche)
      base.accept('relacheTouche', self.relacheTouche)
      #base.accept('printTouche', self.printTouche)
      
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
    
    #On met à jour les états sélectionné / non sélectionné des unités
    if self.selection != self._selection:
      if self._selection!=None:
        for sprite in self._selection:
          sprite.deselectionne()
      if self.selection!=None:
        for sprite in self.selection:
          sprite.selectionne()
      self._selection = self.selection[:]

    
    
    if base.mouseWatcherNode !=None:
      #Teste de la position de la souris
      if base.mouseWatcherNode.hasMouse():
        mpos=base.mouseWatcherNode.getMouse()
        x=mpos.getX()
        y=-mpos.getY()
        
        #Regarde si la caméra est proche d'un bord et fait tourner la planète le cas échéant
        if "control" in self.touchesControles:
          if x<-self.seuilMouvementCamera:
            self.camera.setR(self.camera.getR()+self.rotationCameraX*deltaT*(x+self.seuilMouvementCamera)/(1.0-self.seuilMouvementCamera))
          if x>self.seuilMouvementCamera:
            self.camera.setR(self.camera.getR()-self.rotationCameraX*deltaT*(x-self.seuilMouvementCamera)/(1.0-self.seuilMouvementCamera))
          if y<-self.seuilMouvementCamera:
            self.camera.setP(self.camera.getP()+self.rotationCameraY*deltaT*(y+self.seuilMouvementCamera)/(1.0-self.seuilMouvementCamera))
          if y>self.seuilMouvementCamera:
            self.camera.setP(self.camera.getP()-self.rotationCameraY*deltaT*(y-self.seuilMouvementCamera)/(1.0-self.seuilMouvementCamera))
        else:
          if x<-self.seuilMouvementCamera:
            self.tourneCamera(self.cameraPasRotation*(x+self.seuilMouvementCamera)/(1.0-self.seuilMouvementCamera)*deltaT, 0.0)
          if x>self.seuilMouvementCamera:
            self.tourneCamera(self.cameraPasRotation*(x-self.seuilMouvementCamera)/(1.0-self.seuilMouvementCamera)*deltaT, 0.0)
          if y<-self.seuilMouvementCamera:
            self.tourneCamera(0.0, self.cameraPasRotation*(y+self.seuilMouvementCamera)/(1.0-self.seuilMouvementCamera)*deltaT)
          if y>self.seuilMouvementCamera:
            self.tourneCamera(0.0, self.cameraPasRotation*(y-self.seuilMouvementCamera)/(1.0-self.seuilMouvementCamera)*deltaT)
      
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
      
    if planete!=None and isinstance(planete, SystemeSolaire):
      return
      
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
    if planete!=None and isinstance(planete, SystemeSolaire):
      return
            
    self.cameraRayon -= self.cameraRayon*self.cameraPasZoom
    self.cameraRayon = max(self.cameraRayon, 1.0 + planete.geoide.delta + 0.001)
    self.positionneCamera()

  def zoomMoins(self):
    """Éloigne la caméra de la planète"""
    planete = general.planete
    if planete!=None and isinstance(planete, SystemeSolaire):
      return
            
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
    
    if touche in ["alt", "shift", "control"]:#, "lalt", "lshift", "lcontrol", "ralt", "rshift", "rcontrol"]:
      self.touchesControles.append(touche)

    #On regarde si c'est le clavier (touche.find("mouse")==-1) et si on est sur une zone de texte (focus!=None)
    if general.interface.gui.keys.focus and touche.find("mouse")==-1:
      return
    #On regarde si c'est la souris (touche.find("mouse")!=-1) et si on est sur l'interface (hoveringOver!=None)
    if (general.interface.gui.hoveringOver and not general.interface.gui.hoveringOver==general.interface.rectangleDrag) and touche.find("mouse")!=-1:
      return

    self.touches.append(touche)
    self.gereTouche()
    
  def printTouche(self, touche):
    print "key",touche
    
  def relacheTouche(self, touche):
    """Une touche a été relâchée, on l'enlève de la liste des touches"""
    while self.touches.count(touche)>0:
      self.touches.remove(touche)
      if touche+"-off" in self.configClavier.keys():
        action = self.configClavier[touche+"-off"]
        if action not in self.actions.keys():
          #La touche a été configurée pour faire un truc mais on saît pas ce que c'est
          print "Type d'action inconnue : ", action
        else:
          #On lance la fonction
          self.appelFonction(*self.actions[action])
    while self.touchesControles.count(touche)>0:
      self.touchesControles.remove(touche)
            
  def gereTouche(self):
    """Gère les touches clavier"""
    for touche in self.touches:
      #On ajoute les touches de modifications dans l'ordre alphabétique genre alt+shit-r indique que les touche alt, shift et r sont pressées en même temps
      if self.touchesControles:
        tch=touche
        touche = "+".join(sorted(self.touchesControles))+"-"+touche
        #Si jamais la touche avec les modificateurs appliquee n'est pas dans la config, on teste sans
        if not touche in self.configClavier.keys():
          touche=tch
      #On regarde si clique pas sur l'interface
      if not touche.startswith("mouse") or not general.interface.gui.hoveringOver or general.interface.gui.hoveringOver==general.interface.rectangleDrag:
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
    self.actions["modifiealtitude+"] = (self.modifieAltitude,(1.0,))
    self.actions["modifiealtitude-"] = (self.modifieAltitude,(-1.0,))
    self.actions["fabriquegroupe1"] = (self.fabriqueGroupe,(1,))
    self.actions["fabriquegroupe2"] = (self.fabriqueGroupe,(2,))
    self.actions["fabriquegroupe3"] = (self.fabriqueGroupe,(3,))
    self.actions["fabriquegroupe4"] = (self.fabriqueGroupe,(4,))
    self.actions["fabriquegroupe5"] = (self.fabriqueGroupe,(5,))
    self.actions["fabriquegroupe6"] = (self.fabriqueGroupe,(6,))
    self.actions["fabriquegroupe7"] = (self.fabriqueGroupe,(7,))
    self.actions["fabriquegroupe8"] = (self.fabriqueGroupe,(8,))
    self.actions["fabriquegroupe9"] = (self.fabriqueGroupe,(9,))
    self.actions["fabriquegroupe0"] = (self.fabriqueGroupe,(0,))
    self.actions["appelgroupe1"] = (self.appelGroupe,(1,))
    self.actions["appelgroupe2"] = (self.appelGroupe,(2,))
    self.actions["appelgroupe3"] = (self.appelGroupe,(3,))
    self.actions["appelgroupe4"] = (self.appelGroupe,(4,))
    self.actions["appelgroupe5"] = (self.appelGroupe,(5,))
    self.actions["appelgroupe6"] = (self.appelGroupe,(6,))
    self.actions["appelgroupe7"] = (self.appelGroupe,(7,))
    self.actions["appelgroupe8"] = (self.appelGroupe,(8,))
    self.actions["appelgroupe9"] = (self.appelGroupe,(9,))
    self.actions["appelgroupe0"] = (self.appelGroupe,(0,))
    self.actions["selectionnetout"] = (self.selectionneTout, None)
    self.actions["debclic"] = (self.debClic,None)
    self.actions["finclic"] = (self.finClic,None)
    self.actions["affichestat"] = (self.afficheStat,None)
    self.actions["screenshot"] = (self.screenShot,None)
    self.actions["selectionne"] = (self.selectionne,None)
    self.actions["dragdrop"] = (self.dragDrop,None)
    self.actions["console"] = (self.afficheConsole,None)
    
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
    #Purge la sélection actuelle
    if self.selection:
      self.selection=[]
      return
    general.interface.quitter()
  
  def testeSouris(self, coords=None):
    """Teste ce qui se trouve sous le curseur de la souris"""
    planete = general.planete
    
    if coords==None:
      if base.mouseWatcherNode.hasMouse():
        mpos=base.mouseWatcherNode.getMouse()
        x=mpos.getX()
        y=mpos.getY()
      else:
        #La souris n'est pas sur l'écran
        return
    else:
      x,y=coords
      
    #Test du survol de la souris  
    self.pickerRay.setFromLens(base.camNode, x, y)
    base.cTrav.traverse(render)
    if self.myHandler.getNumEntries() > 0:
      self.myHandler.sortEntries()
      objet = self.myHandler.getEntry(0).getIntoNodePath().findNetPythonTag('type')
      
      ### clic sur le sol ### ---------------------------------------------------------------
      if objet.getPythonTag('type') == "sol":
        coord = self.myHandler.getEntry(0).getSurfacePoint(planete.geoide.racine)
        if self.selection:
          for sprite in self.selection:
            sprite.stop()
            sprite.marcheVers(coord)
          print self.selection,"va vers", coord
        else:
          idsommet = general.planete.geoide.trouveSommet(coord)
          planete.geoide.survol = idsommet

      ### clic sur un sprite ### ------------------------------------------------------------
      elif objet.getPythonTag('type') == "sprite":
          print "clic sprite"
          if "shift" not in self.touchesControles:
            self.selection = []
          if objet.getPythonTag('instance') not in self.selection:
            self.selection.append(objet.getPythonTag('instance'))

      ### clic sur une planete du systeme solaire ### ----------------------------------------
      elif objet.getPythonTag('type') == "planete":
          nomPlanete = objet.getPythonTag("nomPlanete")
          from gui import MenuVierge
          if isinstance(general.interface.menuCourant, MenuVierge):
            if nomPlanete.lower().strip() != "--n/a--":
              general.interface.planeteVierge(nomPlanete)
          else:
            general.interface.changeMenuVers(MenuVierge)
      else:
        print objet
        general.interface.afficheTexte("Clic sur un objet au tag inconnu : %(a)s", parametres={"a": str(objet.getPythonTag('type'))}, type="info")
    else:
      if planete!=None and isinstance(planete, SystemeSolaire):
        return
      if "shift" not in self.touchesControles:
        self.selection = []
      planete.geoide.survol = None
        
        
        
        
        
        
  ### Autres -----------------------------------------------------------
  
  posClic = None
  isDragging = False
  seuilDrag = 100
  
  def debClic(self):
    """Le bouton gauche de la souris a été pressé"""
    if self.posClic==None:
      if base.mouseWatcherNode.hasMouse():
        mpos=base.mouseWatcherNode.getMouse()
        x=mpos.getX()+1.0
        y=-mpos.getY()+1.0
        self.posClic=(x*base.win.getXSize()/2,y*base.win.getYSize()/2)
    else:
      if base.mouseWatcherNode.hasMouse():
        mpos=base.mouseWatcherNode.getMouse()
        x=mpos.getX()+1.0
        y=-mpos.getY()+1.0
        newPos=(x*base.win.getXSize()/2,y*base.win.getYSize()/2)
        if not self.isDragging: #Si on sait qu'on fait du d&d
            d = (newPos[0]-self.posClic[0])*(newPos[0]-self.posClic[0]), (newPos[1]-self.posClic[1])*(newPos[1]-self.posClic[1])
            if d[0]>self.seuilDrag or d[1]>self.seuilDrag:
              self.isDragging = True
        else:
          if general.interface.rectangleDrag==None:
            general.interface.rectangleDrag = general.interface.add(Pane())
            general.interface.rectangleDrag.color = (1.0, 1.0, 1.0, 0.5)
          minx = min(self.posClic[0], newPos[0])
          miny = min(self.posClic[1], newPos[1])
          maxx = max(self.posClic[0], newPos[0])
          maxy = max(self.posClic[1], newPos[1])
          
          general.interface.rectangleDrag.doPlacement({"x":minx, "y": miny})
          if maxx - minx!=0:
            general.interface.rectangleDrag.width = maxx - minx
          if maxy - miny!=0:
            general.interface.rectangleDrag.height = maxy - miny

    
  def finClic(self):
    """Le bouton gauche de la souris a été relâché"""
    touche = None
    params = None
    
    #On cache l'affichage du rectangle de D&D s'il existait
    if general.interface.rectangleDrag!=None:
      general.interface.remove(general.interface.rectangleDrag)
      general.interface.rectangleDrag = None
    
    #Si on draggais
    if self.isDragging:
      self.isDragging = False
      #On regarde si on a un truc à faire à la fin du drag
      if "drag-off" in self.configClavier.keys():
        touche = "drag-off"
        newPos=None
        if base.mouseWatcherNode.hasMouse():
          mpos=base.mouseWatcherNode.getMouse()
          x=mpos.getX()+1.0
          y=-mpos.getY()+1.0
          newPos=(x*base.win.getXSize()/2,y*base.win.getYSize()/2)
        if newPos==None:
          #Le drag & drop est sorti de l'écran
          self.posClic=None
          return
        params = (self.posClic, newPos)
      else:
        self.posClic=None
        return
    else:
      #On regarde si on a un truc à faire pour un clic normal
      if "clic" in self.configClavier.keys():
        touche = "clic"
        params = (self.posClic,)
      else:
        self.posClic=None
        return
      
    action = self.configClavier[touche]
    if action not in self.actions.keys():
      #La touche a été configurée pour faire un truc mais on saît pas ce que c'est
      print "Type d'action inconnue : ", action
    else:
      fonction, parametres = self.actions[action]
      if params!=None:
        if parametres==None:
          parametres = []
        for param in params:
          parametres.append(param)
      #On lance la fonction
      self.appelFonction(fonction, parametres)
      
    self.posClic=None
    
  def pointEcranVersRender2D(self, point):
    """Passe un point en pixels dans le champ [-1:1][-1:1] de render2D"""
    if point==None:
      return None
    return (point[0]/base.win.getXSize()*2-1.0, -(point[1]/base.win.getYSize()*2-1.0))
    
  def selectionne(self, coordSouris):
    """Fait un clic"""
    if coordSouris==None:
      return
    self.testeSouris()
   
  def dragDrop(self, coordDeb, coordFin):
    """Gère le drag&drop"""
    
    if general.joueurLocal == None:
      #on a pas de joueur
      return
      
    #"shift+d&d" ajoute les unités à la sélection courante, "d&d" remplace la sélection courante par ce qui est dans le rectangle
    if not "shift" in self.touchesControles:
      self.selection = []
    
    #On normalise les coordonnées du rectangle de sélection
    minx = min(coordDeb[0], coordFin[0])
    miny = min(coordDeb[1], coordFin[1])
    maxx = max(coordDeb[0], coordFin[0])
    maxy = max(coordDeb[1], coordFin[1])
    pt1 = self.pointEcranVersRender2D((minx,miny))
    pt2 = self.pointEcranVersRender2D((maxx,maxy))
    
    for sprite in general.planete.spritesJoueur:
      #On ne prend en compte que les sprites du joueur local
      if sprite.joueur == general.joueurLocal:
        pos = general.map3dToRender2d(sprite.rac, Vec3(0.0,0.0,0.0))
        if pos!=None:
          if pos[0]>=pt1[0] and pos[0]<=pt2[0]:
            if pos[1]>=pt1[1] and pos[1]<=pt2[1]:
              if general.ligneCroiseSphere(sprite.position, self.camera.getPos(), (0.0,0.0,0.0), 1.0) == None:
                if sprite not in self.selection:
                  self.selection.append(sprite)
  
  def afficheStat(self):
    #Affiche le contenu du chronomètre
    general.afficheStatChrono()
    
  def afficheConsole(self):
    general.interface.afficheConsole()
    
  def fabriqueGroupe(self, idGroupe):
    self.groupesUnites[idGroupe]=self.selection[:]
    print "création du groupe",idGroupe,"contenant :",self.selection
    
  def appelGroupe(self, idGroupe):
    """un "1" sélectionne le groupe 1 uniquement, si "shift+1" ajoute le groupe 1 à la sélection courante"""
    if not idGroupe in self.groupesUnites:
      print "groupe",idGroupe,"no défini"
      if not "shift" in self.touchesControles:
        self.selection = []
    else:
      #On supprime les unités mortes depuis la création du groupe
      selection = self.groupesUnites[idGroupe][:]
      for sprite in self.groupesUnites[idGroupe]:
        if sprite not in general.planete.spritesJoueur and sprite not in general.planete.spritesNonJoueur:
          selection.remove(sprite)
          
      #On met à jour la sélection et les infos de groupe
      self.groupesUnites[idGroupe] = selection[:]
      if not "shift" in self.touchesControles:
        self.selection = selection
      else:
        for unite in selection:
          if unite not in self.selection:
            self.selection.append(unite)
      
        #On met à jour les infos de groupe
    
    print "sélection est maintenant :",self.selection
    
  def selectionneTout(self):
    self.selection = []
    if not isinstance(general.planete, SystemeSolaire):
      for sprite in general.planete.spritesJoueur:
        if sprite.joueur == general.joueurLocal:
          self.selection.append(sprite)

  def modifieAltitude(self, direction):
    """Change l'altitude d'un point, si direction>0 alors l'altitude sera accrue sinon diminuée"""
    self.testeSouris()
    if general.planete.geoide.survol == None:
      return
    
    ndelta = general.planete.geoide.delta * direction * 0.01
    general.planete.geoide.elevePoint(general.planete.geoide.survol, ndelta)
    
  def screenShot(self):
    base.screenshot("test")
  ### Fin autres -------------------------------------------------------  
