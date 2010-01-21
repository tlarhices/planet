#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import math, os, sys
from pandac.PandaModules import *

configuration = None
  
def floatise(vecteur):
  """Caste les éléments d'un vecteur vers float"""
  out = []
  for element in vecteur:
    out.append(float(element))
  return out
  
def degVersRad(angle):
  """Transforme des degrés en radiants"""
  return float(angle)/180*math.pi
  
"""def cartesienVersSpherique(point):
  ""Passe les coordonnées d'un point du système cartésien au système sphérique""
  x,y,z = floatise(point)
  rayon = math.sqrt(x*x+y*y+z*z)
  if x<=0:
    anglex = math.asin(y/math.sqrt(x*x+y*y))
  else:
    anglex = math.pi-math.asin(y/math.sqrt(x*x+y*y))
  angley = math.acos(z/rayon)
  return [rayon, anglex, angley]
  
def spheriqueVersCartesien(rayon, anglex, angley):
  ""Passe les coordonnées d'un point du système sphérique au système cartésien""
  rayon, anglex, angley = floatise([rayon, anglex, angley])
  x = -rayon * math.cos(anglex) * math.sin(angley)
  y = rayon * math.sin(anglex) * math.sin(angley)
  z = rayon * math.cos(angley)
  return [x,y,z]
  """
  
import time
chronos={}
chronchron={}
def startChrono(nomChrono):
  """Sauvegarde l'heure de début"""
  if not configuration.getConfiguration("debug", "general", "debug_utilise_statistiques", "f", bool):
    return
  nomChrono = nomChrono.lower().strip()
  if nomChrono in chronos.keys():
    print "chrono ",nomChrono,"déjà existant, écrasement"
  chronos[nomChrono] = time.time()
  
def stopChrono(nomChrono):
  """Sauvegarde l'heure de fin"""
  if not configuration.getConfiguration("debug", "general", "debug_utilise_statistiques", "f", bool):
    return
  nomChrono = nomChrono.lower().strip()
  if not nomChrono in chronos.keys():
    print "chrono ",nomChrono,"innexistant"
    return None
  A = chronos[nomChrono]
  
  if nomChrono not in chronchron.keys():
    chronchron[nomChrono] = []
    
  chronchron[nomChrono].append(time.time() -A)
  del chronos[nomChrono]

def afficheStatChrono():
  """Affiche les statistiques de durées d'appels"""
  if not configuration.getConfiguration("debug", "general", "debug_utilise_statistiques", "f", bool):
    return
  for element in chronchron.keys():
    print "########"
    print element
    cpt = 0.0
    tot = 0.0
    for temps in chronchron[element]:
      cpt+=1
      tot+=temps
    print "Itérations :", cpt
    print "Total :", tot
    print "Moyen :", tot/cpt
    print "########"
    

def map3dToRender2d(node, point):
    """Maps the indicated 3-d point (a Point3), which is relative to
    the indicated NodePath, to the corresponding point in the aspect2d
    scene graph. Returns the corresponding Point3 in aspect2d.
    Returns None if the point is not onscreen. """
    #pos=map3dToAspect2d(render,node.getPos()) 
    # Convert the point to the 3-d space of the camera
    p3 = base.cam.getRelativePoint(node, point)
    # Convert it through the lens to render2d coordinates
    p2 = Point2()
    if not base.camLens.project(p3, p2):
       return None
    return Point3(p2[0], 0, p2[1])

def map3dToAspect2d(node, point):
    """Maps the indicated 3-d point (a Point3), which is relative to
    the indicated NodePath, to the corresponding point in the aspect2d
    scene graph. Returns the corresponding Point3 in aspect2d.
    Returns None if the point is not onscreen. """
    r2d = map3dToRender2d(node, point)
    if r2d==None:
       return None
    # And then convert it to aspect2d coordinates
    a2d = aspect2d.getRelativePoint(render2d, r2d)
    return a2d 
    
    
    
def pluck(p1, p2):
  pluck = []
  pluck.append(p1[0]*p2[1]-p2[0]*p1[1])
  pluck.append(p1[0]*p2[2]-p2[0]*p1[2])
  pluck.append(p1[0]-p2[0])
  pluck.append(p1[1]*p2[2]-p2[1]*p1[2])
  pluck.append(p1[2]-p2[2])
  pluck.append(p2[1]-p1[1])
  return pluck

def sideProduct(p11, p12, p21, p22):
  pl1 = pluck(p11, p12)
  pl2 = pluck(p21, p22)
  return pl1[0]*pl1[4]+pl1[1]*pl2[5]+pl1[2]*pl2[3]+pl1[3]*pl2[2]+pl1[4]*pl2[0]+pl1[5]*pl2[1]
  
