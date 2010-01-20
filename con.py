#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import random
import time

T=10
grilleSol = []
grilleMonte = []
grilleDescend = []
grillePlan = []
  
for i in range(0,T):
  grilleSol.append([0.0,]*T)
  grilleMonte.append([0,]*T)
  grilleDescend.append([0,]*T)
  grillePlan.append([0,]*T)
  for j in range(0,T):
    grilleSol[i][j] = 0.0#random.random()*100-50
    grilleMonte[i][j] = int(random.random()+0.5)
    grilleDescend[i][j] = int(random.random()+0.5)
    grillePlan[i][j] = int(random.random()+0.5)

def sommeVoisin(tab, x, y):
  somme=0
  for i in (-1, 0, 1):
    for j in (-1, 0, 1):
      if x+i>=0 and y+j>=0 and x+i<T and y+j<T:
        if i!=0 or j!=0:
          somme+=tab[x+i][y+j]
  return somme
  
def cellule(tab):
  copie = []
  for i in range(0,T):
    copie.append([0,]*T)
    for j in range(0,T):
      copie[i][j] = tab[i][j]
      
  for i in range(0,T):
    for j in range(0,T):
      somme = sommeVoisin(copie, i, j)
      if copie[i][j]==0 and (somme==3 or False):#somme==6):
        tab[i][j]=1
      if copie[i][j]==1:
        if somme==2 or somme==3:
          tab[i][j]=1
        else:
          tab[i][j]=0
        
  return tab
  
while True:
  grilleMonte = cellule(grilleMonte)
  grilleDescend = cellule(grilleDescend)
  grillePlan = cellule(grillePlan)
  for i in range(0,T):
    for j in range(0,T):
      if grilleMonte[i][j]==1 and grilleDescend[i][j]==0 and grillePlan[i][j]==0:
        grilleSol[i][j]+=1
      elif grilleMonte[i][j]==0 and grilleDescend[i][j]==1 and grillePlan[i][j]==0:
        grilleSol[i][j]-=1
      elif grilleMonte[i][j]==0 and grilleDescend[i][j]==0 and grillePlan[i][j]==1:
        grilleSol[i][j]=sommeVoisin(grilleSol,i,j)/8.0
      elif grilleMonte[i][j]==1 and grilleDescend[i][j]==1 and grillePlan[i][j]==1:
        grilleMonte[i][j] = int(random.random()+0.5)
        grilleDescend[i][j] = int(random.random()+0.5)
        grillePlan[i][j] = int(random.random()+0.5)
      else:
        grilleMonte[i][j] = abs(grilleDescend[i][j]+grillePlan[i][j]-1)
        grilleDescend[i][j] = abs(grilleMonte[i][j]+grillePlan[i][j]-1)
        grillePlan[i][j] = abs(grilleMonte[i][j]+grilleDescend[i][j]-1)
      if random.random()>0.8:
        grille = random.choice((grilleMonte, grilleDescend, grillePlan))
        grille[i][j] = int(random.random()+0.5)
      if grilleSol[i][j]>=100:
        grilleSol[i][j] = 100
        grilleMonte[i][j] = 0
        grillePlan[i][j] = 0
        grilleDescend[i][j] = 1
      if grilleSol[i][j]<=-100:
        grilleSol[i][j] = -100
        grilleDescend[i][j] = 0
        grillePlan[i][j] = 0
        grilleMonte[i][j] = 1
      print int(grilleSol[i][j]),
    print
  raw_input()
