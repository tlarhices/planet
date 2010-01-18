#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general
import random
import math
from pandac.PandaModules import *

class SystemeSolaire:
  
  planetes = None
  racine = None
  soleil = None
  fini = None
  nom = None
  
  # Initialisation -----------------------------------------------------
  def __init__(self, nom="sans nom"):
    """Constructeur"""
    self.planetes = []
    self.racine = NodePath("syssol")
    self.racine.reparentTo(render)
    self.fini = False
    self.nom = nom
    taskMgr.add(self.ping, "BouclePrincipale-syssol")
    
  def ajoutePlanete(self, planete):
    """"""
    rayonorbite = float(len(self.planetes)*len(self.planetes)+6.0)*5
    rayonplanete = random.random()*2.0+0.5
    angleDepart = 360.0*random.random()
    vitesse = 8.0*random.random()+2.0
    self.planetes.append((planete, rayonplanete, rayonorbite, angleDepart, None, vitesse))
    
  def detruit(self):
    """Détruit la planète et tout ce qui lui est associé"""
    self.fini = True
    self.racine.detachNode()
    self.racine.removeNode()
    
  def fabriqueModel(self):
    """Produit un modèle 3D à partir du nuage des faces"""
    if self.soleil == None:
      cardMaker = CardMaker('soleil')
      cardMaker.setFrame(-0.5, 0.5, -0.5, 0.5)
      self.soleil = self.racine.attachNewNode(cardMaker.generate())
      #Applique la tecture dessus
      tex = loader.loadTexture("data/textures/soleil.png")
      self.soleil.setTexture(tex)
      #Active la transprence
      self.soleil.setTransparency(TransparencyAttrib.MDual)
      #Fait une mise à l'échelle
      self.soleil.setScale(8.0)
      #On fait en sorte que la carte soit toujours tournée vers la caméra, le haut vers le haut
      self.soleil.setBillboardPointEye()
      
      #Étoiles
      self.etoiles = loader.loadModel("data/modeles/sphere.egg")
      self.etoiles.setTransparency(TransparencyAttrib.MDual )
      tex = loader.loadTexture('data/textures/etoiles4.tif')
      #tex.setMagfilter(Texture.FTLinear)
      #tex.setMinfilter(Texture.FTLinearMipmapLinear)
      #etoiles.setTexGen(TextureStage.getDefault(), TexGenAttrib.MEyeSphereMap)
      self.etoiles.setTexture(tex, 1)
      self.etoiles.setTwoSided(False)
      self.etoiles.setScale(general.configuration.getConfiguration("planete", "Univers", "distanceSoleil","10.0",float)*3.0/2.0)
      self.etoiles.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
      self.etoiles.reparentTo(self.racine)    
      self.etoiles.setLightOff()
      self.etoiles.setBin('background', 1)
      self.etoiles.setDepthTest(False)
      self.etoiles.setDepthWrite(False)

    for i in range(0, len(self.planetes)):
      planete, rayonplanete, rayonorbite, angleDepart, planetemdl, vitesse = self.planetes[i]
      if planetemdl == None:
        planetemdl = loader.loadModel("./data/modeles/sphere.egg")
        planetemdl.reparentTo(self.racine)
        planetemdl.setScale(rayonplanete)
        self.planetes[i] = (planete, rayonplanete, rayonorbite, angleDepart, planetemdl, vitesse)
        
  def ping(self, task):
    lastorb = 10.0
    for planete, rayonplanete, rayonorbite, angleDepart, planetemdl, vitesse in self.planetes:
      px = rayonorbite * math.cos((angleDepart + task.time*vitesse)/180.0*math.pi)
      py = rayonorbite * math.sin((angleDepart + task.time*vitesse)/180.0*math.pi)
      planetemdl.setPos(px, 0.0, py)
      lastorb = rayonorbite
    
    general.io.camera.setPos(0.0, rayonorbite*10, 0.0)
    self.etoiles.setScale(rayonorbite*11)
    general.io.camera.lookAt(self.soleil)
    while not self.fini:
      return task.cont
    return task.done