def testIntersectionTriangleDroite(p1, p2, p3, l1, l2):
  s1 = sideProduct(l1, l2, p1, p2)
  s2 = sideProduct(l1, l2, p2, p3)
  s3 = sideProduct(l1, l2, p3, p1)
   
  if(s1==0 and s2==0 and s3==0):  
    print " Line and Triangle are coplanar" 
    #TODO compute_2D_intersection(T,L)
    #On a jamais ce cas là
    return None
  elif(( s1>0 and s2>0 and s3>0) or (s1<0 and s2<0 and s3<0)): 
    print " Line passes through the triangle"
    return (p3[0] + p2[0] + p1[0])/3.0, (p3[1] + p2[1] + p1[1])/3.0, (p3[2] + p2[2] + p1[2])/3.0
  elif(s1==0 and s2*s3>0):
    print " Line passes through the edge p1 p2"
    return (p2[0] + p1[0])/2.0, (p2[1] + p1[1])/2.0, (p2[2] + p1[2])/2.0
  elif(s2==0 and s1*s3>0):
    print " Line passes through the edge p2 p3"
    return (p3[0] + p2[0])/2.0, (p3[1] + p2[1])/2.0, (p3[2] + p2[2])/2.0
  elif(s3==0 and s1*s2>0):
    print " Line passes through the edge p3 p1"
    return (p1[0] + p3[0])/2.0, (p1[1] + p3[1])/2.0, (p1[2] + p3[2])/2.0
  elif(s1==0 and s2==0):
    print " Line passes through the vertex"
    return p2
  elif(s1==0 and s3==0):
    print " Line passes through the vertex" 
    return p1
  elif(s2==0 and s3==0):
    print " Line passes through the vertex"
    return p3
  return None
    
    
    
def ligneCroiseSphere(l1, l2, c, r):
  """Retourne None si la ligne n'intersecte pas la sphère, sinon retourne le ou les points d'intersection"""
  #Teste si le segment croise la sphere
  def intersecte(l1, l2, c):
    x1, y1, z1 = l1
    x2, y2, z2 = l2
    x3, y3, z3 = c
    u=((x3 - x1)*(x2 - x1) + (y3 - y1)*(y2 - y1) + (z3 - z1)*(z2 - z1))/((x2 - x1)*(x2 - x1) + (y2 - y1)*(y2 - y1) + (z2 - z1)*(z2 - z1))
    if u<0 or u>1:
      return False
    return True
    
  if not intersecte(l1, l2, c):
    return None
  
  #Calcul les facteurs de la résolution du croisement ligne / sphere
  x1, y1, z1 = l1
  x2, y2, z2 = l2
  x3, y3, z3 = c
  a = (x2 - x1)*(x2 - x1) + (y2 - y1)*(y2 - y1) + (z2 - z1)*(z2 - z1)
  b = 2*((x2 - x1)*(x1 - x3) + (y2 - y1)*(y1 - y3) + (z2 - z1)*(z1 - z3))
  c = x3*x3 + y3*y3 + z3*z3 + x1*x1 + y1*y1 + z1*z1 - 2*(x3*x1 + y3*y1 + z3*z1) - r*r

  #On calcul un u, c'est à dire la position du point sur la ligne l1-l2 en partant de l1
  #Permet de retrouver les coordonnées
  def coordDepuisU(l1, l2, u):
    x1, y1, z1 = l1
    x2, y2, z2 = l2
    return (x1 + u*(x2 - x1), y1 + u*(y2 - y1), z1 + u*(z2 - z1))

  #Le facteur de résolution de l'équation du second degré
  facteur = b*b - 4*a*c
  if facteur < 0:
    return None #Pas de collision
  elif facteur == 0:
    return [coordDepuisU(l1, l2, -b/2*a)] #Une seule (droite tangente)
  else:
    return [coordDepuisU(l1, l2, (-b + math.sqrt(facteur))/2*a), coordDepuisU(l1, l2, (-b - math.sqrt(facteur))/2*a)] #2 collisions
    
def projetePointSurPlan(normale, pointPlan, pointProj):
  #Calcul du plan
  #a*x + b*y + c*z + d = 0
  a, b, c = normale
  x, y, z = pointPlan
  d = -a*x - b*y - c*z
  
  #calcul de la projection
  x, y, z = pointProj
  #comme P(xp, yp, zp) est sur le plan on a :
  #a*xp+b*yp+c*zp+d=0
  #et comme le vecteur -pointProj-P-> est selon la normale
  #xp=x-k*a
  #yp=y-k*a
  #zp=z-k*a
  k = (a*x+b*y+c*z+d)/(a*a+b*b+c*c)
  xp=x-k*a
  yp=y-k*a
  zp=z-k*a
  return xp, yp, zp
  
def lerp(pt1, v1, pt2, v2, pt3, v3, pt):
  d1=(pt1-pt).length()
  d2=(pt2-pt).length()
  d3=(pt3-pt).length()
  s = d1+d2+d3
  d1 = d1/s
  d2 = d2/s
  d3 = d3/s
  return v1*d1+v2*d2+v3*d3
  
  
LISTE_TODO = []
def chargeTODO():
  try:
    fichier = open(os.path.join("todo.txt"))
  except IOError:
    return
    
  for ligne in fichier:
    ligne = ligne.strip()
    if ligne not in LISTE_TODO:
      LISTE_TODO.append(ligne)
def sauveTODO():
  fichier = open(os.path.join("todo.txt"), "w")
  for todo in LISTE_TODO:
    fichier.write(todo+"\r\n")
def TODO(texte):
  #On attrape le fichier et la fonction qui a appelé le TODO
  frame = sys._getframe(1)
  texte=str(frame.f_code.co_filename)+"::"+"??"+"::"+str(frame.f_code.co_name)+" > "+texte.strip()
  if texte not in LISTE_TODO:
    LISTE_TODO.append(texte)
    LISTE_TODO.sort()
    sauveTODO()
    
    print "TODO :: "+texte
