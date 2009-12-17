#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import random

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
      
  def ennui(self):
    #On fait se promener le gugusse en rond sans but (bouffe quelques watts de pathfinding)
    point = self.sprite.planete.trouveSommet(self.sprite.position)
    cible = point
    for i in range(2, int(random.random()*6)):
      cible = random.choice(self.sprite.planete.voisinage[cible])
    self.sprite.marcheVers(cible)
      
  def seFaitAttaquerPar(self, sprite):
    self.attaquants[sprite]=0.0
