#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general

import random
import math
import sys
import os
import zipfile

from weakref import proxy

from element import Element
from tectonique import Tectonique
import sprite

from pandac.PandaModules import *

class Geoide:
  tesselation = None #Le niveau de subdivision que l'on souhaite obtenir
  delta = None #Le degré de perturbation maximal de la surface par rapport à 0
  
  sommets = None #La liste des sommets
  elements = None #La liste des faces (indices des sommets)
  racine = None #Point (0,0,0) de la planète selon lequel tout est ajouté
  tectonique = None
  
  voisinage = None #Dictionnaire associant a chaque sommet les indices des sommets auxquels il est connecté
                   #Construit par self.fabriqueVoisinage
  sommetDansFace = None #Dictionnaire associant à chaque sommet les faces dans lesquelles il se trouve
                        #Construit par les constructeurs de chaque face (Element())
  survol = None #L'id du sommet le plus proche du curseur (None si rien)

  niveauEau = None #Altitude à laquelle se trouve l'eau
  modeleEau = None #Modele 3D de l'eau
  niveauCiel = None #Altitude à laquelle se trouve le ciel
  modeleCiel = None #Modele 3D du ciel
  azure = None
  lastMAJPosSoleil=100000.0 #Le temps depuis lequel on n'a pas remis à jour la carte du soleil
  dureeMAJPosSoleil=23.0 #Le temps que l'on attends avant de recalculer la carte du soleil


  fini = False
  
  # Initialisation -----------------------------------------------------
  def __init__(self):
    """Constructeur, initialise les tableaux"""
    self.sommets = [] #Pas de sommets
    self.elements = [] #Pas de faces
    self.voisinage = {} #Pas de sommet, donc pas de voisinage
    self.sommetDansFace = {} #Pas de faces, donc pas d'association
    self.survol = None #Le curseur n'est au dessus de rien par défaut
    
    self.dureeMAJPosSoleil = general.configuration.getConfiguration("affichage", "Minimap", "dureeMAJPosSoleil", "23.0", float)
    
    self.fini = False
    
    taskMgr.add(self.pingGeoide, "BouclePrincipale-geoide")
    
  def fabriqueVoisinage(self):
    """
    Remplit le dictionnaire self.voisinage de la façon suivante :
    self.voisinage[a]=[b, c, d, e, ...]
    avec a, b, c, d, e les indices des sommets et de telle sorte qu'il y ai une arrête ab, ac, ad, ae, ...
    """
    self.voisinage = {}
    totSommets = len(self.sommets)
    for sommet in range(0, totSommets):
      if general.configuration.getConfiguration("debug", "planete", "debug_genere_planete", "f", bool):
        if sommet%250==0:
          general.planete.afficheTexte("Calcul du voisinage... %(a)i/%(b)i", parametres={"a":sommet, "b":totSommets}, type="construction")
      faces = self.sommetDansFace[sommet]
      for face in faces:
        if face.enfants == None: #On ne considère que les faces les plus subdivisées
          self.ajouteNoeud(sommet, face.sommets[0])
          self.ajouteNoeud(sommet, face.sommets[1])
          self.ajouteNoeud(sommet, face.sommets[2])
        
  def ajouteNoeud(self, pt1, pt2):
    """Ajoute un noeud au voisinage"""
    if pt1==pt2:
      return
      
    if pt1 not in self.voisinage.keys():
      self.voisinage[pt1]=[]
    
    if pt2 not in self.voisinage[pt1]:
      self.voisinage[pt1].append(pt2)
      
  def detruit(self):
    """Détruit le géoïde et tout ce qui lui est associé"""
    self.fini = True
    self.sommets=[]
    self.lignes=[]
    for element in self.elements:
      element.detruit()
    if self.racine!=None:
      self.racine.detachNode()
      self.racine.removeNode()
  # Fin Initialisation -------------------------------------------------
    
  # Constructions géométriques -----------------------------------------
  def fabriqueNouveauGeoide(self, tesselation, delta):
    """
    Construit un nouveau geoide :
    tesselation : Le nombre de subdivision que l'on souhaite faire
    delta : Le niveau maximal de perturbation de la surface que l'on souhaite
    """
    self.niveauEau = 1.0 #La planète a un rayon de 1.0 en dessous de son noeud, on place l'eau juste a sa surface
    self.sommets = [] #Pas de sommets
    self.elements = [] #Pas de faces
    self.voisinage = {} #Pas de sommet, donc pas de voisinage
    self.sommetDansFace = {} #Pas de faces, donc pas d'association
    
    #Permet d'être sûr que ce sont bien des valeurs valides
    self.delta = float(delta)
    self.tesselation = int(tesselation)
    
    #On regarde si on a pas déjà calculé une sphère a ce niveau de tesselation
    if os.path.isfile(os.path.join(".","data","pre-tesselate",str(tesselation))):
      #On charge la sphere pre-tesselée
      self.charge(os.path.join(".","data","pre-tesselate",str(tesselation)), simple=True)
      self.fini=False
    else:
      #On a pas de sphère pré-tesselée, on cherche la plus grande tesselation que l'on ai qui soit inférieure à celle souhaitée
      last = -1
      for i in range(0, tesselation):
        if os.path.isfile(os.path.join(".","data","pre-tesselate",str(i+1))):
          last = i+1
      if last == -1:
        #On a pas du tout de sphère donc on commence à 0
        self.fabriqueSphere()
        last = 0
      else:
        #On recommence à la meilleure que l'on ai
        self.charge(os.path.join(".","data","pre-tesselate",str(last)), simple=True)
        self.fini=False
        
      #On remet le niveau de tesselation qu'il faut, le chargement aura tout pété
      self.tesselation = int(tesselation)
      self.delta = float(delta)

      #On tesselate la sphère courante
      for i in range(last, self.tesselation):
        cpt=0.0
        tot=len(self.elements)
        for element in self.elements:
          cpt+=1
          if general.configuration.getConfiguration("debug", "planete", "debug_genere_planete", "f", bool):
            general.planete.afficheTexte("Tesselation en cours... %(a)i/%(b)i::%(c)i/%(d)i", parametres={"a": i+1, "b": self.tesselation, "c": cpt, "d": tot}, type="construction")
          element.tesselate()
        self.tesselation = int(tesselation)
        self.delta = float(delta)
        #On sauvegarde la tesselation courante pour gagner du temps pour les prochains chargements
        self.sauvegarde(os.path.join(".","data","pre-tesselate",str(i+1)), i+1)
        
    self.tesselation = int(tesselation)
    self.delta = float(delta)
    self.fabriqueVoisinage()
        
    #Place un unique point sous lequel tous les objets 3D vont exister
    self.racine = render.attachNewNode("planete")
    
    #On perturbe le sol
    self.fabriqueSol()
    
    #On applique un flou sur le sol pour faire des collines arrondies
    for i in range(0, int(self.tesselation*0.5+0.5)):
      self.flouifieSol(3)
    
    #On étend la gamme d'altitudes
    self.normaliseSol()
    
    general.planete.aiNavigation.grapheDeplacement()
    
  def fabriqueSphere(self):
    self.fabriqueSphereIcosahedre()
    
  def fabriqueSphereOctahedre(self):
    """fabrique un octahèdre régulier de rayon 1.0"""
    XP = Vec3(1.0,0.0,0.0)
    XM = Vec3(-1.0,0.0,0.0)
    YP = Vec3(0.0,1.0,0.0)
    YM = Vec3(0.0,-1.0,0.0)
    ZP = Vec3(0.0,0.0,1.0)
    ZM = Vec3(0.0,0.0,-1.0)
    
    self.sommets = [XP, XM, YP, YM, ZP, ZM]
    iXP = 0;iXM = 1;iYP = 2;iYM = 3;iZP = 4;iZM = 5
    self.elements = []
    self.elements.append(Element("["+str(len(self.elements))+"]", iXP, iZP, iYP, proxy(self), 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYP, iZP, iXM, proxy(self), 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iXM, iZP, iYM, proxy(self), 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYM, iZP, iXP, proxy(self), 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iXP, iYP, iZM, proxy(self), 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYP, iXM, iZM, proxy(self), 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iXM, iYM, iZM, proxy(self), 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYM, iXP, iZM, proxy(self), 0, None))
    
  def fabriqueSphereIcosahedre2(self):
    a = math.sqrt(2.0/(5.0+math.sqrt(5.0)))
    b = math.sqrt(2.0/(5.0-math.sqrt(5.0)))
    
    self.sommets = []
    self.sommets.append(Vec3(-a, 0.0, b))
    self.sommets.append(Vec3(a, 0.0, b))
    self.sommets.append(Vec3(-a, 0.0, -b))
    self.sommets.append(Vec3(a, 0.0, -b))
    self.sommets.append(Vec3(0.0, b, a))
    self.sommets.append(Vec3(0.0, b, -a))
    self.sommets.append(Vec3(0.0, -b, a))
    self.sommets.append(Vec3(0.0, -b, -a))
    self.sommets.append(Vec3(b, a, 0.0))
    self.sommets.append(Vec3(-b, a, 0.0))
    self.sommets.append(Vec3(b, -a, 0.0))
    self.sommets.append(Vec3(-b, -a, 0.0))
    
    #Faces
    self.elements = []
    self.elements.append(Element("["+str(len(self.elements))+"]", 1,  4, 0, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 4, 9, 0, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 4, 5, 9, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 8, 5, 4, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 1, 8, 4, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 1, 10, 8, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 10, 3, 8, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 8, 3, 5, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 3, 2, 5, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 3, 7, 2, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 3, 10, 7, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 10, 6, 7, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 6, 11, 7, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 6, 0, 11, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 6, 1, 0, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 10, 1, 6, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 11, 0, 9, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 2, 11, 9, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 5, 2, 9, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", 11, 2, 7, self, 0, None))
    
  def fabriqueSphereIcosahedre(self):
    """fabrique un icosahèdre régulier de rayon 1.0"""
    t=(1.0+math.sqrt(5.0))/2.0
    tau=t/math.sqrt(1.0+t*t)
    one=1.0/math.sqrt(1.0+t*t)
    
    #Sommets
    ZA = Vec3(tau, one, 0)
    ZB = Vec3(-tau, one, 0)
    ZC = Vec3(-tau, -one, 0)
    ZD = Vec3(tau, -one, 0)
    YA = Vec3(one, 0 , tau)
    YB = Vec3(one, 0 , -tau)
    YC = Vec3(-one, 0 , -tau)
    YD = Vec3(-one, 0 , tau)
    XA = Vec3(0 , tau, one)
    XB = Vec3(0 , -tau, one)
    XC = Vec3(0 , -tau, -one)
    XD = Vec3(0 , tau, -one)
    
    self.sommets = [ZA, ZB, ZC, ZD, YA, YB, YC, YD, XA, XB, XC, XD]
    iZA = 0;iZB = 1;iZC = 2;iZD = 3;iYA = 4;iYB = 5;iYC = 6;iYD = 7;iXA = 8;iXB = 9;iXC = 10;iXD = 11

    #Faces
    self.elements = []
    self.elements.append(Element("["+str(len(self.elements))+"]", iYA, iXA, iYD, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYA, iYD, iXB, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYB, iYC, iXD, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYB, iXC, iYC, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iZA, iYA, iZD, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iZA, iZD, iYB, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iZC, iYD, iZB, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iZC, iZB, iYC, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iXA, iZA, iXD, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iXA, iXD, iZB, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iXB, iXC, iZD, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iXB, iZC, iXC, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iXA, iYA, iZA, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iXD, iZA, iYB, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYA, iXB, iZD, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYB, iZD, iXC, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYD, iXA, iZB, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYC, iZB, iXD, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYD, iZC, iXB, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYC, iXC, iZC, self, 0, None))
    
  def fabriqueSol(self):
    """Randomise la surface du géoïde"""
    cpt=0.0
    totlen= len(self.sommets)
    for i in range(0, totlen):
      cpt+=1.0
      if general.configuration.getConfiguration("debug", "planete", "debug_genere_planete", "f", bool):
        if i%250==0:
          general.planete.afficheTexte("Perturbation de la surface... %(a)i/%(b)i", parametres={"a": i, "b": totlen}, type="construction")
      #On pousse chaque sommet aléatoirement
      rn = (random.random()-0.5)*self.delta + 1.0
      #On n'utilise pas self.changeCoordPoint car tout le modèle sera changé
      #donc pas besoin de tenter de deviner ce qui doit être recalculé
      self.sommets[i] = self.sommets[i] * rn
      
  def normaliseSol(self):
    """
    Étend la gamme des valeurs aléatoires pour les ramener dans l'échelle [1.0-delta;1.0+delta]
    """
    if general.configuration.getConfiguration("debug", "planete", "debug_genere_planete", "f", bool):
      general.planete.afficheTexte("Normalisation...", parametres={}, type="construction")
    A=self.sommets[0].length()
    B=A
    
    for sommet in self.sommets:
      A = min(A, sommet.length())
      B = max(B, sommet.length())
      
    C=1.0-self.delta
    D=1.0+self.delta
    
    facteur = (B-A)/(D-C)
    
    totlen= len(self.sommets)
    for i in range(0, len(self.sommets)):
      if general.configuration.getConfiguration("debug", "planete", "debug_genere_planete", "f", bool):
        if i%250==0:
          general.planete.afficheTexte("Normalisation... %(a)i/%(b)i", parametres={"a": i, "b": totlen}, type="construction")
      V=self.sommets[i].length()
      V=(V-A)/facteur+C
      som = Vec3(self.sommets[i])
      som.normalize()
      self.sommets[i] = som * V
      
  def flouifieSol(self, rayon):
    """
    Flou linéaire sur les sommets de la sphère
    """
    cpt=0.0
    totclefs=len(self.voisinage.keys())
    for sommet in self.voisinage.keys():
      if general.configuration.getConfiguration("debug", "planete", "debug_genere_planete", "f", bool):
        if cpt%250==0:
          general.planete.afficheTexte("Flouification... %(a)i/%(b)i", parametres={"a": cpt, "b": totclefs}, type="construction")
      cpt+=1.0
      old = self.sommets[sommet]
      
      voisins = []
      #On ajoute les voisins directes
      for element in self.voisinage[sommet]:
        if (not element in voisins) and element!=sommet:
          voisins.append(element)
      #Pour chaque voisin, on ajoute ses voisins rayon-1 fois
      for i in range(0, rayon-1):
        vsn = voisins[:]
        for s in vsn:
          for element in self.voisinage[s]:
            if (not element in voisins) and element!=sommet:
              voisins.append(element)
      
      tot = self.sommets[sommet].length()*4
      for id in voisins:
        tot += self.sommets[id].length()
      tot = tot / (len(voisins)+4)
      som = Vec3(self.sommets[sommet])
      som.normalize()
      self.sommets[sommet] = som *tot
      
  def fabriqueModel(self):
    """Produit un modèle 3D à partir du nuage des faces"""
    self.racine.detachNode()
    self.racineModel = NodePath("model")
    self.racineModel.reparentTo(self.racine)
    
    cpt=0.0
    totlen = len(self.elements)
    #Dessine les triangles
    for element in self.elements:
      cpt+=1.0
      if general.configuration.getConfiguration("debug", "planete", "debug_genere_planete", "f", bool):
        general.planete.afficheTexte("Création du modèle... %(a)i/%(b)i", parametres={"a": cpt, "b": totlen}, type="construction")
      #Ce sont les faces qui vont se charger de faire le modèle pour nous
      element.fabriqueModel()
    
      
    #On ajoute l'eau
    self.fabriqueEau()
    #On ajoute le ciel
    self.fabriqueCiel()
    
    general.cartographie.calculMiniMap((256, 128))
    
    if general.configuration.getConfiguration("affichage","general", "multitexturage","heightmap",str)=="heightmap":
      general.cartographie.calculHeightMap()
    if general.configuration.getConfiguration("affichage","general", "multitexturage","heightmap",str)!="flat":
      self.ajouteTextures()

    self.racine.reparentTo(render)
    if general.configuration.getConfiguration("Debug", "Planete", "debug_analyse_scene", "f", bool):
      self.racine.analyze()
      
    self.tectonique = Tectonique()

  vectricesEau = None
  @general.chrono
  def animEau(self, temps):
    """Animation de l'eau via manipulation des vectrices"""
    geomNodeCollection = self.modeleEau.findAllMatches('**/+GeomNode')

    if not self.vectricesEau:
      self.vectricesEau = {}
      for nodePath in geomNodeCollection:
        geomNode = nodePath.node()
        for i in range(geomNode.getNumGeoms()):
          geom = geomNode.modifyGeom(i)
          vdata = geom.modifyVertexData()

          vertex = GeomVertexRewriter(vdata, 'vertex')
          
          idx=0
          while not vertex.isAtEnd():
            if idx not in self.vectricesEau.keys():
              v=Vec3(*vertex.getData3f())
              v.normalize()
              self.vectricesEau[idx]=v
            vertex.setData3f(v[0], v[1], v[2])
            idx+=1
    
    for nodePath in geomNodeCollection:
      geomNode = nodePath.node()
      for i in range(geomNode.getNumGeoms()):
        geom = geomNode.modifyGeom(i)
        vdata = geom.modifyVertexData()

        vertex = GeomVertexRewriter(vdata, 'vertex')
        
        idx=0
        while not vertex.isAtEnd():
          v = self.vectricesEau[idx]
          v=v*self.ondulateur(v[0], v[1], v[2], temps)
          vertex.setData3f(v[0], v[1], v[2])
          idx+=1

  def ondulateur(self, x, y, z, temps):
    """Fonction qui calcule les vagues de l'animation de l'eau (mode par vectrice)"""
    longueurOnde = general.configuration.getConfiguration("affichage","effets", "animation-eau-longueuronde","0.005", float)
    tailleOnde = general.configuration.getConfiguration("affichage","effets", "animation-eau-tailleonde","0.0001", float)
    z=(math.sin(temps+x/longueurOnde)+math.sin(y+x)/longueurOnde)*math.cos(temps+z/longueurOnde)*tailleOnde/2
    return self.niveauEau+z 

  def fabriqueEau(self):
    """Ajoute une sphère qui représente l'eau"""
    
    if general.configuration.getConfiguration("debug", "planete", "debug_construction_sphere", "f", bool):
      return
      
    #Crée le modèle de l'eau
    self.modeleEau = loader.loadModel("data/modeles/sphere.egg")
    self.modeleEau.reparentTo(self.racine)
    self.modeleEau.setTransparency(TransparencyAttrib.MDual )
    
    if general.configuration.getConfiguration("affichage", "general", "type-eau", "texture", str)=="shader":
      self.modeleEau.setShader( loader.loadShader( 'data/shaders/water.sha' ) )
      tex = loader.loadTexture( 'data/textures/017eau.jpg' )
      self.modeleEau.setTexture( tex, 1 )
    else:
      self.modeleEau.setColor(0.0,0.0,0.0,0.5)
      tex = loader.loadTexture('data/textures/eau.jpg')
      self.modeleEau.setTexture(tex, 1)
        
    self.niveauEau = 1.0
    
    #Met à l'échelle la sphère de l'eau
    self.modeleEau.setScale(self.niveauEau)
    self.modeleEau.setPythonTag("type","eau")
    
    #On coupe la collision avec le ciel pour pas qu'on détecte de clics dans l'eau
    self.modeleEau.setCollideMask(BitMask32.allOff())
      
  def fabriqueCiel(self):
    """Ajoute une sphère qui représente l'eau"""
    
    if general.configuration.getConfiguration("debug", "planete", "debug_construction_sphere", "f", bool):
      return
      
    #Crée le modèle du ciel
    self.modeleCiel = NodePath("ciel")
    self.modeleCiel.reparentTo(self.racine)
    self.niveauCiel = 1.0+self.delta*1.25+0.0001
    
    if general.configuration.getConfiguration("planete", "nuages", "affiche-nuages", "t", bool):
      nuages = NodePath("nuage")
      densite = general.configuration.getConfiguration("planete", "nuages", "densite", "15", int)
      taille = general.configuration.getConfiguration("planete", "nuages", "taille", "0.15", float)
      quantite = general.configuration.getConfiguration("planete", "nuages", "quantite", "80", int)
      for i in range(0, quantite):
        a = sprite.Nuage(densite, taille)
        a.fabriqueModel().reparentTo(nuages)
        general.planete.spritesNonJoueur.append(a)
      nuages.reparentTo(self.modeleCiel)
      
    #Ciel bleu
    self.azure = loader.loadModel("data/modeles/sphere.egg")
    self.azure.setTransparency(TransparencyAttrib.MDual )
    self.azure.setColor(0.6, 0.6, 1.0, 1.0)
    self.azure.setTwoSided(True)
    self.azure.setScale((self.niveauCiel+0.001+0.0001))
    #self.azure.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
    self.azure.reparentTo(self.modeleCiel)
    #self.azure.setTexture("data/textures/EarthClearSky2.png", 1)
    self.azure.setBin('background', 2)
    self.azure.setDepthTest(False)
    self.azure.setDepthWrite(False)
    
    if general.configuration.getConfiguration("affichage","general", "multitexturage","heightmap",str)=="shader" or general.configuration.getConfiguration("affichage", "general", "type-eau", "texture", str)=="shader":
      self.azure.setShader( loader.loadShader( 'data/shaders/atmosphere.sha' ) )

    tex = loader.loadTexture( 'data/textures/EarthClearSky2.png' )
    self.azure.setTexture( tex, 1 )

    #Fabrique une lumière ambiante pour que la nuit soit moins noire
    if general.configuration.getConfiguration("affichage", "Effets", "typeEclairage","shader",str)=="flat":
      couleurNuit = general.configuration.getConfiguration("Planete", "Univers", "couleurNuit", "0.2 0.2 0.275 1.0", str)
      couleurNuit = VBase4(*general.floatise(couleurNuit.split(" ")))
      alight = AmbientLight('alight')
      alight.setColor(couleurNuit)
      alnp = self.racine.attachNewNode(alight)
      self.racine.setLight(alnp)
      #L'azure n'est pas affectée par la lumière ambiante
      self.azure.setLightOff(alnp)
    
    #Ciel orange
    #couchant = loader.loadModel("data/modeles/sphere.egg")
    #couchant.setTransparency(TransparencyAttrib.MDual )
    #couchant.setColor(1.0, 0.3, 0.1, 1.0)
    #couchant.setTwoSided(False)
    #couchant.setScale((self.niveauCiel+0.001+0.0005))
    #couchant.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
    #couchant.reparentTo(self.modeleCiel)    
    
    #Étoiles
    etoiles = loader.loadModel("data/modeles/sphere.egg")
    etoiles.setTransparency(TransparencyAttrib.MDual )
    tex = loader.loadTexture('data/textures/etoiles4.tif')
    #tex.setMagfilter(Texture.FTLinear)
    #tex.setMinfilter(Texture.FTLinearMipmapLinear)
    #etoiles.setTexGen(TextureStage.getDefault(), TexGenAttrib.MEyeSphereMap)
    etoiles.setTexture(tex, 1)
    etoiles.setTwoSided(False)
    etoiles.setScale(general.configuration.getConfiguration("planete", "Univers", "distanceSoleil","10.0",float)*3.0/2.0)
    etoiles.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
    etoiles.reparentTo(self.modeleCiel)    
    etoiles.setLightOff()
    etoiles.setBin('background', 1)
    etoiles.setDepthTest(False)
    etoiles.setDepthWrite(False)

    
    self.modeleCiel.setPythonTag("type","ciel")
    
    #On coupe la collision avec le ciel pour pas qu'on détecte de clics sur le ciel
    self.modeleCiel.setCollideMask(BitMask32.allOff())

  # Fin Constructions géométriques -------------------------------------
      
  # Import / Export ----------------------------------------------------
  def sauvegarde(self, fichier=None, tess=None):
    if tess==None:
      tess = self.tesselation
    nomFichier = fichier
      
    #On sauvegarde dans un fichier temporaire
    out = ""
    out += "parametres:tesselation:"+str(tess)+":\r\n"
    out += "parametres:delta:"+str(self.delta)+":\r\n"
    out += "parametres:niveauEau:"+str(self.niveauEau)+":\r\n"
    out += "parametres:niveauCiel:"+str(self.niveauCiel)+":\r\n"
    for point in self.sommets:
      out += "sommet:"+str(point[0])+":"+str(point[1])+":"+str(point[2])+":\r\n"
    for element in self.elements:
      out += element.sauvegarde()
      
    if nomFichier!=None:
      fichier = open(os.path.join(".", "data", "cache", "save.tmp"), "w")
      fichier.write(out)
      fichier.close()
    
      #On zip le fichier temporaire
      zip = zipfile.ZipFile(nomFichier, "w")
      zip.write(os.path.join(".", "data", "cache", "save.tmp"), os.path.basename(nomFichier), zipfile.ZIP_DEFLATED)
      zip.close()
      #On enlève le fichier temporaire
      os.remove(os.path.join(".", "data", "cache", "save.tmp"))
    else:
      return out
      
  def __repr__(self):
    return self.sauvegarde()
    
  _repr = None
  def _syncCheck(self):
    if self._repr == None:
      self._repr = self.__repr__()
    return self._repr
    
  def charge(self, fichier, simple=False):
    """Charge le géoïde depuis un fichier"""
    self.detruit()
    self.sommets = []
    self.faces = []
    self.lignes = []
    self.sommetDansFace = {}
    self.voisinage = {}
    self.racine = render.attachNewNode("planete")

    if not isinstance(fichier, list):
      #Lecture depuis le zip
      zip = zipfile.ZipFile(fichier, "r")
      if zip.testzip()!=None:
        print "PLANETE :: Charge :: Erreur : Fichier de sauvegarde corrompu !"
      data = zip.read(os.path.basename(fichier))
      zip.close()
      lignes = data.split("\r\n")
    else:
      lignes = fichier

    tot = len(lignes)
    inconnu = []
    for i in range(0, tot):
      if general.configuration.getConfiguration("debug", "planete", "debug_charge_planete", "f", bool):
        if i%500==0:
          general.planete.afficheTexte("Parsage des infos... %(a)i/%(b)i", parametres={"a": i, "b": tot}, type="sauvegarde")
      ligne = lignes[i]
        
      elements = ligne.strip().lower().split(":")
      type = elements[0]
      elements = elements[1:]
      if type=="parametres":
        if elements[0]=="tesselation":
          #Attrapage des infos de tesselation
          self.tesselation = int(elements[1])
        elif elements[0]=="delta":
          #Attrapage des infos de delta
          self.delta = float(elements[1])
        elif elements[0]=="niveaueau":
          #Attrapage des infos de niveauEau
          self.niveauEau = float(elements[1])
        elif elements[0]=="niveauciel":
          #Attrapage des infos de niveauCiel
          if elements[1]=="none":
            self.niveauCiel = 2.0
          else:
            self.niveauCiel = float(elements[1])
        else:
          inconnu.append(ligne)
      elif type=="sommet":
        #Création d'un sommet
        self.sommets.append(Vec3(float(elements[0]), float(elements[1]), float(elements[2])))
      elif type=="element":
        #Création d'une face
        ids = elements[0].replace("[","").split("]")
        if len(ids)<2:
          print
          print "Erreur ID", ids
        elif len(ids)==2:
          self.elements.append(Element("["+str(ids[0])+"]", int(elements[1]), int(elements[2]), int(elements[3]), self, 0, None))
        else:
          self.elements[int(ids[0])].charge(ids[1:], elements[1], elements[2], elements[3])
      elif ligne.strip()!="":
        inconnu.append(ligne)
        
    if not simple:
      self.fabriqueVoisinage()
      
      #On ajoute le gestionnaire d'intelligence artificielle
      general.planete.aiNavigation.grapheDeplacement()
    return inconnu
  # Fin Import / Export ------------------------------------------------
      
  lastPing = None
  @general.chrono
  def pingGeoide(self, task):
    """Fonction appelée a chaque image, temps indique le temps écoulé depuis l'image précédente"""
    if self.lastPing==None:
      self.lastPing = task.time-1.0/60
    temps = task.time - self.lastPing
    self.lastPing = task.time
    
    if general.configuration.getConfiguration("affichage","effets", "animation-eau","t", bool):
      if self.modeleEau!=None:
        self.animEau(task.time)
        
    """rnd = random.choice(range(0, len(self.sommets)))
    self.montagne(rnd, 2, self.delta/10)
    rnd = random.choice(range(0, len(self.sommets)))
    self.montagne(rnd, 2, -self.delta/10)"""
    
    #if self.azure != None:
    #  if general.planete.soleil!=None:
    #    self.azure.lookAt(general.planete.soleil)
    
    if general.configuration.getConfiguration("affichage","minimap","affichesoleil","t", bool):
      #Met à jour la carte du soleil
      self.lastMAJPosSoleil += temps
      if self.lastMAJPosSoleil > self.dureeMAJPosSoleil:
        self.lastMAJPosSoleil=0.0
        general.cartographie.calculZoneOmbre((256, 128))
        
    if general.configuration.getConfiguration("planete","Regles","tectonique","t", bool):
      self.tectonique.pingTectonique(temps)
    
    if not self.fini:
      return task.cont
    else:
      return task.done
  # Fin Mise à jour ----------------------------------------------------
        
  # Fonctions diverses -------------------------------------------------
  def trouveSommet(self, point, tiensCompteDeLAngle=False, angleSolMax=None):
    """
    Retourne le sommet le plus proche
    point : le point à rechercher
    """
    if angleSolMax==None:
      angleSolMax = general.planete.aiNavigation.angleSolMax
      
    dst = (self.sommets[0]-point).lengthSquared()
    id = 0
    for s in self.sommets:
      d = (s-point).lengthSquared()
      if dst > d:
        #On fait attention à pouvoir aller à ce point là
        if not tiensCompteDeLAngle:
          id = self.sommets.index(s)
          dst = d
        elif general.planete.aiNavigation.anglePassage(point, s, False)<angleSolMax:
          id = self.sommets.index(s)
          dst = d
    return id
    
  def trouveFace(self, point, sub=None):
    """
    Retourne la face dans laquelle le point se trouve
    point : le point à rechercher
    sub : la liste des faces à parcourir (utiliser None dans le doute)
    """
    general.TODO("Utiliser testIntersectionTriangleDroite pour plus de rapidité (voir #B#)")
    ## ------------ Version avec self.sommetDansFace
    sommetProche = self.trouveSommet(point)
    faces = self.sommetDansFace[sommetProche]
    cible = Vec3(point)
    cible.normalize()
    
    #On initialise a des valeurs stupides
    f = None
    d1, d2, d3 = 10, 10, 10
    for face in faces:
      tri = face.sommets
      #On fait des comparaisons, pas du travail sur des valeurs exactes, donc on utilise le carré pour gagner le temps du sqrt
      da = Vec3(self.sommets[tri[0]])
      da.normalize()
      db = Vec3(self.sommets[tri[1]])
      db.normalize()
      dc = Vec3(self.sommets[tri[2]])
      dc.normalize()
      
      da = (cible - da).lengthSquared()
      db = (cible - db).lengthSquared()
      dc = (cible - dc).lengthSquared()
      
      #Si on a une plus proche, elle remplace la meilleure
      if math.sqrt(da*da+db*db+dc*dc) < math.sqrt(d1*d1+d2*d2+d3*d3):
        d1, d2, d3 = da, db, dc
        f = face
    return f
    ## ------------ Version avec self.sommetDansFace
        
    ## ------------ Version avec self.elements
    #Si on a pas de liste de faces, on utilise la liste complète de la planète
    if sub==None:
      sub = self.elements
    cible = Vec3(point)
    cible.normalize()
    
    #On initialise a des valeurs stupides
    f = None
    d1, d2, d3 = 10, 10, 10
    
    #On teste toutes les facettes de l'ensemble
    for tria in sub:
      tri = tria.sommets
      #On fait des comparaisons, pas du travail sur des valeurs exactes, donc on utilise le carré pour gagner le temps du sqrt
      da = Vec3(self.sommets[tri[0]])
      da.normalize()
      db = Vec3(self.sommets[tri[1]])
      db.normalize()
      dc = Vec3(self.sommets[tri[2]])
      dc.normalize()
      
      da = (cible - da).lenghSquared()
      db = (cible - db).lenghSquared()
      dc = (cible - dc).lenghSquared()
      
      #Si on a une plus proche, elle remplace la meilleure
      if math.sqrt(da*da+db*db+dc*dc) < math.sqrt(d1*d1+d2*d2+d3*d3):
        d1, d2, d3 = da, db, dc
        f = tria
        
    #Si la face que l'on trouvé a été subdivisée
    if f.enfants!=None:
      #On recherche dans ses enfants
      return self.trouveFace(point, f.enfants)
    return f
    ## ------------ Version avec self.elements
    
    ## ------------ Version avec testIntersectionTriangleDroite
    #Si on a pas de liste de faces, on utilise la liste complète de la planète
    if sub==None:
      sub = self.elements
    cible = Vec3(point)
    cible.normalize()
    cible = cible * 100
    
    #On initialise a des valeurs stupides
    f = None
    d1, d2, d3 = 10000, 10000, 10000
    
    #On teste toutes les facettes de l'ensemble
    for tria in sub:
      tri = tria.sommets
      if general.testIntersectionTriangleDroite(self.sommets[tri[0]], self.sommets[tri[1]], self.sommets[tri[2]], cible, (0.0,0.0,0.0)):
        #Si la face que l'on trouvé a été subdivisée
        if tria.enfants!=None:
          #On recherche dans ses enfants
          return self.trouveFace(point, tria.enfants)
        else:
          return tria
    return None
    ## ------------ Version avec testIntersectionTriangleDroite
    
  def altitudeCarre(self, point):
    """Retourne l'altitude (rayon) à laquelle le point devrait se trouver pour être juste sur la face en dessous (au dessus) de lui (coord cartésiennes)"""
    #Cherche la face dans laquelle se trouve le point
    face = self.trouveFace(point).sommets
    if face==None:
      #La droite passant par un point quelconque et le centre de la sphère coupe obligatoirement la dite sphère en un point
      #Ne pas avoir de résultat dit que ça bug
      print "Bug :: testIntersectionTriangleDroite déconne"
      return point.length()
    pt1, pt2, pt3 = self.sommets[face[0]], self.sommets[face[1]], self.sommets[face[2]]
    d1 = pt1.lengthSquared()
    d2 = pt2.lengthSquared()
    d3 = pt3.lengthSquared()
    return general.lerp(pt1, d1, pt2, d2, pt3, d3, point)
    
  def altitude(self, point):
    return math.sqrt(self.altitudeCarre(point))

  def placeSurSol(self, point):
    """Déplace le point pour qu'il soit juste sur la surface de la facette (coord cartésiennes)"""
    point = Vec3(point)
    point.normalize()
    return point * self.altitude(point)

  def changeCoordPoint(self, oldCoord, newCoord, MAJ=True):
    """
    Change les coordonnées du point connu par ses anciennes coordonnées vers de nouvelles coordonnées
    Met à jour la géométrie qui en a besoin
    """
    if self.sommets.count(oldCoord)<1:
      print "Erreur planete::changeCoordPoint,",oldCoord,"ce sommet n'existe pas"
      raw_input()
    idx = self.sommets.index(oldCoord)
    self.sommets[idx] = Vec3(*general.floatise(newCoord))
    self.modifieVertex(idx, MAJ=MAJ)
    
    elements = self.sommetDansFace[idx]
        
    for element in elements:
      element.normale = None #On a bougé un point, donc sa normale a changée
      
    if MAJ:
      general.planete.aiNavigation.majGraphNavigation(idx)
    
  def montagne(self, idxSommetCentre, rayon, delta):
    delta = delta/10
    voisins = []
    deltas = {}
    
    #On ajoute les voisins directes
    for element in self.voisinage[idxSommetCentre]:
      if (not element in voisins):
        voisins.append(element)
        deltas[element]=deltas.get(element, 0.0)+delta
    for i in range(0, rayon):
      for idx in voisins[:]:
        for element in self.voisinage[idx]:
          if (not element in voisins):
            voisins.append(element)
            deltas[element]=deltas.get(element, 0.0)+delta*(float(i)/rayon)*(float(i)/rayon)
    for sommet in deltas:
      delta=deltas[sommet]
      self.elevePoint(sommet, delta, MAJ=False)
    for sommet in deltas:
      general.planete.aiNavigation.majGraphNavigation(idx)
      
  def elevePoint(self, idx, delta):
    """Déplace le sommet d'indice idx de delta unité et met à jour la géométrie qui en a besoin"""
    norme = self.sommets[idx].length()
    tmp = Vec3(self.sommets[idx])
    tmp.normalize()
    tmp = tmp * (norme + delta)
    self.changeCoordPoint(self.sommets[idx], tmp)
    
  # Fin Fonctions diverses ---------------------------------------------
  
  vdata = None
  def ajouteVerteces(self, vdata, vWriter, nWriter, tWriter, cWriter):
    self.vdata = vdata
    cpt = 0
    for sommet in self.sommets:
      if cpt%250==0:
        general.planete.afficheTexte("Création des vectrices : %(a).2f%%", parametres={"a":(cpt*1.0)/len(self.sommets)*100}, type="construction")
      cpt+=1
      self.ajouteVertex(sommet, self.vdata, vWriter, nWriter, tWriter, cWriter)
      
  def ajouteVertex(self, p, vdata, vWriter, nWriter, tWriter, cWriter):
    #On attrape les couleurs pour chaque sommet
    c1,t1,h1=self.elements[0].couleurSommet(p)

    #On calcule les normales à chaque sommet
    n1=self.sommetDansFace[self.sommets.index(p)][0].calculNormale(p)
    
    if general.configuration.getConfiguration("affichage","general", "multitexturage","heightmap", str)=="heightmap":
      ci1 = general.cartographie.point3DVersCarte(p, (1.0, 1.0), coordonneesTexturage=True)
    else:
      ci1 = general.cartographie.point3DVersCarte(p, (general.configuration.getConfiguration("affichage","general", "repetition-texture","17.0", float), general.configuration.getConfiguration("affichage","general", "repetition-texture", "17.0", float)), coordonneesTexturage=True)
    
    if general.configuration.getConfiguration("affichage","general", "multitexturage","heightmap", str)=="shader":
      minAlt = (1.0-self.delta)
      maxAlt = (1.0+self.delta)
      altitude = p.length()
      c1 = ((altitude-minAlt)/(maxAlt-minAlt), 0.0, 0.0, 0.0)
    elif general.configuration.getConfiguration("affichage","general", "multitexturage","heightmap", str)=="heightmap":
      c1 = (1.0, 1.0, 1.0, 1.0)
    
    #On écrit le modèle dans cet ordre :
    #-vectrice
    #-normale
    #-texture | couleur
    vWriter.addData3f(p)
    nWriter.addData3f(n1)
    tWriter.addData2f(ci1)
    cWriter.addData4f(*c1)
      
  def modifieVertex(self, indice, MAJ=True):
    if self.vdata == None:
      return
    #self._repr = self.__repr__()
    #On bouge le point
    vWriter = GeomVertexWriter(self.vdata, 'vertex')
    vWriter.setRow(indice)
    vWriter.setData3f(self.sommets[indice])
    
    #On recalcul sa normale
    nWriter = GeomVertexWriter(self.vdata, 'normal')
    nWriter.setRow(indice)
    nWriter.setData3f(self.sommetDansFace[indice][0].calculNormale(self.sommets[indice]))
    
    c1=self.elements[0].couleurSommet(self.sommets[indice])[0]
    if general.configuration.getConfiguration("affichage","general", "multitexturage","heightmap", str)=="shader":
      minAlt = (1.0-self.delta)
      maxAlt = (1.0+self.delta)
      altitude = max(min(self.sommets[indice].length(), maxAlt), minAlt)
      c1 = ((altitude-minAlt)/(maxAlt-minAlt), 0.0, 0.0, 0.0)
    elif general.configuration.getConfiguration("affichage","general", "multitexturage","heightmap", str)=="heightmap":
      c1 = (1.0, 1.0, 1.0, 1.0)

    print c1
    #On change sa couleur
    cWriter = GeomVertexWriter(self.vdata, 'color')
    cWriter.setRow(indice)
    cWriter.setData4f(c1)
      
    #On met à jour la minimap
    if MAJ:
      general.cartographie.calculMiniMap((256, 128),self.sommetDansFace[indice])
      
  def ajouteTextures(self):
    general.TODO("Finir le texturage via heightmap")
    
    if general.configuration.getConfiguration("affichage", "general", "multitexturage", "heightmap", str)=="shader":
      tex0 = loader.loadTexture( 'data/textures/sable.png' )
      tex0.setMinfilter( Texture.FTLinearMipmapLinear )
      tex0.setMagfilter( Texture.FTLinearMipmapLinear )
      tex1 = loader.loadTexture( 'data/textures/herbe.png' )
      tex1.setMinfilter( Texture.FTLinearMipmapLinear )
      tex1.setMagfilter( Texture.FTLinearMipmapLinear )
      tex2 = loader.loadTexture( 'data/textures/neige.png' )
      tex2.setMinfilter( Texture.FTLinearMipmapLinear )
      tex2.setMagfilter( Texture.FTLinearMipmapLinear )
      
      ts0 = TextureStage( 'sable' )
      ts1 = TextureStage( 'herbe' )
      ts2 = TextureStage( 'neige' )

      self.racineModel.setTexture( ts0, tex0, 15 )
      self.racineModel.setTexture( ts1, tex1, 20 )
      self.racineModel.setTexture( ts2, tex2, 35 )
      self.racineModel.setTag( 'Normal', 'True' )
      self.racineModel.setTag( 'Clipped', 'True' )
      self.racineModel.setTexScale(ts0, 256, 256)
      self.racineModel.setTexScale(ts1, 256, 256)
      self.racineModel.setTexScale(ts2, 256, 256)
      
    elif general.configuration.getConfiguration("affichage", "general", "multitexturage", "heightmap", str)=="flat":
      tex = loader.loadTexture("data/textures/herbe.png")
      self.racineModel.setTexture(tex, 1)
    
    elif general.configuration.getConfiguration("affichage", "general", "multitexturage", "heightmap", str)=="heightmap":
      root = self.racineModel
      root.setLightOff()

      # Stage 1: alpha maps
      ts = TextureStage("stage-alphamaps")
      ts.setSort(00)
      ts.setPriority(1)
      ts.setMode(TextureStage.MReplace)
      ts.setSavedResult(True)
      root.setTexture(ts, loader.loadTexture("data/cache/zoneherbe.png", "data/cache/zoneneige.png"))

      # Stage 2: the first texture
      ts = TextureStage("stage-first")
      ts.setSort(10)
      ts.setPriority(1)
      ts.setMode(TextureStage.MReplace)
      root.setTexture(ts, loader.loadTexture("data/textures/sable.png"))
      root.setTexScale(ts, 17, 17)

      # Stage 3: the second texture
      ts = TextureStage("stage-second")
      ts.setSort(20)
      ts.setPriority(1)
      ts.setCombineRgb(TextureStage.CMInterpolate, TextureStage.CSTexture, TextureStage.COSrcColor,
                                                   TextureStage.CSPrevious, TextureStage.COSrcColor,
                                                   TextureStage.CSLastSavedResult, TextureStage.COSrcColor)
      root.setTexture(ts, loader.loadTexture("data/textures/herbe.png"))
      root.setTexScale(ts, 17, 17)

      # Stage 4: the third texture
      ts = TextureStage("stage-third")
      ts.setSort(30)
      ts.setPriority(0)
      ts.setCombineRgb(TextureStage.CMInterpolate, TextureStage.CSTexture, TextureStage.COSrcColor,
                                                   TextureStage.CSPrevious, TextureStage.COSrcColor,
                                                   TextureStage.CSLastSavedResult, TextureStage.COSrcAlpha)
      root.setTexture(ts, loader.loadTexture("data/textures/neige.png"))
      root.setTexScale(ts, 17, 17)

