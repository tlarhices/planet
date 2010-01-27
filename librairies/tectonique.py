#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import random
from weakref import proxy

class Attracteur:
  position = None
  direction = None
  grille = None
  
  def __init__(self, force, grille):
    self.grille=grille
    self.position = random.choice(self.grille.voisinage.keys())
    self.force = force
    self.direction = [random.random(),random.random()]
    
  def pingAttracteur(self, temps):
    voisin=self.grille.voisinage[self.position]
    
    self.direction[0] = self.direction[0]+(random.random()*2-1.0)/5*temps
    self.direction[1] = self.direction[1]+(random.random()*2-1.0)/100*temps
    
    if abs(self.direction[1]>1.5):
      self.direction[1]=self.direction[1]/abs(self.direction[1])/10
      
    
    id = int(self.direction[0]*len(voisin))%len(voisin)
    #print self.direction, id
    if self.direction[1]>0.5:
      self.position=voisin[id]
      
    return self.force
    
  def getPosition(self):
    return self.grille.sommets[self.position]

class Tectonique:
  
  matriceAltitude = None
  attracteurs = None
  tailleX = None
  tailleY = None
  nombreAttracteurs = None
  
  def __init__(self, tailleX, tailleY, nombreAttracteurs):
    self.tailleX = tailleX
    self.tailleY = tailleY
    self.nombreAttracteurs = nombreAttracteurs
    self.matriceAltitude = []
    
    self.sommets = []
    
    for i in range(0, self.tailleX):
      self.matriceAltitude.append([])
      for j in range(0, self.tailleY):
        self.sommets.append((i,j))
        self.matriceAltitude[i].append(0.0)
    
    self.fabriqueVoisins()
      
    self.attracteurs = []
    for i in range(0, self.nombreAttracteurs):
      force = random.random()
      self.attracteurs.append(Attracteur(+force, proxy(self)))
      self.attracteurs.append(Attracteur(-force, proxy(self)))

  def fabriqueVoisins(self):
    self.voisinage = {}
    for i in range(0, len(self.sommets)):
      self.voisinage[i] = []
      for k in [-1, 0, 1]:
        for l in [-1, 0, 1]:
          if k!=0 or l!=0:
            x,y = self.sommets[i]
            if x+k<0:
              x=x+self.tailleX-1
            if x+k>=self.tailleX:
              x=x-self.tailleX+1
            if y+l<0:
              y=y+self.tailleY-1
            if y+l>=self.tailleY:
              y=y-self.tailleY+1
            self.voisinage[i].append(self.sommets.index((x+k,y+l)))
    
  def pingTectonique(self, temps):
    for i in range(0, self.nombreAttracteurs):
      valeur = self.attracteurs[i].pingAttracteur(temps)
      x,y = self.attracteurs[i].getPosition()
      self.matriceAltitude[x][y]+=valeur*temps#/10
      self.matriceAltitude[x][y] = min(max(self.matriceAltitude[x][y], -9), 9)
            
  def affiche(self):
    for i in range(0, self.tailleX):
      for j in range(0, self.tailleY):
        aff = False
        for att in self.attracteurs:
          if att.getPosition()[0]==i and att.getPosition()[1]==j and not aff:
            print "##",
            aff=True
        if not aff:
          print "%+i" %self.matriceAltitude[i][j],
      print
    print "="*50
    
    """for i in range(0, self.nombreAttracteurs):
      print i,":", (self.attracteurs[i].direction[0]/10*0.1,self.attracteurs[i].direction[1]/10*0.1)"""
        
if __name__=="__main__":
  tectonique = Tectonique(50,25,10)
  while True:
    tectonique.affiche()
    tectonique.pingTectonique(0.1)
    #raw_input()