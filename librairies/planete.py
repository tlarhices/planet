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

from ai import AINavigation
from geoide import Geoide
from sprite import Sprite, Nuage
from joueur import *

import ImageDraw
import ImageFilter
import Image

#from pandac.PandaModules import *

class Planete:
  aiNavigation = None #Le bout d'AI qui contient le graphe de navigation qui est commun a toute entité de la planète
  sprites = None #La liste des objets du monde dérivant de la classe sprite
  joueurs = None
  
  #Paramètres éclairage
  soleil=None #Noeud du soleil (une caméra dans le cas de la projection d'ombre)
  flare = None #Le lens flare
  distanceSoleil = None #Distance du soleil à la planète
  vitesseSoleil = None #Vitesse de rotation du soleil en pifometre/s
  angleSoleil = None
  lastMAJPosSoleil=100000.0 #Le temps depuis lequel on n'a pas remis à jour la carte du soleil
  dureeMAJPosSoleil=23.0 #Le temps que l'on attends avant de recalculer la carte du soleil
  lastSave = 1000
  seuilSauvegardeAuto = 600 #Sauvegarde auto toutes les 10 minutes
  
  geoide = None
  fini = False
  
  # Initialisation -----------------------------------------------------
  def __init__(self):
    """Constructeur, initialise les tableaux"""
    self.geoide = Geoide()
    
    self.sprites = [] #Pas d'objets sur la planète
    self.joueurs = []
    
    self.distanceSoleil = float(general.configuration.getConfiguration("planete", "Univers", "distanceSoleil","10.0"))
    self.vitesseSoleil = float(general.configuration.getConfiguration("planete", "Univers", "vitesseSoleil","1.0"))
    self.angleSoleil = 0.0
    self.dureeMAJPosSoleil = float(general.configuration.getConfiguration("affichage", "Minimap", "dureeMAJPosSoleil","23.0"))
    self.seuilSauvegardeAuto = float(general.configuration.getConfiguration("affichage", "General", "seuilSauvegardeAuto","600.0"))
    
    self.fini = False
    #On calcule la navigation pour l'intelligence artificielle
    self.aiNavigation = AINavigation()
    taskMgr.add(self.ping, "BouclePrincipale-planete")
    
  def detruit(self):
    """Détruit la planète et tout ce qui lui est associé"""
    self.geoide.detruit()
    self.geoide=None
    
    self.aiNavigation.detruit()
    self.aiNavigation = None
    
    self.fini = True
    for joueur in self.joueurs:
      joueur.detruit()
    for sprite in self.sprites:
      sprite.tue("destruction de la planète")
    self.sprites = []
    self.joueurs = []
  # Fin Initialisation -------------------------------------------------
    
  def afficheTexte(self, texte, type=None):
    """Affiche le texte sur l'écran, si texte==None, alors efface le dernier texte affiché"""
    general.interface.afficheTexte(texte, type, True)
    
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
    self.sprites = [] #Pas d'objets sur la planète
    self.joueurs = [] 
    self.angleSoleil = 0.0
    
  def fabriqueModel(self):
    """Produit un modèle 3D à partir du nuage des faces"""
    self.geoide.fabriqueModel()

  # Fin Constructions géométriques -------------------------------------
      
  # Import / Export ----------------------------------------------------
  def sauvegarde(self, fichier, tess=None):
    """Sauvegarde la planète dans un fichier"""
    self.afficheTexte("Sauvegarde en cours...", "sauvegarde")
    
    nomFichier = fichier
      
    #On sauvegarde dans un fichier temporaire
    fichier = open(os.path.join(".", "data", "cache", "save.tmp"), "w")
    fichier.write("O:distanceSoleil:"+str(self.distanceSoleil)+":\r\n")
    fichier.write("O:angleSoleil:"+str(self.angleSoleil)+":\r\n")
    for joueur in self.joueurs:
      fichier.write(joueur.sauvegarde()) #j
    for sprite in self.sprites:
      fichier.write(sprite.sauvegarde()) #s
    fichier.write(self.geoide.sauvegarde(None, tess))
    fichier.close()
    
    #On zip le fichier temporaire
    zip = zipfile.ZipFile(nomFichier, "w")
    zip.write(os.path.join(".", "data", "cache", "save.tmp"), os.path.basename(nomFichier), zipfile.ZIP_DEFLATED)
    zip.close()
    #On enlève le fichier temporaire
    os.remove(os.path.join(".", "data", "cache", "save.tmp"))
    self.afficheTexte("Sauvegarde terminée", "sauvegarde")
    
  def charge(self, fichier, simple=False):
    """Charge le géoïde depuis un fichier"""
    self.afficheTexte("Chargement en cours...", "sauvegarde")
    
    self.detruit()
    self.sprites = []
    self.joueurs = []

    if general.DEBUG_CHARGE_PLANETE:
      self.afficheTexte("Lecture du fichier...")

    #Lecture depuis le zip
    zip = zipfile.ZipFile(fichier, "r")
    if zip.testzip()!=None:
      print "PLANETE :: Charge :: Erreur : Fichier de sauvegarde corrompu !"
    data = zip.read(os.path.basename(fichier))
    zip.close()
    lignes = data.split("\r\n")

    if general.DEBUG_CHARGE_PLANETE:
      self.afficheTexte("Parsage des infos...")
      
    lignes = self.geoide.charge(lignes, simple)
    tot = len(lignes)
      
    for i in range(0, tot):
      if general.DEBUG_CHARGE_PLANETE:
        if i%500==0:
          self.afficheTexte("Parsage des infos... %i/%i" %(i, tot))
      ligne = lignes[i]
        
      elements = ligne.strip().lower().split(":")
      type = elements[0]
      elements = elements[1:]
      if type=="o":
        if elements[0]=="distancesoleil":
          #Attrapage des infos de distanceSoleil
          self.distanceSoleil = float(elements[1])
        elif elements[0]=="anglesoleil":
          #Attrapage des infos de angleSoleil
          self.angleSoleil = float(elements[1])
        else:
          print "Donnée inconnue : ",element[0]
      elif type=="j":
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
      elif type=="jr":
        #Création des ressources d'un joueur
        nomjoueur, nomressource, valeur, vide = elements
        for joueur in self.joueurs:
          if joueur.nom.lower().strip()==nomjoueur.lower().strip():
            joueur.ressources[nomressource] = int(valeur)
      elif type=="s":
        #Sprites
        id, nomjoueur, modele, symbole, position, vitesse, vie, bouge, aquatique, vide = elements
        position = Vec3(*general.floatise(position.replace("[","").replace("]","").replace("(","").replace(")","").split(",")))
        if nomjoueur.lower().strip()=="none":
          joueur = None
        else:
          for joueurT in self.joueurs:
            if joueurT.nom.lower().strip()==nomjoueur.lower().strip():
              joueur = joueurT
        sprite = Sprite(id, position, modele, symbole, float(vie), self, joueur)
        sprite.vitesse = float(vitesse)
        sprite.bouge = bouge.lower().strip()=="true"
        sprite.aquatique = aquatique.lower().strip()=="true"
        self.sprites.append(sprite)
        joueur.sprites.append(sprite)
      elif type=="sm":
        #Mouvement des sprites
        id, elem, vide = elements
        for sprite in self.sprites:
          if sprite.id.lower().strip() == id.lower().strip():
            sprite.marcheVersTab.append(int(elem))
      elif ligne.strip()!="":
        print
        print "Avertissement : Planete::charge, type de ligne inconnue :", type,"sur la ligne :\r\n",ligne.strip()
        
    self.afficheTexte("Chargement terminé", "sauvegarde")
  # Fin Import / Export ------------------------------------------------
      
  # Mise à jour --------------------------------------------------------
  def fabriqueSoleil(self, type=None):
    if type==None:
      type = general.configuration.getConfiguration("affichage", "effets", "typeEclairage", "shader")
    type=type.lower().strip()
      
    couleurSoleil = general.configuration.getConfiguration("Planete", "Univers", "couleurSoleil", "0.9 0.9 0.9 0.8")
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
    id = "[neutre]"+id+"-"+str(len(self.sprites)+1)
    sprite = Sprite(id=id, position=position, fichierDefinition=fichier, joueur=None)
    self.sprites.append(sprite)
    return sprite

  lastPing=None
  def ping(self, task):
    """Fonction appelée a chaque image, temps indique le temps écoulé depuis l'image précédente"""
    if self.lastPing==None:
      self.lastPing = task.time-1.0/60
    temps = task.time-self.lastPing
    self.lastPing = task.time
    
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
      joueur.ping(temps)
      
    #Met à jour les états des sprites
    for sprite in self.sprites[:]:
#      if general.ligneCroiseSphere(sprite.position, self.soleil.getPos(), (0.0,0.0,0.0), 1.0) != None:
#        if not sprite.nocturne:
#          sprite.tue("obscurite")
      if not sprite.ping(temps):
        if sprite.joueur !=None:
          sprite.joueur.spriteMort(sprite)
        while sprite in self.sprites:
          self.sprites.remove(sprite)
        
    #Sauvegarde automatique
    self.lastSave += temps
    if self.seuilSauvegardeAuto != -1 and self.lastSave > self.seuilSauvegardeAuto:
      self.afficheTexte("Sauvegarde automatique en cours...", "sauvegarde")
      self.sauvegarde(os.path.join(".","sauvegardes","sauvegarde-auto.pln"))
      self.lastSave = 0
      
      
    if general.configuration.getConfiguration("affichage","minimap","affichesoleil","t")=="t":
      #Met à jour la carte du soleil
      self.lastMAJPosSoleil += temps
      if self.lastMAJPosSoleil > self.dureeMAJPosSoleil:
        self.lastMAJPosSoleil=0.0
        def procFace(face):
          jour = (1.0,1.0,1.0)
          nuit = (0.2,0.2,0.4)
          p1 = Vec3(self.sommets[face.sommets[0]])
          p1.normalize()
          p1 = p1 * 1.0001
          if general.ligneCroiseSphere(p1, self.soleil.getPos(), Vec3(0.0,0.0,0.0), 1.0) != None:
            c1=nuit
          else:
            c1=jour
          p2 = Vec3(self.sommets[face.sommets[1]])
          p2.normalize()
          p2 = p2 * 1.0001
          if general.ligneCroiseSphere(p2, self.soleil.getPos(), Vec3(0.0,0.0,0.0), 1.0) != None:
            c2=nuit
          else:
            c2=jour
          p3 = Vec3(self.sommets[face.sommets[2]])
          p3.normalize()
          p3 = p3 * 1.0001
          if general.ligneCroiseSphere(p3, self.soleil.getPos(), Vec3(0.0,0.0,0.0), 1.0) != None:
            c3=nuit
          else:
            c3=jour
          
          if face.enfants == None:# or (c1==c2 and c2==c3):
            if general.interface.menuCourant.miniMap != None:
              general.interface.menuCourant.miniMap.dessineCarte(p1, p2, p3, c1, c2, c3, True)
          return True#not (c1==c2 and c2==c3) #Return False si tout est de la meme couleur
          
        def recur(face):
          if procFace(face):
            if face.enfants != None:
              for enfant in face.enfants:
                recur(enfant)
        for face in self.elements:
          recur(face)
    
    if not self.fini:
      return task.cont
    else:
      return task.done
  # Fin Mise à jour ----------------------------------------------------
  