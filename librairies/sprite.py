#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general
import math
import random

from pandac.PandaModules import *

class Sprite:
  """Un objet du monde"""
  id = None
  planete = None #La planète sur laquelle l'objet se trouve
  position = None #La position dans l'espace de cet objet
  modele = None #Le modèle 3D de l'objet
  fichierModele = None #Le nom du fichier du modèle 3D (utilisé pour la sauvegarde)
  fichierSymbole = None
  altCarre = None #L'altitude de cet objet
  symbole=None
  
  vitesse = 0.01 #(en unité/s)
  
  marcheVersTab = None #La liste des sommets vers lequel l'objet se dirige
  
  joueur = None #Le joueur qui possède cet objet
  contenu = None #Ce qui se trouve dans l'objet
  vie = None #L'état dans lequel se trouve l'objet
  
  bouge = None #Si True, alors l'objet peut bouger (personnage, véhicule, ...) sinon il est statique (arbre, bâtiment, ...)
  aquatique = None #Si True, alors l'objet peut aller dans l'eau, sinon il est détruit
  zoneContact = None #Les coordonnées de la zone de contact
  
  rac = None #Ce qui fait que le sprite garde les pieds en bas
  racine = None #Ce qui fait que le sprite garde la tête en haut
  
  def __init__(self, id, position, modele, symbole, planete, joueur):
    """
    Fabrique un nouvel objet
    position : là où l'objet se trouve
    modele : le nom du fichier 3D à charger
    planete : la planète de laquelle cet objet dépend
    """
    self.planete = planete
    self.joueur = joueur
    self.modele = None
    self.fichierModele = modele
    self.fichierSymbole = symbole
    self.marcheVersTab = []
    self.bouge = True
    self.aquatique = False
    self.id = id
    self.vie=100
    self.rac = NodePath("racine-sprite")
    self.racine = NodePath("racine-sprite")
    self.miseAJourPosition(position)
    
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
    if self.vie<=0:
      return False
      
    #Fait marcher
    if self.marcheVersTab != None:
      if len(self.marcheVersTab) > 0:
        self.deplace(self.marcheVersTab[0], temps)
        if general.distanceCarree(self.position, self.versCoord(self.marcheVersTab[0])) < 0.002:
          self.marcheVersTab.pop(0)

    #Fait tomber
    self.appliqueGravite(temps)

    if self.vie<=0:
      return False
      
    #Recalcule la verticale du modèle
    self.MAJSymbole()

    return True
    
  def appliqueGravite(self, temps):
    """Fait tomber les objets sur le sol"""
    altitudeCible = self.planete.altitudeCarre(self.position)
    seuil = 0.01
    
    if self.altCarre < altitudeCible or (self.altCarre > altitudeCible and not self.bouge):
      #Si on est dans le sol, on se place sur le sol d'un seul coup
      self.miseAJourPosition(general.multiplieVecteur(general.normaliseVecteur(self.position), math.sqrt(altitudeCible)))
    elif self.altCarre > altitudeCible+seuil:
      #Si on est au dessus, on tombe sur la surface
      #On calcul le vecteur -planete-sprite> et on lui donne comme longueur le déplacement que l'on veut faire
      haut = general.multiplieVecteur(general.normaliseVecteur(self.position), seuil*temps)
      #On retire ce vecteur à la position (fait un vecteur -sprite-planete>)
      self.miseAJourPosition((self.position[0]-haut[0], self.position[1]-haut[1], self.position[2]-haut[2]))
    
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
    self.rac.detachNode()
    self.rac.removeNode()
    self.rac = None
    self.racine = None
    self.modele = None
    self.symbole = None
    
  def sauvegarde(self):
    """Retoune une chaine qui représente l'objet"""
    return "S:"+str(self.position)+":"+str(self.modele)+":\r\n"
    
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
    
    if self.fichierModele == None:
      self.modele = None
      return
    if self.fichierModele.endswith(".png"):
      tmp = self.fabriqueSprite(self.fichierModele)
    else:
      tmp = loader.loadModel(self.fichierModele)
    tmp.reparentTo(self.modele)
    self.modele.node().addSwitch(3.0, 0) 
    
    symbole = self.fabriqueSymbole(self.fichierSymbole)
    symbole.reparentTo(self.modele)
    
    self.modele.node().addSwitch(9999999, 3.0) 
    
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
    taille = general.normeVecteur(base.camera.getPos(self.modele))
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
    
    
  def fabriqueSprite(self, fichierSprite, taille=1.0):
    """Construit un nouveau sprite"""
    
    racine = NodePath("sprite")
    
    #Fabrique un carré
    cardMaker = CardMaker('sprite')
    cardMaker.setFrame(-0.5, 0.5, 0.0, 1.0)
    cardMaker.setHasNormals(True)
    
    #Construit une carte (un plan)
    card1 = racine.attachNewNode(cardMaker.generate())
    #Applique la texture dessus (des 2 cotés)
    tex = loader.loadTexture(fichierSprite)
    card1.setTexture(tex)
    #Active la transprence
    card1.setTransparency(TransparencyAttrib.MDual)
    #Fait une mise à l'échelle
    card1.setScale(taille, taille, taille)
    
    #On fait tourner la carte pour quelle pointe toujours vers la caméra
    #Elle rotationne autour d'un axe uniquement (garde ses pieds vers le sol)
    card1.setBillboardAxis()
    
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

