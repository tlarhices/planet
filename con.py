#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import random
import time

T=10
grilleType = []
grilleAltitude = []
  

def disp():
  for i in range(0,T):
    for j in range(0, T):
      print "% .2f" %grilleType[i][j],
    print

  for i in range(0,T):
    for j in range(0, T):
      print "% 2i" %int(grilleAltitude[i][j]),
    print

for i in range(0,T):
  grilleType.append([0.0,]*T)
  grilleAltitude.append([0,]*T)
  
  for j in range(0, T):
    val = random.random()
    if val<0.6:
      grilleType[i][j] = 1.0
    if val<0.3:
      grilleType[i][j] = -1.0
    grilleAltitude[i][j] = random.random()*100

disp()

pas = time.time()
while True:
  delta = time.time() - pas
  delta = delta*10000
  for i in range(0,T):
    for j in range(0, T):
      if grilleType[i][j]!=0:
        if grilleType[i][j]>0:
          signe = +1
        else:
          signe = -1
        
        grilleType[i][j] = abs(grilleType[i][j])
        grilleType[i][j] += delta*random.random()
        
        cpt=0
        if grilleType[i][j] > 100:
          cpt = int(grilleType[i][j]/100)
          grilleType[i][j] = grilleType[i][j]%100
          grilleType[i][j] = signe*grilleType[i][j]
          
          grilleAltitude[i][j]+=signe*cpt
          if abs(grilleAltitude[i][j])>100:
            grilleAltitude[i][j] = signe*100
            grilleType[i][j] = 0
            for a in (-1,0,1):
              for b in (-1,0,1):
                if i+a>=0 and j+b>=0 and i+a<T and j+b<T:
                  grilleType[i+a][j+b]+=signe      
        
  disp()
  pas = time.time()
  raw_input()