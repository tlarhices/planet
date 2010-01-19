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
    rayonorbite = float(len(self.planetes)*len(self.planetes)+10.0)*5+20.0
    rayonplanete = random.random()*3.0+15.0
    angleDepart = 360.0*random.random()
    vitesse = 8.0*random.random()+2.0
    self.planetes.append((planete, rayonplanete, rayonorbite, angleDepart, None, vitesse))
    
  def detruit(self):
    """Détruit la planète et tout ce qui lui est associé"""
    self.fini = True
    self.racine.detachNode()
    self.racine.removeNode()
    
  def dessineCercle(self, rayon, nbFaces):
    couleur = (1.0, 1.0, 1.0, 1.0)
    ls = LineSegs()
    ls.setColor(*couleur)
    ls.setThickness(1.0)
    deltaAngle = 2*math.pi/nbFaces
    for i in range(0, nbFaces):
      ls.moveTo(rayon*math.cos(deltaAngle*i), 0.0, rayon*math.sin(deltaAngle*i))
      ls.drawTo(rayon*math.cos(deltaAngle*(i+1)), 0.0, rayon*math.sin(deltaAngle*(i+1)))
    return ls.create()
    
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
      self.soleil.setScale(100.0)
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
      self.etoiles.setBin('background', 1)
      self.etoiles.setDepthTest(False)
      self.etoiles.setDepthWrite(False)
      self.etoiles.setPythonTag("type","ciel")
      #On coupe la collision avec les étoiles pour pas qu'on détecte de clics sur le fond
      self.etoiles.setCollideMask(BitMask32.allOff())
      
      #Lumière dans le noir
      couleurNuit = general.configuration.getConfiguration("Planete", "Univers", "couleurNuit", "0.2 0.2 0.275 1.0", str)
      couleurNuit = VBase4(*general.floatise(couleurNuit.split(" ")))
      alight = AmbientLight('alight')
      alight.setColor(couleurNuit)
      alnp = self.racine.attachNewNode(alight)
      self.racine.setLight(alnp)
      
      #Lumière du soleil
      couleurSoleil = general.configuration.getConfiguration("Planete", "Univers", "couleurSoleil", "0.9 0.9 0.9 0.8", str)
      couleurSoleil = VBase4(*general.floatise(couleurSoleil.split(" ")))
      light = PointLight('soleil')
      light.setColor(couleurSoleil)
      lampe = self.racine.attachNewNode(light)
      lampe.setPos(0,0,0)
      self.racine.setLight(lampe)

      #Le fond et le soleil ne sont pas affectés par la lumière
      self.soleil.setLightOff()
      self.etoiles.setLightOff()

    for i in range(0, len(self.planetes)):
      planete, rayonplanete, rayonorbite, angleDepart, planetemdl, vitesse = self.planetes[i]
      if planetemdl == None:
        planetemdl = loader.loadModel("./data/modeles/sphere.egg")
        planetemdl.reparentTo(self.racine)
        planetemdl.setScale(rayonplanete)
        planetemdl.setColor(random.random()*0.5, random.random()*0.5, random.random()*0.5)
        planetemdl.setPythonTag("type", "planete") #Pour dire que c'est une planète
        planetemdl.setPythonTag("nomPlanete", planete) #Pour indiquer de quelle planète il sagit et le retrouver facilement 
        #planetemdl.setTexture(loader.loadTexture("./data/cache/minimap.png"))
        planetemdl.setHpr(random.random()*360, random.random()*360, random.random()*360)
        self.planetes[i] = (planete, rayonplanete, rayonorbite, angleDepart, planetemdl, vitesse)
        anneau = self.racine.attachNewNode(self.dessineCercle(rayonorbite, 40))
        anneau.setBin('background', 2)
        anneau.setDepthTest(False)
        anneau.setDepthWrite(False)
        
  def ping(self, task):
    lastorb = 10.0
    for planete, rayonplanete, rayonorbite, angleDepart, planetemdl, vitesse in self.planetes:
      px = rayonorbite * math.cos((angleDepart + task.time*vitesse)/180.0*math.pi)
      py = rayonorbite * math.sin((angleDepart + task.time*vitesse)/180.0*math.pi)
      planetemdl.setPos(px, 0.0, py)
      planetemdl.setR(task.time*vitesse*5)
      lastorb = rayonorbite
    
    general.io.camera.setPos(0.0, rayonorbite*4, 0.0)
    self.etoiles.setScale(rayonorbite*11)
    general.io.camera.lookAt(self.soleil)
    while not self.fini:
      return task.cont
    return task.done
