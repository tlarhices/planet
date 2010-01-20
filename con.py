#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import random
import time
import math

grilleSol = []
grilleStress = []
grilleNormale = []
  
T=10
  
for i in range(0,T):
  grilleSol.append([0.0,]*T)
  grilleStress.append([0.0,]*T)
  grilleNormale.append([(0.0,0.0,0.0),]*T)
  for j in range(0,T):
    grilleSol[i][j] = 0.0#random.random()*100-50
    grilleStress[i][j] = 1.0
    grilleNormale[i][j] = (random.random()-0.5, random.random()-0.5, random.random()-0.5)

def norme(vecteur):
  x,y,z = vecteur
  if x<0 or y<0 or z<0:
    return -math.sqrt(x*x+y*y+z*z)
  elif x<0 and y<0 and z<0:
    return -math.sqrt(x*x+y*y+z*z)
  else:
    return math.sqrt(x*x+y*y+z*z)
  
while True:
  for i in range(0,T):
    for j in range(0,T):
      grilleSol[i][j]+=grilleStress[i][j]
      grilleSol[i][j]=max(-100, grilleSol[i][j])
      grilleSol[i][j]=min(100, grilleSol[i][j])
      grilleStress[i][j] = grilleStress[i][j]+grilleStress[i][j]*norme(grilleNormale[i][j])
      x,y,z = grilleNormale[i][j]
      nx = min(T-1, max(0, int(i+x*4-2)))
      ny = min(T-1, max(0, int(j+y*4-2)))
      xa, ya, za = grilleNormale[nx][ny]
      grilleNormale[nx][ny]=(x+xa)/2,(y+ya)/2,(z+za)/2
      print int(grilleSol[i][j]), 
    print
  raw_input()
