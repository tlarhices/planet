#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import random
import general

class Attracteur:
  position = None
  direction = None
  
  def __init__(self, force):
    self.position = random.choice(general.planete.geoide.voisinage.keys())
    self.force = force
    self.direction = [random.random(),random.random()]
    
  def pingAttracteur(self, temps):
    voisin=general.planete.geoide.voisinage[self.position]
    
    self.direction[0] = self.direction[0]+(random.random()*2-1.0)/5*temps
    self.direction[1] = self.direction[1]+(random.random()*2-1.0)/100*temps
    
    if abs(self.direction[1]>1.5):
      self.direction[1]=self.direction[1]/abs(self.direction[1])/10
      
    id = int(self.direction[0]*len(voisin))%len(voisin)
    
    if self.direction[1]>0.5:
      self.position=voisin[id]
      
    return self.force

class Tectonique:
  modifications = None
  attracteurs = None
  
  def __init__(self):
    self.modifications = []
    for i in range(0, len(general.planete.geoide.sommets)):
      self.modifications.append(0.0)
    self.attracteurs = []
    for i in range(0, general.configuration.getConfiguration("planete", "construction", "attracteurs", "10", int)):
      force=random.random()
      self.attracteurs.append(Attracteur(force))
      self.attracteurs.append(Attracteur(-force))
      
  def pingTectonique(self, temps):
    for attracteur in self.attracteurs:
      decal = attracteur.pingAttracteur(temps)
      self.modifications[attracteur.position]+=decal
      if abs(self.modifications[attracteur.position])>1.0:
        altitude = general.planete.geoide.delta/10*self.modifications[attracteur.position]
        general.planete.geoide.elevePoint(attracteur.position, altitude)
        self.modifications[attracteur.position] = 0.0