class Nuage(Sprite):
  """Génère un nuage aléatoirement"""
  
  def __init__(self, planete):
    Sprite.__init__(self, "nuage", (10000,10000,10000), "none", "none", planete, None)
    self.planete = planete
    
  def tue(self, type):
    """Un nuage ne peut pas mourrir"""
    return
    
  def ping(self, temps):
    """Non utilisé mais protège du risque d'appel à ping() de Sprite"""
    self.deplace(temps)
    return True
    
  def deplace(self, temps):
    """Promène le nuage sur l'écran"""
    #Modele est centré sur la planète, donc les rotations le promènent un peu tout autour
    f = random.random()*2.0-1.0
    self.modele.setH(self.modele.getH()+random.random()*temps*f)
    self.modele.setP(self.modele.getP()+random.random()*temps*f)
    self.modele.setR(self.modele.getR()+random.random()*temps*f)
    #Faire tourner la racine change le profile du nuage présenté à la caméra et donc sa forme pour donner l'impression qu'il évolue
    f=1
    self.racine.setH(self.racine.getH()+random.random()*temps*f)
    self.racine.setP(self.racine.getP()+random.random()*temps*f)
    self.racine.setR(self.racine.getR()+random.random()*temps*f)
    
  def fabriqueModel(self):
    """Construit le nuage"""
    
    #Choisit un nombre de prout nuageux aléatoirement
    taille = (int)(random.random()*15)+4
    #Choisit une position du nuage selon un sommet aléatoire
    centre = random.choice(self.planete.sommets)
    
    #Facteur d'étalement du nuage selon les 3 axes en espace monde
    dx, dy, dz = 1.2,1.2,1.2
    fact = general.normeVecteur((dx, dy, dz))
        
    distanceSoleil = float(general.configuration.getConfiguration("generationPlanete", "distanceSoleil","10.0"))
        
    #Place le "centre" du nuage
    self.modele = NodePath("nuage")#NodePath(FadeLODNode('nuage'))
    self.modele.setPos(*general.multiplieVecteur(general.normaliseVecteur(centre), self.planete.niveauCiel-0.01))
    self.racine = NodePath("nuage-elem")
    
    import os
    textures = os.listdir(os.path.join(".","data","textures","nuages"))
    
    #Ajoute les prouts nuageux un par un
    for i in range(0, taille):
      #Fabrique un nouveau prout
      nuage = NodePath(FadeLODNode('lod'))
      tex="./data/textures/nuages/"+random.choice(textures)
      self.fabriqueSprite(tex, taille=1).reparentTo(nuage)
      if i==0:
        nuage.node().addSwitch(99999, 0) 
      else:
        nuage.node().addSwitch(float(i)/float(taille)*distanceSoleil, 0) 
        
      nuage.setBillboardPointWorld()
      
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
      #self.modele.node().addSwitch(9999999, 0.1) 
    self.racine.reparentTo(self.modele)
    #On redimentionne le bestiau
    self.modele.setScale(0.2)
    #On optimise les envois à la carte graphique
    self.racine.flattenStrong()
    self.modele.reparentTo(self.planete.racine)
    #self.modele.setBin('fixed', -1)
    #self.modele.setDepthTest(False)
    #self.modele.setDepthWrite(False)
    #self.modele.setLightOff()
    
    return self.modele
    