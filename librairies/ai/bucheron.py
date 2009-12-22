#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

from standard import Bulbe as std
import general

class Bulbe(std):
  _classe_ = "bucheron"
  rechercheSprite = None
  
  def __init__(self, sprite):
    std.__init__(self, sprite)
    
  def ping(self, temps):
    std.ping(self, temps)
    if self.rechercheSprite!=None:
      if self.rechercheSprite.poll():
        spriteid = self.rechercheSprite.recv()
        
        if spriteid != None:
          sprite=None
          for spr in general.planete.sprites:
            if spr.id==spriteid:
              sprite=spr
          if sprite!=None:
            print self.sprite.id,"va couper l'arbre",sprite.id
            self.sprite.marcheVers(sprite.position)
            self.sprite.ai.comportement.piller(sprite, 0.75)
        self.rechercheSprite = None
      
  def ennui(self):
    #Quand un bûcheron s'ennuie, il va couper un arbre s'il a pas du ois plein les poches
    if self.rechercheSprite!=None:
      return #On cherche un sprite, on ne change donc pas d'activité
      
    if self.sprite.taillePoches["construction"]<=self.sprite.contenu["construction"]:
      print "poches pleines"
      print "TODO vider les poches"
      for type in self.sprite.contenu.keys():
        self.sprite.contenu[type] = 0.0
      return
    print self.sprite.id, "cherche un arbre"
    self.rechercheSprite = self.sprite.ai.comportement.chercheSpriteProche(-1, ["construction"], None, False)
