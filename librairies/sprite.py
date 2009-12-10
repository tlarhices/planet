#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general
import math
import random
from ai import AI

from pandac.PandaModules import *

class Sprite:
  """Un objet du monde"""
  id = None
  planete = None #La planète sur laquelle l'objet se trouve
  position = None #La position dans l'espace de cet objet
  modele = None #Le modèle 3D de l'objet
  fichierModele = None #Le nom du fichier du modèle 3D (utilisé pour la sauvegarde)
  fichierSymbole = None #Symbole remplaçant le modèle quand on dézoome
  icone = None #Icone sur la minimap
  altCarre = None #L'altitude de cet objet
  symbole=None
  
  vitesse = None
  
  marcheVersTab = None #La liste des sommets vers lequel l'objet se dirige
  
  joueur = None #Le joueur qui possède cet objet
  contenu = None #Ce qui se trouve dans l'objet
  vie = None #L'état dans lequel se trouve l'objet
  typeMort = None
  
  bouge = None #Si True, alors l'objet peut bouger (personnage, véhicule, ...) sinon il est statique (arbre, bâtiment, ...)
  aquatique = None #Si True, alors l'objet peut aller dans l'eau, sinon il est détruit
  zoneContact = None #Les coordonnées de la zone de contact
  
  rac = None #Ce qui fait que le sprite garde les pieds en bas
  racine = None #Ce qui fait que le sprite garde la tête en haut
  
  inertie = None
  inertieSteering = None
  terminalVelocity = None
  distanceProche = None
  
  nocturne = None #S'il est nocturne, la nuit ne le tue pas
  
  blipid = None #L'id du blip sur la carte
  
  ai = None
  pileTempsAppliqueGraviteObjetsFixes = None
  seuilRecalculPhysique = None

  
  def __init__(self, id, position, fichierDefinition, planete, joueur):
    """
    Fabrique un nouvel objet
    position : là où l'objet se trouve
    modele : le nom du fichier 3D à charger
    planete : la planète de laquelle cet objet dépend
    """
    self.planete = planete
    self.joueur = joueur
    self.id = id
    self.miseAJourPosition(position)
    

    definition = general.configuration.parseSprite(fichierDefinition)
    
    self.modele = None
    self.marcheVersTab = []
    self.inertie = [0.0,0.0,0.0]
    self.inertieSteering = [0.0,0.0,0.0]
    self.rac = NodePath("racine-sprite")
    self.racine = NodePath("racine-sprite")
    self.pileTempsAppliqueGraviteObjetsFixes = 1000.0

    self.fichierModele = definition["modele"]
    self.fichierSymbole = definition["symbole"]
    self.icone = definition["icone"]
    self.vie=definition["vie"]
    self.nocturne = definition["nocturne"]
    self.terminalVelocity = definition["terminalvelocity"]
    self.angleSolMax = general.configuration.getConfiguration("ai", "navigation", "angleSolMax", "70.0")
    self.distanceProche = definition["distanceProche"]
    self.seuilToucheSol = definition["seuilToucheSol"]
    self.constanteGravitationelle = definition["constanteGravitationelle"]
    self.vitesse = definition["vitesse"]
    self.distanceSymbole = definition["distancesymbole"]
    self.bouge = definition["bouge"]
    self.aquatique = definition["aquatique"]
    if definition["ai"] != "none" and self.bouge:
      self.ai = AI(self)
      self.ai.choisitComportement(definition["ai"])
    self.seuilRecalculPhysique = definition["seuilrecalculphysique"]
    
  def pointeRacineSol(self):
    """Tourne la racine des éléments graphiques pour maintenir les "pieds" du sprite par terre"""
    #Positionne le modèle et le fait pointer vers le centre de la planète (Z pointant sur la planète)
    self.rac.reparentTo(self.planete.racine)
    self.rac.setPos(*self.position)
    self.rac.lookAt(self.planete.racine,0,0,0)
    #Tourne le modèle pour que sa tête soit en "haut" (Y pointant vers l'extérieur de la planète)
    self.racine.reparentTo(self.rac)
    self.racine.setP(90)
    self.racine.setScale(0.01)
    
    #Affiche le racine devant tout pour le debug
    #self.rac.setBin('fixed', -1)
    #self.rac.setDepthTest(False)
    #self.rac.setDepthWrite(False)
    #self.rac.setLightOff()
    
  def ping(self, temps):
    """
    Appelé à chaque image, met à jour l'état de l'objet
    temps : le nombre de secondes depuis la dernière mise à jour
    """
    
    if self.modele==None:
      self.fabriqueModel()
      if self.modele==None:
        self.tue("Impossible de charger le modele")
    
    if self.vie<=0:
      return False
      
    #Fait marcher
    if self.marcheVersTab != None:
      if len(self.marcheVersTab) > 0:
        self.deplace(self.marcheVersTab[0], temps)
        if general.distanceCarree(self.position, self.versCoord(self.marcheVersTab[0])) < self.distanceProche:
          self.marcheVersTab.pop(0)

    #Fait tomber
    self.appliqueGravite(temps)
    
    if self.ai != None:
      self.ai.ping(temps)

    #Deplace
    self.appliqueInertie(temps)

    if self.vie<=0:
      return False
      
    #Recalcule la verticale du modèle
    self.MAJSymbole()
    self.blip()
    return True
    
  def blip(self):
    if self.blipid!=None:
      try:
        general.gui.menuCourant.miniMap.majBlip(self.blipid,self.position,self.icone)
      except AttributeError:
        self.blipid=None
    else:
      try:
        if self.icone != None and self.icone != "none":
          self.blipid = general.gui.menuCourant.miniMap.ajoutePoint3D(self.position,self.icone)
      except AttributeError:
        pass
  
  def testeSol(self, temps):
    """Regarde l'angle entre la normale de la face et le sprite qui s'y tient"""
    sp = Vec3(*general.normaliseVecteur(self.position))
    fc = Vec3(*self.planete.trouveFace(self.position).calculNormale())
    angle = sp.angleDeg(fc)
    if angle > self.angleSolMax:
      self.inertie = self.inertie[0]+fc.getX()*temps, self.inertie[1]+fc.getY()*temps, self.inertie[2]+fc.getZ()*temps
    
  def appliqueGravite(self, temps):
    """Fait tomber les objets sur le sol"""
    altitudeCible = self.planete.altitudeCarre(self.position)
    
    if not self.bouge:
      self.appliqueGravite = self.appliqueGraviteObjetsFixes
      self.appliqueGravite(temps)
      return
    
    if self.altCarre < altitudeCible:
      #Si on est dans le sol, on se place sur le sol d'un seul coup
      self.miseAJourPosition(general.multiplieVecteur(general.normaliseVecteur(self.position), math.sqrt(altitudeCible)))
      self.inertie = (0.0,0.0,0.0)
    elif self.altCarre > altitudeCible+self.seuilToucheSol:
      #Si on est au dessus, on tombe sur la surface
      #On calcul le vecteur -planete-sprite> et on lui donne comme longueur le déplacement que l'on veut faire
      haut = general.multiplieVecteur(general.normaliseVecteur(self.position), -self.constanteGravitationelle)
      #On retire ce vecteur à l'inertie (fait un vecteur -sprite-planete>)
      self.inertie = self.inertie[0]+haut[0]*temps, self.inertie[1]+haut[1]*temps, self.inertie[2]+haut[2]*temps
    else:
      self.testeSol(temps) #On est sur le sol, on teste si on peut se tenir debout dessus
      
  def appliqueGraviteObjetsFixes(self, temps):
    """Place les objets qui ne bougent pas sur le sol"""
    self.pileTempsAppliqueGraviteObjetsFixes+=temps
    
    if self.pileTempsAppliqueGraviteObjetsFixes<self.seuilRecalculPhysique+random.random():
      return
      
    self.pileTempsAppliqueGraviteObjetsFixes = 0.0
    
    altitudeCible = self.planete.altitudeCarre(self.position)
    if self.altCarre < altitudeCible or self.altCarre > altitudeCible + self.seuilToucheSol:
      #On place l'objet sur le sol d'un seul coup
      self.miseAJourPosition(general.multiplieVecteur(general.normaliseVecteur(self.position), math.sqrt(altitudeCible)))
      self.inertie = (0.0,0.0,0.0)
      
  def appliqueInertie(self, temps):
    if general.normeVecteur(self.inertie)>self.terminalVelocity:
      self.inertie = general.multiplieVecteur(general.normaliseVecteur(self.inertie), self.terminalVelocity)
    self.inertie = self.inertie[0] + self.inertieSteering[0], self.inertie[1] + self.inertieSteering[1], self.inertie[2] + self.inertieSteering[2]
    self.inertieSteering = [0.0,0.0,0.0]
    self.miseAJourPosition((self.position[0]+self.inertie[0]*temps, self.position[1]+self.inertie[1]*temps, self.position[2]+self.inertie[2]*temps))

    
  def versCoord(self, cible):
    """Si cible est une coordonnée, retourne cette dernière, sinon extrait les coordonnées"""
    try:
      cible = list(cible)
    except TypeError:
      cible=[cible, ]
      
    if len(cible)==1:
      cible = self.planete.sommets[cible[0]]

    return cible
    
      
  def deplace(self, cible, temps):
    """
    Déplace un personnage entre 2 points
    TODO : Tester si le passage est toujours valide (changements géographiques,...) jusqu'au prochain point, recalculer si besoin est
    """
      
    cible = self.versCoord(cible)
      
    vecteurDeplacement = general.multiplieVecteur(general.normaliseVecteur((cible[0]-self.position[0], cible[1]-self.position[1], cible[2]-self.position[2])), self.vitesse*temps)
    
    #Affiche le déplacement un personnage sur l'écran
    #top = self.planete.racine.attachNewNode(self.dessineLigne((random.random(),random.random(),random.random()), self.position, (self.position[0] + vecteurDeplacement[0], self.position[1] + vecteurDeplacement[1], self.position[2] + vecteurDeplacement[2])))
    #top.setBin('fixed', -1)
    #top.setDepthTest(False)
    #top.setDepthWrite(False)
    #top.setLightOff()
    
    self.position = (self.position[0] + vecteurDeplacement[0], self.position[1] + vecteurDeplacement[1], self.position[2] + vecteurDeplacement[2])
    #self.planete.afficheTexte(self.id+" marche vers "+str(cible))
    self.miseAJourPosition(self.position)
      
  def miseAJourPosition(self, position):
    """Change la position de l'objet"""
    self.position = position
    self.altCarre = general.normeVecteurCarre(self.position)
    if self.altCarre < self.planete.niveauEau*self.planete.niveauEau:
      if self.aquatique:
        #Nage
        pass
      else:
        #Se noie
        self.tue("noyade")
    if self.modele != None:
      self.pointeRacineSol()
      
  def tue(self, type):
    """Gère la mort du sprite"""
    general.gui.afficheTexte(self.id+" est mort par "+type, "mort")
    self.vie = 0
    self.typeMort = type
    if self.rac!=None:
      self.rac.detachNode()
      self.rac.removeNode()
      self.rac = None
    if self.racine!=None:
      self.racine.detachNode()
      self.racine.removeNode()
      self.racine = None
    if self.modele!=None:
      self.modele.detachNode()
      self.modele.removeNode()
      self.modele = None
    self.symbole = None
    if self.blipid!=None:
      general.gui.menuCourant.miniMap.enlevePoint(self.blipid)
    if self.ai != None:
      self.ai.clear()
      self.ai = None
    
  def sauvegarde(self):
    """Retoune une chaine qui représente l'objet"""
    nom = "none"
    if self.joueur != None:
      nom = self.joueur.nom
    out = "s:"+self.id+":"+nom+":"+self.fichierModele+":"+self.fichierSymbole
    out += ":"+str(self.position)+":"+str(self.vitesse)+":"+str(self.vie)+":"+str(self.bouge)+":"+str(self.aquatique)+":\r\n"
    for elem in self.marcheVersTab:
      out+="sm:"+self.id+":"+elem+":\r\n"
    if self.contenu != None:
      print "SPRITE :: Erreur : contenu non géré dans la sauvegarde"
    return out
    
  def marcheVers(self, cible):
    """Calcule la trajectoire pour aller du point actuel à la cible"""
    idP = self.planete.trouveSommet(self.position)
    idC = self.planete.trouveSommet(cible)
    self.marcheVersTab = self.planete.aiNavigation.aStar(idP, idC)
    if self.marcheVersTab!=None:
      self.marcheVersTab.append(cible)
      #self.planete.afficheTexte(self.id+" requête de promenade : "+str(self.marcheVersTab))
      return True
    else:
      #self.planete.afficheTexte(self.id+" impossible d'aller à "+str(cible))
      pass
    return False
    
  def fabriqueModel(self):
    """Produit le modèle ou le sprite"""
    if self.vie <=0:
      return None
      
    self.modele = NodePath(FadeLODNode('lod'))
    
    if self.fichierModele == None or self.fichierModele=="none":
      self.modele = None
      return
    if self.fichierModele.endswith(".png"):
      tmp = self.fabriqueSprite(self.fichierModele)
    else:
      tmp = loader.loadModel(self.fichierModele)
      tmp.setScale(3.0)
    tmp.reparentTo(self.modele)
    self.modele.node().addSwitch(self.distanceSymbole, 0) 
    
    symbole = self.fabriqueSymbole(self.fichierSymbole)
    symbole.reparentTo(self.modele)
    
    self.modele.node().addSwitch(9999999, self.distanceSymbole) 
    
    self.modele.setPythonTag("type","sprite")
    self.modele.setPythonTag("id",self.id)
    self.modele.setPythonTag("instance",self)
    self.modele.reparentTo(self.racine)
    self.pointeRacineSol()
    return self.modele
    
  def fabriqueSymbole(self, fichierSymbole):
    """Affiche une icône dont la taille ne change pas avec la distance à la caméra"""
    
    if fichierSymbole=="none":
      self.symbole=NodePath("pas de symbole")
      return self.symbole
    #On calcule la distance à la caméra pour avoir le facteur de corection d'échelle
    if base.camera != None:
      taille = general.normeVecteur(base.camera.getPos(self.modele))
    else:
      taille = 1.0
    #On construit l'objet
    self.symbole = self.fabriqueSprite(fichierSprite = fichierSymbole, taille = taille)
    #On lui dit de ne pas être dérangé par les sources lumineuses
    self.symbole.setLightOff()
    
    #Permet de l'afficher devant toute géométrie
    #self.symbole.setBin('fixed', -1)
    #self.symbole.setDepthTest(False)
    #self.symbole.setDepthWrite(False)

    return self.symbole
    
  def MAJSymbole(self):
    """Change l'échelle du symbole pour le garder toujours à la même taille"""
    if self.symbole!=None and self.racine!=None:
      #On calcule la distance à la caméra pour avoir le facteur de corection d'échelle
      taille = general.normeVecteur(base.camera.getPos(self.racine))
      #On change l'échelle
      self.symbole.setScale(taille*0.005, taille*0.005, taille*0.005)
    
    
  def makeDot(self):
    gvf = GeomVertexFormat.getV3cp()

    # Create the vetex data container.
    vertexData = GeomVertexData('SpriteVertices',gvf,Geom.UHStatic)

    # Create writers
    vtxWriter = GeomVertexWriter(vertexData,'vertex')
    clrWriter = GeomVertexWriter(vertexData,'color') 
    vtxWriter.addData3f(0.0,0.0,0.0)
    clrWriter.addData3f(1,1,1) 
       
    # Create a GeomPrimitive object and fill with the vertices.
    geom = Geom(vertexData)
    points = GeomPoints(Geom.UHStatic)
    points.setIndexType(Geom.NTUint32)
    points.addVertex(0)

    points.closePrimitive()
    geom.addPrimitive(points)
    geomNode = GeomNode('Sprites')
    geomNode.addGeom(geom)
    cloud = NodePath(geomNode)
    cloud.setRenderModePerspective(True)
    #cloud.setRenderModeThickness(1.0)
    TS = TextureStage.getDefault()
    cloud.setTexGen(TS, TexGenAttrib.MPointSprite)
    #cloud.setTexScale(TS,-1,1) 
    return cloud
    
  def fabriqueSprite(self, fichierSprite, taille=1.0, type="carte"):
    """Construit un nouveau sprite"""
    
    racine = NodePath("sprite")
    
    if type=="carte":
      #Fabrique un carré
      cardMaker = CardMaker('sprite')
      cardMaker.setFrame(-0.5, 0.5, 0.0, 1.0)
      cardMaker.setHasNormals(True)
    
      #Construit une carte (un plan)
      card1 = racine.attachNewNode(cardMaker.generate())
      #On fait tourner la carte pour quelle pointe toujours vers la caméra
      #Elle rotationne autour d'un axe uniquement (garde ses pieds vers le sol)
      card1.setBillboardAxis()
    elif type=="point":
      card1 = self.makeDot()
      card1.reparentTo(racine)
    else:
      print "SPRITE :: Erreur :: type de carte inconnu :", type
      return self.fabriqueSprite(fichierSprite=fichierSprite, taille=1.0, type="carte")
      
    tex = loader.loadTexture(fichierSprite)
    card1.setTexture(tex)
    #Active la transprence
    card1.setTransparency(TransparencyAttrib.MDual)
    #Fait une mise à l'échelle
    card1.setScale(taille, taille, taille)
    
    #Les lignes suivantes font dessiner le sprite au dessus de tout le reste
    #Utile pour débugger
    #card1.setBin('fixed', -1)
    #card1.setDepthTest(False)
    #card1.setDepthWrite(False)
    return racine
    
  def dessineLigne(self, couleur, depart, arrivee):
    """Dessine une ligne de depart vers arrivée et ne fait pas de doublons"""
    ls = LineSegs()
    ls.setColor(*couleur)
    ls.setThickness(1.0)
    ls.moveTo(*depart)
    ls.drawTo(*arrivee)
    return ls.create()

