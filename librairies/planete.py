#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general

import random
import math
import sys
import os
import zipfile
import time

import ai
from geoide import Geoide
from sprite import Sprite

import ImageDraw
import ImageFilter
import Image

from pandac.PandaModules import *

import hashlib

class Planete:
  aiNavigation = None #Le bout d'AI qui contient le graphe de navigation qui est commun a toute entité de la planète
  spritesJoueur = None #La liste des objets du monde dérivant de la classe sprite
  spritesNonJoueur = None #La liste des objets du monde dérivant de la classe sprite
  joueurs = None
  
  #Paramètres éclairage
  soleil=None #Noeud du soleil (une caméra dans le cas de la projection d'ombre)
  flare = None #Le lens flare
  distanceSoleil = None #Distance du soleil à la planète
  vitesseSoleil = None #Vitesse de rotation du soleil en pifometre/s
  angleSoleil = None
  lastSave = 1000
  seuilSauvegardeAuto = 600 #Sauvegarde auto toutes les 10 minutes
  
  geoide = None
  fini = False
  
  nom = None #Le nom de la planète (et/ou du niveau)
  
  # Initialisation -----------------------------------------------------
  def __init__(self, nom="sans nom"):
    """Constructeur, initialise les tableaux"""
    self.geoide = Geoide()
    self.nom = nom
    self.spritesJoueur = [] #Pas d'objets sur la planète
    self.spritesNonJoueur = [] #Pas d'objets sur la planète
    self.joueurs = []
    
    self.distanceSoleil = general.configuration.getConfiguration("planete", "Univers", "distanceSoleil", "10.0", float)
    self.vitesseSoleil = general.configuration.getConfiguration("planete", "Univers", "vitesseSoleil", "1.0", float)
    self.angleSoleil = 0.0
    self.seuilSauvegardeAuto = general.configuration.getConfiguration("affichage", "General", "seuilSauvegardeAuto", "600.0", float)
    
    self.fini = False
    #On calcule la navigation pour l'intelligence artificielle
    self.aiNavigation = ai.AINavigation()
    taskMgr.add(self.pingPlanete, "BouclePrincipale-planete")
    
  def detruit(self):
    """Détruit la planète et tout ce qui lui est associé"""
    self.geoide.detruit()
    self.geoide=None
    
    self.aiNavigation.detruit()
    self.aiNavigation = None
    
    self.fini = True
    for joueur in self.joueurs:
      joueur.detruit()
    for sprite in self.spritesJoueur:
      sprite.tue("destruction de la planète", silence=True)
    for sprite in self.spritesNonJoueur:
      sprite.tue("destruction de la planète", silence=True)
    self.spritesJoueur = []
    self.spritesNonJoueur = []
    self.joueurs = []
    
  def _syncCheck(self):
    check = ""
    check+=self.geoide._syncCheck()
    for joueur in self.joueurs:
      check+=joueur._syncCheck()
    for sprite in self.spritesJoueur:
      check+=sprite._syncCheck()
    for sprite in self.spritesNonJoueur:
      check+=sprite._syncCheck()
    return check
    
  def hash(self):
    return hashlib.sha256(self._syncCheck()).hexdigest()
  # Fin Initialisation -------------------------------------------------
    
  @general.accepts(None, (str, unicode), dict, (str, unicode, "opt"))
  def afficheTexte(self, texte, parametres, type=None):
    """Affiche le texte sur l'écran"""
    general.interface.afficheTexte(texte, parametres, type, True)
    
  # Constructions géométriques -----------------------------------------
  def fabriqueNouvellePlanete(self, tesselation, delta):
    """
    Construit une nouvelle planète :
    tesselation : Le nombre de subdivision que l'on souhaite faire
    delta : Le niveau maximal de perturbation de la surface que l'on souhaite
    """
    if self.geoide == None:
      self.geoide=Geoide()
      
    self.geoide.fabriqueNouveauGeoide(tesselation, delta)
    self.spritesJoueur = [] #Pas d'objets sur la planète
    self.spritesNonJoueur = [] #Pas d'objets sur la planète
    self.joueurs = [] 
    self.angleSoleil = 0.0
    
  def fabriqueModel(self):
    """Produit un modèle 3D à partir du nuage des faces"""
    self.geoide.fabriqueModel()
    render.analyze()

  # Fin Constructions géométriques -------------------------------------
      
  # Import / Export ----------------------------------------------------
  def sauvegarde(self, fichier, tess=None):
    """Sauvegarde la planète dans un fichier"""
    self.afficheTexte("Sauvegarde en cours...", parametres={}, type="sauvegarde")
    
    nomFichier = fichier
      
    #On sauvegarde dans un fichier temporaire
    fichier = open(os.path.join(".", "data", "cache", "save.tmp"), "w")
    fichier.write("details:dateSauvegarde:"+time.strftime("%Y/%m/%d %H-%M")+":\r\n")
    fichier.write("details:nomPlanete:"+self.nom+":\r\n")
    fichier.write("details:fichierCapture:None:\r\n")
    fichier.write("parametres:distanceSoleil:"+str(self.distanceSoleil)+":\r\n")
    fichier.write("parametres:angleSoleil:"+str(self.angleSoleil)+":\r\n")
    for joueur in self.joueurs:
      fichier.write(joueur.sauvegarde()) #j
    for sprite in self.spritesJoueur:
      fichier.write(sprite.sauvegarde()) #s
    for sprite in self.spritesNonJoueur:
      fichier.write(sprite.sauvegarde()) #s
    fichier.write(self.geoide.sauvegarde(None, tess))
    fichier.close()
    
    #On zip le fichier temporaire
    zip = zipfile.ZipFile(nomFichier, "w")
    zip.write(os.path.join(".", "data", "cache", "save.tmp"), "sauvegarde", zipfile.ZIP_DEFLATED)
    zip.write(os.path.join(".", "data", "cache", "minimap.png"), "minimap.png", zipfile.ZIP_DEFLATED)
    zip.close()
    #On enlève le fichier temporaire
    os.remove(os.path.join(".", "data", "cache", "save.tmp"))
    self.afficheTexte("Sauvegarde terminée", parametres={}, type="sauvegarde")
    
  def charge(self, fichier, simple=False):
    """Charge le géoïde depuis un fichier"""
    self.afficheTexte("Chargement en cours...", parametres={}, type="sauvegarde")
    
    self.detruit()
    self.spritesJoueur = []
    self.spritesNonJoueur = []
    self.joueurs = []

    if general.configuration.getConfiguration("debug", "planete", "debug_charge_planete", "f", bool):
      self.afficheTexte("Lecture du fichier...", parametres={}, type="sauvegarde")

    #Lecture depuis le zip
    zip = zipfile.ZipFile(fichier, "r")
    if zip.testzip()!=None:
      print "PLANETE :: Charge :: Erreur : Fichier de sauvegarde corrompu !"
    data = zip.read("sauvegarde")
    zip.close()
    lignes = data.split("\r\n")

    if general.configuration.getConfiguration("debug", "planete", "debug_charge_planete", "f", bool):
      self.afficheTexte("Parsage des infos...", parametres={}, type="sauvegarde")
      
    lignes = self.geoide.charge(lignes, simple)
    tot = len(lignes)
      
    for i in range(0, tot):
      if general.configuration.getConfiguration("debug", "planete", "debug_charge_planete", "f", bool):
        if i%500==0:
          self.afficheTexte("Parsage des infos... %{a}i/%{b}i", parametres={"a":i, "b":tot}, type="sauvegarde")
      ligne = lignes[i]
        
      elements = ligne.strip().lower().split(":")
      type = elements[0]
      elements = elements[1:]
      if type=="parametres":
        if elements[0]=="distancesoleil":
          #Attrapage des infos de distanceSoleil
          self.distanceSoleil = float(elements[1])
        elif elements[0]=="anglesoleil":
          #Attrapage des infos de angleSoleil
          self.angleSoleil = float(elements[1])
        else:
          print "Donnée inconnue : ",element[0]
      if type=="details":
        if elements[0]=="nomplanete":
          #Attrapage des infos de distanceSoleil
          self.nom = elements[1]
        else:
          print "Détail inconnu : ",element[0]
      elif type=="joueur":
        #Création d'un joueur
        type, nom, couleur, estJoueur, vide = elements
        couleur = VBase4(general.floatise(couleur.replace("(","").replace(")","").replace("[","").replace("]","").split(",")))
        classe = Joueur
        if type=="ia":
          classe = JoueurIA
        elif type=="local":
          classe = JoueurLocal
        elif type=="distant":
          classe = JoueurDistant
        else:
          print "PLANETE :: Charge :: Erreur, type de joueur inconnu :", type
        self.ajouteJoueur(classe(nom, couleur, estJoueur.lower().strip()=="true"))
      elif type=="joueur-ressource":
        #Création des ressources d'un joueur
        nomjoueur, nomressource, valeur, vide = elements
        for joueur in self.joueurs:
          if joueur.nom.lower().strip()==nomjoueur.lower().strip():
            joueur.ressources[nomressource] = int(valeur)
      elif type=="sprite":
        #Sprites
        id, nomjoueur, modele, symbole, position, vitesse, vie, bouge, aquatique, dureeDeVie, tempsDeVie, fichierDefinition, vide = elements
        position = Vec3(*general.floatise(position.replace("[","").replace("]","").replace("(","").replace(")","").split(",")))
        if nomjoueur.lower().strip()=="none":
          joueur = None
        else:
          for joueurT in self.joueurs:
            if joueurT.nom.lower().strip()==nomjoueur.lower().strip():
              joueur = joueurT
        if fichierDefinition.lower().strip()=="none":
          fichierDefinition = None
        sprite = Sprite(id, position, fichierDefinition, joueur)
        sprite.modele = modele
        sprite.symbole = symbole
        sprite.vie = float(vie)
        sprite.bouge = bouge.lower().strip()=="t"
        sprite.aquatique = aquatique.lower().strip()=="t"
        sprite.dureeDeVie = float(dureeDeVie)
        sprite.tempsDeVie = float(tempsDeVie)
        sprite.vitesse = float(vitesse)
        if joueur!=None:
          self.spritesJoueur.append(sprite)
          joueur.sprites.append(sprite)
        else:
          self.spritesNonJoueur.append(sprite)
      elif type=="sprite-contenu":
        id, type, valeur = elements
        valeur = float(valeur)
        for sprite in self.spritesJoueur:
          if sprite.id.lower().strip() == id.lower().strip():
            sprite.contenu[type]=valeur
        for sprite in self.spritesNonJoueur:
          if sprite.id.lower().strip() == id.lower().strip():
            sprite.contenu[type]=valeur
      elif ligne.strip()!="":
        print
        print "Avertissement : Planete::charge, type de ligne inconnue :", type,"sur la ligne :\r\n",ligne.strip()
        general.TODO("Ajouter la prise en charge du chargement de "+type)
        
    self.afficheTexte("Chargement terminé", parametres={}, type="sauvegarde")
  # Fin Import / Export ------------------------------------------------
      
  # Mise à jour --------------------------------------------------------
  def fabriqueSoleil(self, type=None):
    if type==None:
      type = general.configuration.getConfiguration("affichage", "effets", "typeEclairage", "shader", str)
    type=type.lower().strip()
      
    couleurSoleil = general.configuration.getConfiguration("Planete", "Univers", "couleurSoleil", "0.9 0.9 0.9 0.8", str)
    couleurSoleil = VBase4(*general.floatise(couleurSoleil.split(" ")))
      
    if type=="flat":
      light = PointLight('soleil')
      light.setColor(couleurSoleil)
      self.soleil = self.geoide.racine.attachNewNode(light)
      self.soleil.setPos(0,0,0)
      self.soleil.setLightOff()
      self.geoide.racine.setLight(self.soleil)
      
      cardMaker = CardMaker('soleil')
      cardMaker.setFrame(-0.5, 0.5, -0.5, 0.5)
      bl = self.geoide.racine.attachNewNode(cardMaker.generate())
      #Applique la tecture dessus
      tex = loader.loadTexture("data/textures/soleil.png")
      bl.setTexture(tex)
      #Active la transprence
      bl.setTransparency(TransparencyAttrib.MDual)
      #Fait une mise à l'échelle
      bl.setScale(0.8)
      #On fait en sorte que la carte soit toujours tournée vers la caméra, le haut vers le haut
      bl.setBillboardPointEye()

      #bl = loader.loadModel("./data/modeles/sphere.egg")
      bl.reparentTo(self.soleil)
      
      self.soleil.reparentTo(self.geoide.racine)
    elif type=="none":
      self.soleil = loader.loadModel("./data/modeles/sphere.egg")
      self.soleil.reparentTo(self.geoide.racine)
    else:
      print "Type d'éclairage inconnu",type
      
  def ajouteJoueur(self, joueur):
    self.joueurs.append(joueur)
    
  def ajouteSprite(self, id, position, type):
    """
    Ajoute un nouveau sprite
    id : l'identifiant du sprite
    position : sa position sur le terrain
    type : le type de sprite à créer
    """
    fichier = os.path.join(".","data","sprites",type+".spr")
    if not os.path.exists(fichier):
      print "Sprite inconnu",type, "->", fichier
    id = "{S:neutre}"+id+"-"+str(len(self.spritesNonJoueur)+1)
    sprite = Sprite(id=id, position=position, fichierDefinition=fichier, joueur=None)
    self.spritesNonJoueur.append(sprite)
    return sprite

  lastPing=None
  compteurMAJSpriteNonJoueur=0.0
  seuilMAJSpriteNonJoueur=3.0
  
  @general.chrono
  def pingPlanete(self, task):
    """Fonction appelée a chaque image, temps indique le temps écoulé depuis l'image précédente"""
    
    if self.lastPing==None:
      self.lastPing = task.time-1.0/60
    temps = task.time-self.lastPing
    self.lastPing = task.time
    
    #Sauvegarde automatique
    self.lastSave += temps
    if self.seuilSauvegardeAuto != -1 and self.lastSave > self.seuilSauvegardeAuto:
      self.afficheTexte("Sauvegarde automatique en cours...", parametres={}, type="sauvegarde")
      self.sauvegarde(os.path.join(".","sauvegardes","sauvegarde-auto.pln"))
      self.lastSave = 0

    #On fabrique le soleil si on en a pas
    if self.soleil == None:
      self.fabriqueSoleil()

    #Fait tourner le soleil
    self.angleSoleil += temps / math.pi * self.vitesseSoleil
    if self.soleil != None and self.soleil != 1:
      self.soleil.setPos(0.0, math.sin(self.angleSoleil)*self.distanceSoleil, math.cos(self.angleSoleil)*self.distanceSoleil)
      self.soleil.lookAt(0,0,0)
      
      if self.flare != None:
        self.flare.detachNode()
        self.flare.removeNode()
        self.flare=None
      #Calcule le lens flare
      if general.ligneCroiseSphere(general.io.camera.getPos(), self.soleil.getPos(), (0.0,0.0,0.0), 1.0) == None:
        ptLum = general.map3dToRender2d(render, self.soleil.getPos())
        if ptLum!=None:
          pass
          """self.flare = NodePath("flare")
          for i in range(0, 3):
            p=ptLum[0]*i/3.0, ptLum[1]*i/3.0, ptLum[2]*i/3.0
            #Fabrique un carré
            cardMaker = CardMaker('flare')
            cardMaker.setFrame(0.1, 0.1, 0.1, 0.1)
            cardMaker.setHasNormals(True)
            flare = self.flare.attachNewNode(cardMaker.generate())
            flare.setTexture("./data/textures/flare/lens-flare1.png")
            flare.setPos(*p)
          self.flare.reparentTo(render2d)"""      
          
    _lightvec = Vec4(1.0, 0.0, 1.0, 1.0)
    if self.soleil != None and self.geoide!=None:
      _lightvec = Vec3(self.soleil.getPos() - self.geoide.racine.getPos())
      _lightvec = Vec4(_lightvec[0], _lightvec[1], _lightvec[2], 0.0)
      
    render.setShaderInput( 'lightvec', _lightvec )
      
    #Met à jour l'état des joueurs
    for joueur in self.joueurs:
      joueur.pingJoueur(temps)
      
    #Met à jour les états des sprites
    for sprite in self.spritesJoueur[:]:
      if general.configuration.getConfiguration("Planete","regles","obscuriteTue","t", bool):
        if general.ligneCroiseSphere(sprite.position, self.soleil.getPos(), (0.0,0.0,0.0), 1.0) != None:
          if not sprite.nocturne:
            sprite.tue("obscurite")
      if not sprite.pingSprite(temps):
        if sprite.joueur !=None:
          sprite.joueur.spriteMort(sprite)
        while sprite in self.spritesJoueur:
          self.spritesJoueur.remove(sprite)
          
    #Les sprites non joueurs ne sont remis à jour que de temps en temps
    self.compteurMAJSpriteNonJoueur+=temps
    if self.compteurMAJSpriteNonJoueur>self.seuilMAJSpriteNonJoueur:
      for sprite in self.spritesNonJoueur[:]:
        if not sprite.pingSprite(self.compteurMAJSpriteNonJoueur):
          if sprite.joueur !=None:
            sprite.joueur.spriteMort(sprite)
          while sprite in self.spritesNonJoueur:
            self.spritesNonJoueur.remove(sprite)
      self.compteurMAJSpriteNonJoueur = 0.0
    
    if not self.fini:
      return task.cont
    else:
      return task.done
  # Fin Mise à jour ----------------------------------------------------
  
