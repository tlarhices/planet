#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import math

DEBUG_GENERE_PLANETE = True #Donne des infos de debug sur la génération d'une nouvelle planète
DEBUG_CHARGE_PLANETE = True #Donne des infos de debug sur le chargement des fichiers
DEBUG_CHARGE_PLANETE_VERBOSE = False #Donne des infos de debug sur le chargement des sommets et facettes
DEBUG_AI_GRAPHE_DEPLACEMENT_CONSTRUCTION = True #Donne des infos de debug sur la construction de l'arbre de déplacement
DEBUG_AI_GRAPHE_DEPLACEMENT_PROMENADE = True #Donne des infos de debug sur les tests de l'arbre de déplacement
DEBUG_PANDAUI_GUI = False #Donne des infos sur la gestion de l'UI
DEBUG_PANDAUI_CLIC = False #Donne des infos sur la gestion des clics dans l'UI
DEBUG_PANDAUI_PURGE = False #Donne des infos sur la gestion de la suppression des composants dans l'UI

DEBUG_USE_STAT = True

WIREFRAME = False
if WIREFRAME:
  print "DANGER :: HACK :: UTILISATION DU MODE FILAIRE [general.py]"
    
    
configuration = None
  
def normeVecteurCarre(vecteur):
  """Retourne la racine de la somme des carrés des membres de 'vecteur'"""
  pile = 0
  for element in vecteur:
    pile = pile + element * element
  return pile
  
def normeVecteur(vecteur):
  return math.sqrt(normeVecteurCarre(vecteur))
  
def normaliseVecteur(vecteur):
  """Normalise le vecteur"""
  norme = normeVecteur(vecteur)
  if norme==0:
    return vecteur
  return multiplieVecteur(vecteur, 1/norme)
  
def normaliseVecteurCarre(vecteur):
  """Normalise le vecteur avec la norme au carré"""
  norme = normeVecteurCarre(vecteur)
  if norme==0:
    return vecteur
  return multiplieVecteur(vecteur, 1/norme)
  
def multiplieVecteur(vecteur, valeur):
  """Multiplie toutes les coordonnées d'un vecteur par une même valeur"""
  out = []
  for element in vecteur:
    out.append(float(element) * float(valeur))
  return out
  
def crossProduct(v1, v2):
  out = [0,0,0]
  out[0] = v1[1]*v2[2]-v1[2]*v2[1]
  out[1] = v1[2]*v2[0]-v1[0]*v2[2]
  out[2] = v1[0]*v2[1]-v1[1]*v2[0]
  return out
      
def sommeVecteurs(v1, v2):
  """Ajoute 2 vecteurs"""
  v1 = v1[:]
  v2 = v2[:]
  
  if len(v1)!=len(v2):
    print "erreur de dimension de vecteur, on tente tout de même"
    if len(v1)>len(v2):
      t = v1
      v1 = v2
      v2 = t
  for i in range(0, len(v1)):
    v2[i]=v2[i]+v1[i]
  return v2
  
def retraitVecteurs(v1, v2):
  """Retire 2 vecteurs"""
  v1 = v1[:]
  v2 = v2[:]
  
  if len(v1)!=len(v2):
    print "erreur de dimension de vecteur, on tente tout de même"
    if len(v1)>len(v2):
      t = v1
      v1 = v2
      v2 = t
  for i in range(0, len(v1)):
    v2[i]=v1[i]-v2[i]
  return v2
      
def floatise(vecteur):
  """Caste les éléments d'un vecteur vers float"""
  out = []
  for element in vecteur:
    out.append(float(element))
  return out
  
def distanceCarree(point1, point2):
  """Calcule le carré de la distance entre 2 points"""
  
  #Tentative d'accélération pour le cas spécial 3
  if len(point1)==3:
    return (point2[0]-point1[0])*(point2[0]-point1[0])+(point2[1]-point1[1])*(point2[1]-point1[1])+(point2[2]-point1[2])*(point2[2]-point1[2])
    
  if len(point1) != len(point2):
    raise ValueError, "Distance :: point1 et point2 n'ont pas les mêmes dimentions"
    
  pile = 0
  for i in range(0, len(point1)):
    tmp = point2[i]-point1[i]
    pile = pile + tmp*tmp
  return pile
  