class SpritePlan(Sprite):
  """Support d'objets non ponctuels"""
  point1 = None
  point2 = None
  
  def __init__(self, id, point1, point2, modele, symbole, planete, joueur):
    self.point1, self.point2, position = self.preparePoints(point1, point2)
    
    Sprite.__init__(self, id, position, modele, symbole, planete, joueur)

  def preparePoints(self, point1, point2):
    point1 = (min(point1[0], point2[0]), min(point1[1], point2[1]), min(point1[2], point2[2]))
    point2 = (max(point1[0], point2[0]), max(point1[1], point2[1]), max(point1[2], point2[2]))
    position = (point1[0]+point2[0])/2.0, (point1[1]+point2[1])/2.0, (point1[2]+point2[2])/2.0
    return point1, point2, position

  def miseAJourPosition(self, point1, point2):
    self.point1, self.point2, position = self.preparePoints(point1, point2)
    Sprite.miseAJourPosition(self, position)
    
  def testeSol(self):
    Sprite.testeSol(self)

class Nuage(Sprite):
  """Génère un nuage aléatoirement"""
  densite = None
  
  def __init__(self, densite, taille, planete):
    Sprite.__init__(self, id="nuage", position=(0.01,0.01,0.01), modele="none", symbole="none", icone="none", distanceSymbole=999999, vie=100, terminalVelocity=1000, distanceProche=1000, seuilToucheSol=1000, constanteGravitationelle=1000, nocturne=True, vitesse=1000, planete=planete, joueur=None)
    self.densite = densite
    self.taille = taille
    self.planete = planete
    
  def tue(self, type):
    """Un nuage ne peut pas mourrir"""
    return
    #if type=="noyade":
    #  return
    #else:
    #  Sprite.tue(self, type)
    
  def ping(self, temps):
    """Les nuages ne sont pas affectés par la gravité"""
    self.deplace(temps)
    #self.blip()
    if self.vie<=0:
      return False
    return True
    
  def blip(self):
    """Les nuages n'apparaissent pas sur le radar"""
    pass
    
  def deplace(self, temps):
    """Promène le nuage sur l'écran"""
    if self.racine == None or self.modele==None:
      return
    #Modele est centré sur la planète, donc les rotations le promènent un peu tout autour
    f = random.random()*2.0
    self.modele.setH(self.modele.getH()+random.random()*temps*f)
    self.modele.setP(self.modele.getP()+random.random()*temps*f)
    self.modele.setR(self.modele.getR()+random.random()*temps*f)
    #Faire tourner la racine change le profile du nuage présenté à la caméra et donc sa forme pour donner l'impression qu'il évolue
    f=1
    self.racine.setH(self.racine.getH()+random.random()*temps*f)
    self.racine.setP(self.racine.getP()+random.random()*temps*f)
    self.racine.setR(self.racine.getR()+random.random()*temps*f)
    self.position = self.n1.getPos(self.planete.racine)
    
  def fabriqueModel(self):
    """Construit le nuage"""
    #Choisit une position du nuage selon un sommet aléatoire
    centre = random.choice(self.planete.sommets)
    
    #Facteur d'étalement du nuage selon les 3 axes en espace monde
    dx, dy, dz = 1.2,1.2,1.2
    fact = general.normeVecteur((dx, dy, dz))
        
    distanceSoleil = self.planete.distanceSoleil
        
    #Place le "centre" du nuage
    self.modele = NodePath("nuage")#NodePath(FadeLODNode('nuage'))
    self.modele.setPos(*general.multiplieVecteur(general.normaliseVecteur(centre), self.planete.niveauCiel-0.01))
    self.racine = NodePath("nuage-elem")
    
    import os
    textures = os.listdir(os.path.join(".","data","textures","nuages"))
    
    #Ajoute les prouts nuageux un par un
    for i in range(0, self.densite):
      #Fabrique un nouveau prout
      nuage = NodePath(FadeLODNode('lod'))
      tex="./data/textures/nuages/"+random.choice(textures)
      self.fabriqueSprite(tex, taille=1, type="point").reparentTo(nuage)
      if i==0:
        nuage.node().addSwitch(99999, 0) 
        self.n1=nuage
      else:
        nuage.node().addSwitch(float(i)/float(self.densite)*distanceSoleil, 0) 
        
      #nuage.setBillboardPointWorld()
      
      #On le décale par rapport au "centre"
      if i!=0:
        r = (random.random()*dx, random.random()*dy, random.random()*dz)
      else:
        #mais on garde le tout premier "prout" au milieu
        r = (0.0, 0.0, 0.0)
        
      #On coince le nuage dans le ciel
      v=general.multiplieVecteur(general.normaliseVecteur(r), self.planete.niveauCiel-0.01+(self.planete.niveauCiel-self.planete.delta-1.0)*random.random())
      r = v[0]-centre[0], v[1]-centre[1], v[2]-centre[2]
      nuage.setPos(*r)
      
      #On diminue la taille du prout s'il est loin du centre
      nuage.setScale(max((fact-general.normeVecteur(r)), 0.001*fact)/fact)
      #On diminue l'opacité du prout s'il est loin du centre
      nuage.setAlphaScale(max((fact-general.normeVecteur(r)), 0.001*fact)/fact)
      nuage.reparentTo(self.racine)
    self.racine.reparentTo(self.modele)
    #On redimentionne le bestiau
    self.modele.setScale(self.taille)
    #On optimise les envois à la carte graphique
    self.racine.flattenStrong()
    self.modele.reparentTo(self.planete.racine)
    #self.modele.setBin('fixed', -1)
    #self.modele.setDepthTest(False)
    #self.modele.setDepthWrite(False)
    #self.modele.setLightOff()
    
    return self.modele
    
  def sauvegarde(self):
    """Les nuages ne sont là que pour faire joli"""
    return "\r\n"
