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
  
  planete = None #La planète sur laquelle l'objet se trouve
  position = None #La position dans l'espace de cet objet
  modele = None #Le modèle 3D de l'objet
  fichierModele = None #Le nom du fichier du modèle 3D (utilisé pour la sauvegarde)
  fichierSymbole = None
  alt = None #L'altitude de cet objet
  symbole=None
  
  vitesse = 0.01 #(en unité/s)
  
  marcheVersTab = None #La liste des sommets vers lequel l'objet se dirige
  
  joueur = None #Le joueur qui possède cet objet
  contenu = None #Ce qui se trouve dans l'objet
  vie = None #L'état dans lequel se trouve l'objet
  
  bouge = None #Si True, alors l'objet peut bouger (personnage, véhicule, ...) sinon il est statique (arbre, bâtiment, ...)
  zoneContact = None #Les coordonnées de la zone de contact
  
  def __init__(self, id, position, modele, symbole, planete):
    """
    Fabrique un nouvel objet
    position : là où l'objet se trouve
    modele : le nom du fichier 3D à charger
    planete : la planète de laquelle cet objet dépend
    """
    self.planete = planete
    self.modele = None
    self.fichierModele = modele
    self.fichierSymbole = symbole
    self.miseAJourPosition(position)
    self.marcheVersTab = []
    self.bouge = True
    self.id = id
    
  def ping(self, temps):
    """
    Appelé à chaque image, met à jour l'état de l'objet
    temps : le nombre de secondes depuis la dernière mise à jour
    """
    altitudeCible = self.planete.altitude(self.position)
    seuil = 0.01
    if self.alt < altitudeCible or (self.alt > altitudeCible and not self.bouge):
      #Si on est dans le sol, on se place sur le sol d'un seul coup
      self.miseAJourPosition(general.multiplieVecteur(general.normaliseVecteur(self.position), math.sqrt(altitudeCible)))
    elif self.alt > altitudeCible+seuil:
      #Si on est au dessus, on tombe sur la surface
      self.miseAJourPosition((self.position[0]-seuil*temps, self.position[1]-seuil*temps, self.position[2]-seuil*temps))
      
    if self.marcheVersTab != None:
      if len(self.marcheVersTab) > 0:
        self.deplace(self.marcheVersTab[0], temps)
        if general.distanceCarree(self.position, self.versCoord(self.marcheVersTab[0])) < 0.002:
          self.marcheVersTab.pop(0)

    self.MAJSymbole()
    
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
    self.alt = general.normeVecteur(self.position)
    if self.modele != None:
      self.modele.setPos(*self.position)
      self.modele.lookAt((0,0,0))
    
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
    self.modele = NodePath(FadeLODNode('lod'))
    
    if self.fichierModele == None:
      self.modele = None
      return
    if self.fichierModele.endswith(".png"):
      tmp = self.fabriqueSprite(self.fichierModele)
      tmp.setScale(tmp.getScale()*0.1)
    else:
      tmp = loader.loadModel(self.fichierModele)
    tmp.reparentTo(self.modele)
    self.modele.node().addSwitch(3.0, 0) 
    
    symbole = self.fabriqueSymbole(self.fichierSymbole)
    symbole.reparentTo(self.modele)
    symbole.setScale(symbole.getScale()*0.1)
    self.modele.node().addSwitch(9999999, 3.0) 
    self.modele.setPos(*self.position)
    self.modele.lookAt((0,0,0))
    self.modele.reparentTo(self.planete.racine)
    self.modele.setPythonTag("type","sprite")
    self.modele.setPythonTag("id",self.id)
    self.modele.setPythonTag("instance",self)
    return self.modele
    
  def fabriqueSymbole(self, fichierSymbole):
    """Affiche une icône dont la taille ne change pas avec la distance à la caméra"""
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
    if self.symbole!=None:
      #On calcule la distance à la caméra pour avoir le facteur de corection d'échelle
      taille = general.normeVecteur(base.camera.getPos(self.modele))
      #On change l'échelle
      self.symbole.setScale(taille*0.01, taille*0.01, taille*0.01)
    
    
  def fabriqueSprite(self, fichierSprite, taille=1.0, plan=False):
    """Construit un nouveau sprite"""
    
    racine = NodePath("sprite")
    
    #Fabrique un carré
    cardMaker = CardMaker('sprite')
    cardMaker.setFrame(-0.5, 0.5, 0.0, 1.0)
    cardMaker.setHasNormals(True)
    
    #Construit 2 cartes (plans) en croix
    card1 = racine.attachNewNode(cardMaker.generate())
    if not plan:
      card2 = racine.attachNewNode(cardMaker.generate())
    #Applique la texture dessus (des 2 cotés)
    tex = loader.loadTexture(fichierSprite)
    card1.setTexture(tex)
    if not plan:
      card1.setTwoSided(True)
      card2.setTexture(tex)
      card2.setTwoSided(True)
    #Active la transprence
    card1.setTransparency(TransparencyAttrib.MDual)
    if not plan:
      card2.setTransparency(TransparencyAttrib.MDual)
    #Fait une mise à l'échelle
    card1.setScale(taille, taille, taille)
    if not plan:
      card2.setScale(taille, taille, taille)
    #Tourne les cartes
    if not plan:
      card1.setH(90)
      card1.setP(0)
      card1.setR(90)
      card2.setP(-90)
    
      #racine.setPos(0,2,0)
    racine.flattenStrong()
    
    #Les lignes suivantes font dessiner le sprite au dessus de tout le reste
    #Utile pour débugger
    #card1.setBin('fixed', -1)
    #card1.setDepthTest(False)
    #card1.setDepthWrite(False)
    #card2.setBin('fixed', -1)
    #card2.setDepthTest(False)
    #card2.setDepthWrite(False)
    #card1.setLightOff()
    #card2.setLightOff()
    #Dessine le trièdre au pied des cartes
    #racine.attachNewNode(self.dessineLigne((1.0, 0.0, 0.0, 1.0), (0.0, 0.0, 0.0), (2.0, 0.0, 0.0)))
    #racine.attachNewNode(self.dessineLigne((0.0, 1.0, 0.0, 1.0), (0.0, 0.0, 0.0), (0.0, 2.0, 0.0)))
    #racine.attachNewNode(self.dessineLigne((0.0, 0.0, 1.0, 1.0), (0.0, 0.0, 0.0), (0.0, 0.0, 2.0)))
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
    self.planete = planete
    
  def ping(self, temps):
    """Non utilisé mais protège du risque d'appel à ping() de Sprite"""
    pass
    
  def fabriqueModel(self):
    """Construit le nuage"""
    
    #Choisit un nombre de prout nuageux aléatoirement
    taille = (int)(random.random()*20)+4
    #Choisit une position du nuage selon un sommet aléatoire
    centre = random.choice(self.planete.sommets)
    
    #Facteur d'étalement du nuage selon les 3 axes en espace monde
    dx, dy, dz = 1.2,1.2,1.2
    fact = general.normeVecteur((dx, dy, dz))
        
    #Place le "centre" du nuage
    self.modele = NodePath("nuage")#NodePath(FadeLODNode('nuage'))
    self.modele.setPos(*general.multiplieVecteur(general.normaliseVecteur(centre), self.planete.niveauCiel-0.01))
    
    #Ajoute les prouts nuageux un par un
    for i in range(0, taille):
      #Fabrique un nouveau prout
      nuage = self.fabriqueSprite("./data/textures/cloud2.png", taille=1, plan=True)
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
      nuage.reparentTo(self.modele)
      #self.modele.node().addSwitch(9999999, 0.1) 
      
    #On redimentionne le bestiau
    self.modele.setScale(0.2)
    #On optimise les envois à la carte graphique
    self.modele.flattenStrong()
    self.modele.reparentTo(self.planete.racine)
    #self.modele.setBin('fixed', -1)
    #self.modele.setDepthTest(False)
    #self.modele.setDepthWrite(False)
    #self.modele.setLightOff()
    
    return self.modele
    