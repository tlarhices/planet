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
    
  def pingBulbe(self, temps):
    std.pingBulbe(self, temps)
    if self.rechercheSprite!=None:
      if isinstance(self.rechercheSprite, str) or self.rechercheSprite.poll():
        if isinstance(self.rechercheSprite, str):
          spriteid, cheminstr = self.rechercheSprite.split("||")
        else:
          result = self.rechercheSprite.recv()
          if result == None:
            print "rien trouvé"
            self.rechercheSprite = None
            return
          spriteid, cheminstr = result.split("||")
          
        if cheminstr.lower()!="none":
          cheminstr=cheminstr[1:-1].split(",")
          chemin=[self.sprite.position]
          for elem in cheminstr:
            chemin.append(int(elem))
          
          if spriteid != None:
            sprite=None
            for spr in general.planete.spritesJoueur:
              if spr.id==spriteid:
                sprite=spr
            for spr in general.planete.spritesNonJoueur:
              if spr.id==spriteid:
                sprite=spr
            if sprite!=None:
              chemin.append(sprite.position)
              if sprite.stock:
                print self.sprite.id,"va se vider les poches à",sprite.id,"en suivant",chemin
                self.dernierStock = sprite
                self.sprite.suitChemin(chemin, sprite.position)
                self.sprite.ai.comportement.videPoches(sprite, 0.75)
              else:
                print self.sprite.id,"va couper l'arbre",sprite.id,"en suivant",chemin
                self.dernierArbre = sprite
                self.sprite.suitChemin(chemin, sprite.position)
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
      if general.planete.spritesNonJoueur.count(self.dernierArbre)>0:
        self.sprite.ai.comportement.piller(self.dernierArbre, 0.75)
      else:
        #Cet arbre n'est plus, on va devoir en couper un autre
        self.dernierArbre = None
    else:
      self.dernierArbre = None
      self.dernierePositionArbre = None
      self.rechercheSprite = self.sprite.ai.comportement.chercheSpriteProche(False, ["construction"], None, False)
    return True
    
  def stop(self):
    self.rechercheSprite = None
    self.dernierArbre = None
    self.dernierePositionArbre = None
