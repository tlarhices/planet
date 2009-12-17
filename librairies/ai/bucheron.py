#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

class Bulbe:
  _classe_ = "bucheron"
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
    #Quand un bûcheron s'ennuie, il va couper un arbre s'il a pas du ois plein les poches
    
    if self.sprite.taillePoches["construction"]<=self.sprite.contenu["construction"]:
      print "poches pleines"
      print "TODO vider les poches"
      for type in self.sprite.contenu.keys():
        self.sprite.contenu[type] = 0.0
      return
    sprite = self.sprite.chercheSpriteProche(-1, ["construction"], None, False)
    if sprite != None:
      print self.sprite.id,"va couper l'arbre",sprite.id
      self.sprite.marcheVers(sprite.position)
      self.sprite.coupeArbre(sprite)
      
  def seFaitAttaquerPar(self, sprite):
    self.attaquants[sprite]=0.0
