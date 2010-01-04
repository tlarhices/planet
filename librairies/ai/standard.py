#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import random
import general


class Bulbe:
  _classe_ = "standard"
  sprite = None
  
  attaquants = None
  
  def __init__(self, sprite):
    self.sprite = sprite
    self.attaquants = {}
    
  def ping(self, temps):
    finAttaque = []
    for attaquant in self.attaquants:
      self.attaquants[attaquant]+=temps
      if self.attaquants[attaquant]>3.0:
        finAttaque.append(attaquant)
        
    for attaquant in finAttaque:
      del self.attaquants[attaquant]
      
  def sauvegarde(self):
    out = "bulbe-classe:"+self._classe_+":\r\n"
    general.TODO("Sauvegarde du bulbe"+str(self._classe_))
    return out
      
  def ennui(self):
    #On fait se promener le gugusse en rond sans but (bouffe quelques watts de pathfinding)
    point = general.planete.geoide.trouveSommet(self.sprite.position)
    cible = point
    for i in range(2, int(random.random()*6)):
      cible = random.choice(general.planete.geoide.voisinage[cible])
    self.sprite.marcheVers(cible)
    return True
      
  def seFaitAttaquerPar(self, sprite):
    self.attaquants[sprite]=0.0
