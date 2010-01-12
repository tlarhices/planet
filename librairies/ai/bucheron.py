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
  dernierArbre = None
  dernierePositionArbre = None
  dernierStock = None
  dernierePositionStock = None
  
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
            if sprite.stock:
              print self.sprite.id,"va se vider les poches à",sprite.id
              self.dernierStock = sprite
              self.sprite.marcheVers(sprite.position)
              self.sprite.ai.comportement.videPoches(sprite, 0.75)
            else:
              print self.sprite.id,"va couper l'arbre",sprite.id
              self.dernierArbre = sprite
              self.sprite.marcheVers(sprite.position)
              self.sprite.ai.comportement.piller(sprite, 0.75)
        self.rechercheSprite = None
      
  def sauvegarde(self):
    out = "bulbe-classe:"+self._classe_+":\r\n"
    return out
      
  def ennui(self):
    #Quand un bûcheron s'ennuie, il va couper un arbre s'il a pas du ois plein les poches
    if self.rechercheSprite!=None:
      general.TODO("ajouter une icone 'je réfléchit' au dessus des sprites qui calculent des trucs")
      return False #On cherche un sprite, on ne change donc pas d'activité

    if self.sprite.taillePoches["construction"]<=self.sprite.contenu["construction"]:
      self.rechercheSprite = self.sprite.ai.comportement.chercheSpriteProche(True, ["construction"], self.sprite.joueur, False)
      for type in self.sprite.contenu.keys():
        self.sprite.contenu[type] = 0.0
      return True
    print self.sprite.id, "cherche un arbre"
    if self.dernierArbre != None:
      #On retourne là où se trouvait le dernier arbre coupé
      if (self.sprite.position-self.dernierArbre.position).length() > self.sprite.distanceProche:
        print self.sprite.id,"retourne vers l'arbre",self.dernierArbre.id
        self.sprite.marcheVers(self.dernierArbre.position)
      #On lui dit de couper l'arbre
      if general.planete.sprites.count(self.dernierArbre)>0:
        self.sprite.ai.comportement.piller(self.dernierArbre, 0.75)
      else:
        #Cet arbre n'est plus, on va devoir en couper un autre
        self.dernierArbre = None
    else:
      self.dernierArbre = None
      self.dernierePositionArbre = None
      self.rechercheSprite = self.sprite.ai.comportement.chercheSpriteProche(False, ["construction"], None, False)
    return True