def distance(point1, point2):
  """Calcule la distance entre 2 points"""
  return math.sqrt(distanceCarree(point1, point2))
  
def degVersRad(angle):
  """Transforme des degrés en radiants"""
  return float(angle)/180*math.pi
  
def cartesienVersSpherique(point):
  """Passe les coordonnées d'un point du système cartésien au système sphérique"""
  x,y,z = floatise(point)
  rayon = math.sqrt(x*x+y*y+z*z)
  if x<=0:
    anglex = math.asin(y/math.sqrt(x*x+y*y))
  else:
    anglex = math.pi-math.asin(y/math.sqrt(x*x+y*y))
  angley = math.acos(z/rayon)
  return [rayon, anglex, angley]
  
def spheriqueVersCartesien(rayon, anglex, angley):
  """Passe les coordonnées d'un point du système sphérique au système cartésien"""
  rayon, anglex, angley = floatise([rayon, anglex, angley])
  x = -rayon * math.cos(anglex) * math.sin(angley)
  y = rayon * math.sin(anglex) * math.sin(angley)
  z = rayon * math.cos(angley)
  return [x,y,z]
  
  
def memeDirectionRotation(p1, p2, p3, norm):
  i = (((p2[1] - p1[1])*(p3[2] - p1[2])) - ((p3[1] - p1[1])*(p2[2] - p1[2])))
  j = (((p2[2] - p1[2])*(p3[0] - p1[0])) - ((p3[2] - p1[2])*(p2[0] - p1[0])))
  k = (((p2[0] - p1[0])*(p3[1] - p1[1])) - ((p3[0] - p1[0])*(p2[1] - p1[1])))

  scal = i*norm[0] + j*norm[1] + k*norm[2]

  if scal < 0:
    return False
  return True

def testIntersectionTriangleDroite(p1, p2, p3, l1, l2):
  #Vecteur suivant la ligne
  Vx = l2[0] - l1[0]
  Vy = l2[1] - l1[1]
  Vz = l2[2] - l1[2]
  
  #Vecteur p1 -> p2
  V1x = p2[0] - p1[0]
  V1y = p2[1] - p1[1]
  V1z = p2[2] - p1[2]

  #Vecteur p2 -> p3
  V2x = p3[0] - p2[0]
  V2y = p3[1] - p2[1]
  V2z = p3[2] - p2[2]

  #Normale du triangle
  Nx = V1y*V2z-V1z*V2y
  Ny = V1z*V2x-V1x*V2z
  Nz = V1x*V2y-V1y*V2x

  #Produit scalaire entre la normale et le vecteur de la ligne
  #0 si //
  scal = Nx*Vx + Ny*Vy + Nz * Vz

  if scal < 0:
    #Recherche du point d'intersection ligne / triangle
    t = -(Nx*(l1[0]-p1[0])+Ny*(l1[1]-p1[1])+Nz*(l1[2]-p1[2]))/(Nx*Vx+Ny*Vy+Nz*Vz)

    int = multiplieVecteur((Vx, Vy, Vz), t)
    int = sommeVecteurs(int, l1)

    if memeDirectionRotation(p1, p2, int, (Nx, Ny, Nz)):
      if memeDirectionRotation(p2, p3, int, (Nx, Ny, Nz)):
          if memeDirectionRotation(p3, p1, int, (Nx, Ny, Nz)):
            return True
  return False

import time
chronos={}
chronchron={}
def startChrono(nomChrono):
  """Sauvegarde l'heure de début"""
  if not DEBUG_USE_STAT:
    return
  nomChrono = nomChrono.lower().strip()
  if nomChrono in chronos.keys():
    print "chrono ",nomChrono,"déjà existant, écrasement"
  chronos[nomChrono] = time.time()
  
def stopChrono(nomChrono):
  """Sauvegarde l'heure de fin"""
  if not DEBUG_USE_STAT:
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
  if not DEBUG_USE_STAT:
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