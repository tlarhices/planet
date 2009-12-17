#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

from standard import Bulbe as std

class Bulbe(std):
  _classe_ = "bucheron"
  
  def __init__(self, sprite):
    std.__init__(self, sprite)
    
  def ping(self, temps):
    std.ping(self, temps)
      
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
      self.sprite.ai.comportement.piller(sprite, 0.75)
