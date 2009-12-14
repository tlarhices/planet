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

from element import *
from ai import *
from sprite import *
from joueur import *

#from pandac.PandaModules import *

class Planete:
  tesselation = None #Le niveau de subdivision que l'on souhaite obtenir
  delta = None #Le degré de perturbation maximal de la surface par rapport à 0
  
  sommets = None #La liste des sommets
  elements = None #La liste des faces (indices des sommets)
  racine = None #Point (0,0,0) de la planète selon lequel tout est ajouté
  
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
  
  aiNavigation = None #Le bout d'AI qui contient le graphe de navigation qui est commun a toute entité de la planète
  sprites = None #La liste des objets du monde dérivant de la classe sprite
  joueurs = None
  
  #Paramètres éclairage
  soleil=None #Noeud du soleil (une caméra dans le cas de la projection d'ombre)
  flare = None #Le lens flare
  distanceSoleil = None #Distance du soleil à la planète
  vitesseSoleil = None #Vitesse de rotation du soleil en pifometre/s
  angleSoleil = None
  lastMAJPosSoleil=100000.0 #Le temps depuis lequel on n'a pas remis à jour la carte du soleil
  dureeMAJPosSoleil=23.0 #Le temps que l'on attends avant de recalculer la carte du soleil
  lastSave = 1000
  seuilSauvegardeAuto = 600 #Sauvegarde auto toutes les 10 minutes

  
  # Initialisation -----------------------------------------------------
  def __init__(self):
    """Constructeur, initialise les tableaux"""
    self.sommets = [] #Pas de sommets
    self.elements = [] #Pas de faces
    self.sprites = [] #Pas d'objets sur la planète
    self.joueurs = []
    self.voisinage = {} #Pas de sommet, donc pas de voisinage
    self.sommetDansFace = {} #Pas de faces, donc pas d'association
    self.survol = None #Le curseur n'est au dessus de rien par défaut
    
    self.distanceSoleil = float(general.configuration.getConfiguration("planete", "Univers", "distanceSoleil","10.0"))
    self.vitesseSoleil = float(general.configuration.getConfiguration("planete", "Univers", "vitesseSoleil","1.0"))
    self.angleSoleil = 0.0
    self.dureeMAJPosSoleil = float(general.configuration.getConfiguration("affichage", "Minimap", "dureeMAJPosSoleil","23.0"))
    self.seuilSauvegardeAuto = float(general.configuration.getConfiguration("affichage", "General", "seuilSauvegardeAuto","600.0"))
    
    general.WIREFRAME = general.configuration.getConfiguration("affichage", "general", "fildefer","f")=="t"
    general.TEXTURES = general.configuration.getConfiguration("affichage", "general", "utilise-textures","t")=="t"
    
  def fabriqueVoisinage(self):
    """
    Remplit le dictionnaire self.voisinage de la façon suivante :
    self.voisinage[a]=[b, c, d, e, ...]
    avec a, b, c, d, e les indices des sommets et de telle sorte qu'il y ai une arrête ab, ac, ad, ae, ...
    """
    general.startChrono("Planete::fabriqueVoisinage")
    self.voisinage = {}
    totSommets = len(self.sommets)
    for sommet in range(0, totSommets):
      if general.DEBUG_GENERE_PLANETE:
        if sommet%250==0:
          self.afficheTexte("Calcul du voisinage... %i/%i" %(sommet, totSommets))
      faces = self.sommetDansFace[sommet]
      for face in faces:
        if face.enfants == None: #On ne considère que les faces les plus subdivisées
          self.ajouteNoeud(sommet, face.sommets[0])
          self.ajouteNoeud(sommet, face.sommets[1])
          self.ajouteNoeud(sommet, face.sommets[2])
    general.stopChrono("Planete::fabriqueVoisinage")
        
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
    self.sommets=[]
    self.lignes=[]
    for element in self.elements:
      element.detruit()
    if self.racine!=None:
      self.racine.detachNode()
      self.racine.removeNode()
    for joueur in self.joueurs:
      joueur.detruit()
    for sprite in self.sprites:
      sprite.tue("destruction de la planète")
    self.sprites = []
    self.joueurs = []
  # Fin Initialisation -------------------------------------------------
    
  def afficheTexte(self, texte, type=None):
    """Affiche le texte sur l'écran, si texte==None, alors efface le dernier texte affiché"""
    general.gui.afficheTexte(texte, type, True)
    
  # Constructions géométriques -----------------------------------------
  def fabriqueNouvellePlanete(self, tesselation, delta):
    """
    Construit une nouvelle planète :
    tesselation : Le nombre de subdivision que l'on souhaite faire
    delta : Le niveau maximal de perturbation de la surface que l'on souhaite
    """
    general.startChrono("Planete::fabriqueNouvellePlanete")
    self.niveauEau = 1.0 #La planète a un rayon de 1.0 en dessous de son noeud, on place l'eau juste a sa surface
    self.sommets = [] #Pas de sommets
    self.elements = [] #Pas de faces
    self.sprites = [] #Pas d'objets sur la planète
    self.joueurs = [] 
    self.voisinage = {} #Pas de sommet, donc pas de voisinage
    self.sommetDansFace = {} #Pas de faces, donc pas d'association
    self.angleSoleil = 0.0
    
    #Permet d'être sûr que ce sont bien des valeurs valides
    self.delta = float(delta)
    self.tesselation = int(tesselation)
    
    #On regarde si on a pas déjà calculé une sphère a ce niveau de tesselation
    if os.path.isfile(os.path.join(".","data","pre-tesselate",str(tesselation))):
      #On charge la sphere pre-tesselée
      self.charge(os.path.join(".","data","pre-tesselate",str(tesselation)), simple=True)
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
        
      #On remet le niveau de tesselation qu'il faut, le chargement aura tout pété
      self.tesselation = int(tesselation)
      self.delta = float(delta)

      #On tesselate la sphère courante
      for i in range(last, self.tesselation):
        cpt=0.0
        tot=len(self.elements)
        for element in self.elements:
          cpt+=1
          if general.DEBUG_GENERE_PLANETE:
            self.afficheTexte("Tesselation en cours... %i/%i::%i/%i" %(i+1, self.tesselation, cpt, tot))
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
    self.flouifieSol(3)
    
    #On étend la gamme d'altitudes
    self.normaliseSol()
    
    #On calcule la navigation pour l'intelligence artificielle
    self.aiNavigation = AINavigation(self)
    self.aiNavigation.grapheDeplacement()
    
    general.stopChrono("Planete::fabriqueNouvellePlanete")
    
  def fabriqueSphere(self):
    self.fabriqueSphereIcosahedre()
    
  def fabriqueSphereOctahedre(self):
    """fabrique un octahèdre régulier de rayon 1.0"""
    general.startChrono("Planete::fabriqueSphere")
    XP = Vec3(1.0,0.0,0.0)
    XM = Vec3(-1.0,0.0,0.0)
    YP = Vec3(0.0,1.0,0.0)
    YM = Vec3(0.0,-1.0,0.0)
    ZP = Vec3(0.0,0.0,1.0)
    ZM = Vec3(0.0,0.0,-1.0)
    
    self.sommets = [XP, XM, YP, YM, ZP, ZM]
    iXP = 0;iXM = 1;iYP = 2;iYM = 3;iZP = 4;iZM = 5
    self.elements = []
    self.elements.append(Element("["+str(len(self.elements))+"]", iXP, iZP, iYP, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYP, iZP, iXM, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iXM, iZP, iYM, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYM, iZP, iXP, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iXP, iYP, iZM, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYP, iXM, iZM, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iXM, iYM, iZM, self, 0, None))
    self.elements.append(Element("["+str(len(self.elements))+"]", iYM, iXP, iZM, self, 0, None))
    general.stopChrono("Planete::fabriqueSphere")
    
  def fabriqueSphereIcosahedre2(self):
    general.startChrono("Planete::fabriqueSphere")
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
    general.stopChrono("Planete::fabriqueSphere")
    
  def fabriqueSphereIcosahedre(self):
    """fabrique un icosahèdre régulier de rayon 1.0"""
    general.startChrono("Planete::fabriqueSphere")
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
    
    general.stopChrono("Planete::fabriqueSphere")
    
  def fabriqueSol(self):
    """Randomise la surface du géoïde"""
    general.startChrono("Planete::fabriqueSol")
    cpt=0.0
    totlen= len(self.sommets)
    for i in range(0, totlen):
      cpt+=1.0
      if general.DEBUG_GENERE_PLANETE:
        if i%250==0:
          self.afficheTexte("Perturbation de la surface... %i/%i" %(i, totlen))
      #On pousse chaque sommet aléatoirement
      rn = (random.random()-0.5)*self.delta + 1.0
      #On n'utilise pas self.changeCoordPoint car tout le modèle sera changé
      #donc pas besoin de tenter de deviner ce qui doit être recalculé
      self.sommets[i] = self.sommets[i] * rn
        
    general.stopChrono("Planete::fabriqueSol")
      
  def normaliseSol(self):
    """
    Étend la gamme des valeurs aléatoires pour les ramener dans l'échelle [1.0-delta;1.0+delta]
    """
    general.startChrono("Planete::normaliseSol")
    
    if general.DEBUG_GENERE_PLANETE:
      self.afficheTexte("Normalisation...")
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
      if general.DEBUG_GENERE_PLANETE:
        if i%250==0:
          self.afficheTexte("Normalisation... %i/%i" %(i, totlen))
      V=self.sommets[i].length()
      V=(V-A)/facteur+C
      som = Vec3(self.sommets[i])
      som.normalize()
      self.sommets[i] = som * V
      
    general.stopChrono("Planete::normaliseSol")
      
  def flouifieSol(self, rayon):
    """
    Flou gaussien sur les sommets de la sphère
    """
    
    general.startChrono("Planete::flouifieSol")
    cpt=0.0
    totclefs=len(self.voisinage.keys())
    for sommet in self.voisinage.keys():
      if general.DEBUG_GENERE_PLANETE:
        if cpt%250==0:
          self.afficheTexte("Flouification... %i/%i" %(cpt, totclefs))
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
    general.stopChrono("Planete::flouifieSol")
      
  def fabriqueModel(self):
    """Produit un modèle 3D à partir du nuage des faces"""
    general.startChrono("Planete::fabriqueModel")
    
    #Création du cache de texture si nécessaire
    if general.configuration.getConfiguration("affichage", "general", "force-cache-texture","t")=="t":
      element = Element("", 0, 0, 0, self, 0, None)
      totTex = len(element.texturesValides)*len(element.texturesValides)*len(element.texturesValides)
      cpt=0
      for t1 in element.texturesValides:
        for t2 in element.texturesValides:
          for t3 in element.texturesValides:
            cpt+=1
            if cpt%20==0:
              self.afficheTexte("Création du cache de textures : %.2f%%" %((cpt*1.0)/totTex*100))
            clef = t1+"-"+t2+"-"+t3
            if not clef+".png" in os.listdir(os.path.join(".","data","cache")):
              element.textureMixer(t1, t2, t3)
              del element.textures[clef]
    self.racine.setScale(0.01)
    cpt=0.0
    totlen = len(self.elements)
    #Dessine les triangles
    for element in self.elements:
      cpt+=1.0
      if general.DEBUG_GENERE_PLANETE:
        self.afficheTexte("Création du modèle... %i/%i" %(cpt, totlen))
      #Ce sont les faces qui vont se charger de faire le modèle pour nous
      element.fabriqueModel()
    
    self.racine.setScale(1.0)  
      
    #On ajoute l'eau
    self.fabriqueEau()
    #On ajoute le ciel
    self.fabriqueCiel()
    
    self.racine.analyze()
    general.stopChrono("Planete::fabriqueModel")

  def fabriqueEau(self):
    """Ajoute une sphère qui représente l'eau"""
    
    if general.DEBUG_CONSTRUCTION_SPHERE:
      return
      
    general.startChrono("Planete::fabriqueEau")
    
    #Crée le modèle de l'eau
    self.modeleEau = loader.loadModel("data/modeles/sphere.egg")
    self.modeleEau.reparentTo(self.racine)
    self.modeleEau.setTransparency(TransparencyAttrib.MAlpha )
    self.modeleEau.setColor(0.0,0.0,0.0,0.5)
    tex = loader.loadTexture('data/textures/eau.jpg')
    self.modeleEau.setTexture(tex, 1)
        
    self.niveauEau = 1.0
    
    #Met à l'échelle la sphère de l'eau
    self.modeleEau.setScale(self.niveauEau)
    self.modeleEau.setPythonTag("type","eau")
    
    #On coupe la collision avec le ciel pour pas qu'on détecte de clics dans l'eau
    self.modeleEau.setCollideMask(BitMask32.allOff())
    general.stopChrono("Planete::fabriqueEau")
      
  def fabriqueCiel(self):
    """Ajoute une sphère qui représente l'eau"""
    
    if general.DEBUG_CONSTRUCTION_SPHERE:
      return
      
    general.startChrono("Planete::fabriqueCiel")
    
    #Crée le modèle du ciel
    self.modeleCiel = NodePath("ciel")
    self.modeleCiel.reparentTo(self.racine)
    self.niveauCiel = 1.0+self.delta*1.25+0.0001
    
    if general.configuration.getConfiguration("planete", "nuages", "affiche-nuages", "t")=="t":
      nuages = NodePath("nuage")
      densite = int(general.configuration.getConfiguration("planete", "nuages", "densite", "15"))
      taille = float(general.configuration.getConfiguration("planete", "nuages", "taille", "0.15"))
      quantite = int(general.configuration.getConfiguration("planete", "nuages", "quantite", "80"))
      for i in range(0, quantite):
        a = Nuage(densite, taille, self)
        a.fabriqueModel().reparentTo(nuages)
        self.sprites.append(a)
      nuages.reparentTo(self.modeleCiel)
      
    #Ciel bleu
    self.azure = loader.loadModel("data/modeles/sphere.egg")
    self.azure.setTransparency(TransparencyAttrib.MDual )
    self.azure.setColor(0.6, 0.6, 1.0, 1.0)
    self.azure.setTwoSided(False)
    self.azure.setScale((self.niveauCiel+0.001+0.0001))
    self.azure.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
    self.azure.reparentTo(self.modeleCiel)
    self.azure.setTexture("data/textures/EarthClearSky2.png", 1)
    self.azure.setBin('background', 2)
    self.azure.setDepthTest(False)
    self.azure.setDepthWrite(False)

    #Fabrique une lumière ambiante pour que la nuit soit moins noire
    if general.configuration.getConfiguration("affichage", "Effets", "typeEclairage","shader")=="flat":
      couleurNuit = general.configuration.getConfiguration("Planete", "Univers", "couleurNuit", "0.2 0.2 0.275 1.0")
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
    etoiles.setScale(self.distanceSoleil*3.0/2.0)
    etoiles.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
    etoiles.reparentTo(self.modeleCiel)    
    etoiles.setLightOff()
    etoiles.setBin('background', 1)
    etoiles.setDepthTest(False)
    etoiles.setDepthWrite(False)

    
    self.modeleCiel.setPythonTag("type","ciel")
    
    #On coupe la collision avec le ciel pour pas qu'on détecte de clics sur le ciel
    self.modeleCiel.setCollideMask(BitMask32.allOff())
    general.stopChrono("Planete::fabriqueCiel")

  # Fin Constructions géométriques -------------------------------------
      
  # Import / Export ----------------------------------------------------
  def sauvegarde(self, fichier, tess=None):
    general.startChrono("Planete::sauvegarde")
    self.afficheTexte("Sauvegarde en cours...", "sauvegarde")
    
    """Sauvegarde le géoïde dans un fichier"""
    if tess==None:
      tess = self.tesselation
    nomFichier = fichier
      
    #On sauvegarde dans un fichier temporaire
    fichier = open(os.path.join(".", "data", "cache", "save.tmp"), "w")
    fichier.write("O:tesselation:"+str(tess)+":\r\n")
    fichier.write("O:delta:"+str(self.delta)+":\r\n")
    fichier.write("O:distanceSoleil:"+str(self.distanceSoleil)+":\r\n")
    fichier.write("O:niveauEau:"+str(self.niveauEau)+":\r\n")
    fichier.write("O:niveauCiel:"+str(self.niveauCiel)+":\r\n")
    fichier.write("O:angleSoleil:"+str(self.angleSoleil)+":\r\n")
    for point in self.sommets:
      fichier.write("P:"+str(point[0])+":"+str(point[1])+":"+str(point[2])+":\r\n")
    for element in self.elements:
      fichier.write(element.sauvegarde()) #t
    for joueur in self.joueurs:
      fichier.write(joueur.sauvegarde()) #j
    for sprite in self.sprites:
      fichier.write(sprite.sauvegarde()) #s
    fichier.close()
    
    #On zip le fichier temporaire
    zip = zipfile.ZipFile(nomFichier, "w")
    zip.write(os.path.join(".", "data", "cache", "save.tmp"), os.path.basename(nomFichier), zipfile.ZIP_DEFLATED)
    zip.close()
    #On enlève le fichier temporaire
    os.remove(os.path.join(".", "data", "cache", "save.tmp"))
    self.afficheTexte("Sauvegarde terminée", "sauvegarde")
    general.stopChrono("Planete::sauvegarde")
    
  def charge(self, fichier, simple=False):
    """Charge le géoïde depuis un fichier"""
    general.startChrono("Planete::charge")
    self.afficheTexte("Chargement en cours...", "sauvegarde")
    
    self.detruit()
    self.sommets = []
    self.faces = []
    self.lignes = []
    self.sprites = []
    self.joueurs = []
    self.sommetDansFace = {}
    self.voisinage = {}
    self.racine = render.attachNewNode("planete")

    if general.DEBUG_CHARGE_PLANETE:
      self.afficheTexte("Lecture du fichier...")

    #Lecture depuis le zip
    zip = zipfile.ZipFile(fichier, "r")
    if zip.testzip()!=None:
      print "PLANETE :: Charge :: Erreur : Fichier de sauvegarde corrompu !"
    data = zip.read(os.path.basename(fichier))
    zip.close()
    lignes = data.split("\r\n")

    if general.DEBUG_CHARGE_PLANETE:
      self.afficheTexte("Parsage des infos...")
      
    tot = len(lignes)
      
    for i in range(0, tot):
      if general.DEBUG_CHARGE_PLANETE:
        if i%500==0:
          self.afficheTexte("Parsage des infos... %i/%i" %(i, tot))
      ligne = lignes[i]
        
      elements = ligne.strip().lower().split(":")
      type = elements[0]
      elements = elements[1:]
      if type=="o":
        if elements[0]=="tesselation":
          #Attrapage des infos de tesselation
          self.tesselation = int(elements[1])
        elif elements[0]=="delta":
          #Attrapage des infos de delta
          self.delta = float(elements[1])
        elif elements[0]=="distancesoleil":
          #Attrapage des infos de distanceSoleil
          self.distanceSoleil = float(elements[1])
        elif elements[0]=="anglesoleil":
          #Attrapage des infos de angleSoleil
          self.angleSoleil = float(elements[1])
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
          print "Donnée inconnue : ",element[0]
      elif type=="p":
        #Création d'un sommet
        self.sommets.append(Vec3(float(elements[0]), float(elements[1]), float(elements[2])))
      elif type=="f":
        #Création d'une face
        ids = elements[0].replace("[","").split("]")
        if len(ids)<2:
          print
          print "Erreur ID", ids
        elif len(ids)==2:
          self.elements.append(Element("["+str(ids[0])+"]", int(elements[1]), int(elements[2]), int(elements[3]), self, 0, None))
        else:
          self.elements[int(ids[0])].charge(ids[1:], elements[1], elements[2], elements[3])
      elif type=="j":
        #Création d'un joueur
        type, nom, couleur, estJoueur, vide = elements
        couleur = VBase4(general.floatise(couleur.replace("(","").replace(")","").replace("[","").replace("]","").split(",")))
        classe = Joueur
        if type=="ia":
          classe = JoueurIA
        elif type=="local":
          classe = JoueurLocal
        elif type=="distant":
          classe = JoueurDistant
        else:
          print "PLANETE :: Charge :: Erreur, type de joueur inconnu :", type
        self.ajouteJoueur(classe(nom, couleur, estJoueur.lower().strip()=="true"))
      elif type=="jr":
        #Création des ressources d'un joueur
        nomjoueur, nomressource, valeur, vide = elements
        for joueur in self.joueurs:
          if joueur.nom.lower().strip()==nomjoueur.lower().strip():
            joueur.ressources[nomressource] = int(valeur)
      elif type=="s":
        #Sprites
        id, nomjoueur, modele, symbole, position, vitesse, vie, bouge, aquatique, vide = elements
        position = Vec3(*general.floatise(position.replace("[","").replace("]","").replace("(","").replace(")","").split(",")))
        if nomjoueur.lower().strip()=="none":
          joueur = None
        else:
          for joueurT in self.joueurs:
            if joueurT.nom.lower().strip()==nomjoueur.lower().strip():
              joueur = joueurT
        sprite = Sprite(id, position, modele, symbole, float(vie), self, joueur)
        sprite.vitesse = float(vitesse)
        sprite.bouge = bouge.lower().strip()=="true"
        sprite.aquatique = aquatique.lower().strip()=="true"
        self.sprites.append(sprite)
        joueur.sprites.append(sprite)
      elif type=="sm":
        #Mouvement des sprites
        id, elem, vide = elements
        for sprite in self.sprites:
          if sprite.id.lower().strip() == id.lower().strip():
            sprite.marcheVersTab.append(int(elem))
      elif ligne.strip()!="":
        print
        print "Avertissement : Planete::charge, type de ligne inconnue :", type,"sur la ligne :\r\n",ligne.strip()
        
    if general.DEBUG_CHARGE_PLANETE:
      self.afficheTexte("Chargement des sommets... %i sommets chargés" %(len(self.sommets)))
    
    if not simple:
      self.fabriqueVoisinage()
      
      #On ajoute le gestionnaire d'intelligence artificielle
      self.aiNavigation = AINavigation(self)
      self.aiNavigation.grapheDeplacement()
    self.afficheTexte("Chargement terminé", "sauvegarde")
    general.stopChrono("Planete::charge")
  # Fin Import / Export ------------------------------------------------
      
  # Mise à jour --------------------------------------------------------
  def fabriqueSoleil(self, type=None):
    if type==None:
      type = general.configuration.getConfiguration("affichage", "effets", "typeEclairage", "shader")
    type=type.lower().strip()
      
    couleurSoleil = general.configuration.getConfiguration("Planete", "Univers", "couleurSoleil", "0.9 0.9 0.9 0.8")
    couleurSoleil = VBase4(*general.floatise(couleurSoleil.split(" ")))
      
    if type=="flat":
      light = PointLight('soleil')
      light.setColor(couleurSoleil)
      self.soleil = self.racine.attachNewNode(light)
      self.soleil.setPos(0,0,0)
      self.soleil.setLightOff()
      self.racine.setLight(self.soleil)
      
      cardMaker = CardMaker('soleil')
      cardMaker.setFrame(-0.5, 0.5, -0.5, 0.5)
      bl = self.racine.attachNewNode(cardMaker.generate())
      #Applique la tecture dessus
      tex = loader.loadTexture("data/textures/soleil.png")
      bl.setTexture(tex)
      #Active la transprence
      bl.setTransparency(TransparencyAttrib.MDual)
      #Fait une mise à l'échelle
      bl.setScale(0.8)
      #On fait en sorte que la carte soit toujours tournée vers la caméra, le haut vers le haut
      bl.setBillboardPointEye()

      #bl = loader.loadModel("./data/modeles/sphere.egg")
      bl.reparentTo(self.soleil)
      
      self.soleil.reparentTo(self.racine)
    elif type=="none":
      self.soleil = loader.loadModel("./data/modeles/sphere.egg")
      self.soleil.reparentTo(self.racine)
    elif type=="shader":
      #Vérification de la carte graphique
      if (base.win.getGsg().getSupportsBasicShaders()==0):
        raw_input("Planete: Pas de shader dans la carte graphique.")
        self.fabriqueSoleil("flat")
      if (base.win.getGsg().getSupportsDepthTexture()==0):
        raw_input("Planete: Pas de texture de profondeur.")
        self.fabriqueSoleil("flat")
    
      #Crée une fenêtre de rendu hors écran
      winprops = WindowProperties.size(512,512)
      props = FrameBufferProperties()
      props.setRgbColor(1)
      props.setAlphaBits(1)
      props.setDepthBits(1)
      LBuffer = base.graphicsEngine.makeOutput(
               base.pipe, "offscreen buffer", -2,
               props, winprops,
               GraphicsPipe.BFRefuseWindow,
               base.win.getGsg(), base.win)

      if (LBuffer == None):
        raw_input("Planete: Pas de buffer hors écran.")
        self.fabriqueSoleil("flat")

      #self.racine.setShaderAuto()

      #Ajoute une texture de profondeur
      Ldepthmap = Texture()
      LBuffer.addRenderTexture(Ldepthmap, GraphicsOutput.RTMBindOrCopy, GraphicsOutput.RTPDepthStencil)
      if (base.win.getGsg().getSupportsShadowFilter()):
          Ldepthmap.setMinfilter(Texture.FTShadow)
          Ldepthmap.setMagfilter(Texture.FTShadow) 

      #Un buffer en couleur pour le debug
      Lcolormap = Texture()
      LBuffer.addRenderTexture(Lcolormap, GraphicsOutput.RTMBindOrCopy, GraphicsOutput.RTPColor)

      #On fabrique une caméra qui sera notre lampe
      self.soleil=base.makeCamera(LBuffer)
      self.soleil.node().setScene(render)

      #On prépare les variables du shader
      render.setShaderInput('light', self.soleil)
      render.setShaderInput('Ldepthmap', Ldepthmap)
      render.setShaderInput('ambient', self.ambient,0,0,1.0)
      render.setShaderInput('texDisable', 0,0,0,0)
      render.setShaderInput('scale', 1,1,1,1)
      render.setShaderInput('push',self.pushBias,self.pushBias,self.pushBias,0)

      #On place le shader sur le soleil
      lci = NodePath(PandaNode("Light Camera Initializer"))
      lci.setShader(Shader.load('data/shaders/caster.sha'))
      self.soleil.node().setInitialState(lci.getState())
    
      #On place un shader sur la caméra écran
      #Si la carte 3D a du hardware pour ça, on l'utilise
      mci = NodePath(PandaNode("Main Camera Initializer"))
      if (base.win.getGsg().getSupportsShadowFilter()):
          mci.setShader(Shader.load('data/shaders/shadow.sha'))
      else:
          mci.setShader(Shader.load('data/shaders/shadow-nosupport.sha'))
      base.cam.node().setInitialState(mci.getState())
      
      #On configure notre soleil
      self.soleil.setPos(0,-40,40)
      self.soleil.lookAt(0,0,0)
      self.soleil.node().getLens().setFov(30)
      self.soleil.node().getLens().setNearFar(20,60)
      #self.soleil.node().showFrustum()
    
      #base.bufferViewer.toggleEnable()
    else:
      print "Type d'éclairage inconnu",type
      
  def ajouteSprite(self, id, position, type):
    """
    Ajoute un nouveau sprite
    id : l'identifiant du sprite
    position : sa position sur le terrain
    type : le type de sprite à créer
    """
    fichier = os.path.join(".","data","sprites",type+".spr")
    if not os.path.exists(fichier):
      print "Sprite inconnu",type, "->", fichier
    id = "[neutre]"+id+"-"+str(len(self.sprites)+1)
    sprite = Sprite(id=id, position=position, fichierDefinition=fichier, planete=self, joueur=None)
    self.sprites.append(sprite)
    return sprite

  def ping(self, temps):
    general.startChrono("Planete::ping")
    """Fonction appelée a chaque image, temps indique le temps écoulé depuis l'image précédente"""
    
    #On fabrique le soleil si on en a pas
    if self.soleil == None:
      self.fabriqueSoleil()

    #Fait tourner le soleil
    self.angleSoleil += temps / math.pi * self.vitesseSoleil
    if self.soleil != None and self.soleil != 1:
      self.soleil.setPos(0.0, math.sin(self.angleSoleil)*self.distanceSoleil, math.cos(self.angleSoleil)*self.distanceSoleil)
      self.soleil.lookAt(0,0,0)
      
      if self.flare != None:
        self.flare.detachNode()
        self.flare.removeNode()
        self.flare=None
      #Calcule le lens flare
      if general.ligneCroiseSphere(general.gui.io.camera.getPos(), self.soleil.getPos(), (0.0,0.0,0.0), 1.0) == None:
        ptLum = general.map3dToRender2d(render, self.soleil.getPos())
        if ptLum!=None:
          pass
          """self.flare = NodePath("flare")
          for i in range(0, 3):
            p=ptLum[0]*i/3.0, ptLum[1]*i/3.0, ptLum[2]*i/3.0
            #Fabrique un carré
            cardMaker = CardMaker('flare')
            cardMaker.setFrame(0.1, 0.1, 0.1, 0.1)
            cardMaker.setHasNormals(True)
            flare = self.flare.attachNewNode(cardMaker.generate())
            flare.setTexture("./data/textures/flare/lens-flare1.png")
            flare.setPos(*p)
          self.flare.reparentTo(render2d)"""        
      
    if self.azure != None:
      self.azure.lookAt(self.soleil)

    #Regarde s'il faut optimiser le modèle 3D, passe au minimum (apr défaut) 3 secondes après la dernière modification du modèle
    dureeOptimise = float(general.configuration.getConfiguration("Planete", "MAJ", "duree-optimisation", 3.0))
    for element in self.elements:
      if element.besoinOptimise:
        element.pileOptimise+=temps
        if element.pileOptimise > dureeOptimise:
          element.fabriqueModel(optimise=True)
      
    #Met à jour l'état des joueurs
    for joueur in self.joueurs:
      joueur.ping(temps)
      
    #Met à jour les états des sprites
    for sprite in self.sprites[:]:
#      if general.ligneCroiseSphere(sprite.position, self.soleil.getPos(), (0.0,0.0,0.0), 1.0) != None:
#        if not sprite.nocturne:
#          sprite.tue("obscurite")
      if not sprite.ping(temps):
        if sprite.joueur !=None:
          sprite.joueur.spriteMort(sprite)
        self.sprites.remove(sprite)
        
    #Sauvegarde automatique
    self.lastSave += temps
    if self.seuilSauvegardeAuto != -1 and self.lastSave > self.seuilSauvegardeAuto:
      self.afficheTexte("Sauvegarde automatique en cours...", "sauvegarde")
      self.sauvegarde(os.path.join(".","sauvegardes","sauvegarde-auto.pln"))
      self.lastSave = 0
      
      
    if general.configuration.getConfiguration("affichage","minimap","affichesoleil","t")=="t":
      #Met à jour la carte du soleil
      self.lastMAJPosSoleil += temps
      if self.lastMAJPosSoleil > self.dureeMAJPosSoleil:
        self.lastMAJPosSoleil=0.0
        try:
          def procFace(face):
            jour = (1.0,1.0,1.0)
            nuit = (0.2,0.2,0.4)
            p1 = Vec3(self.sommets[face.sommets[0]])
            p1.normalize()
            p1 = p1 * 1.0001
            if general.ligneCroiseSphere(p1, self.soleil.getPos(), Vec3(0.0,0.0,0.0), 1.0) != None:
              c1=nuit
            else:
              c1=jour
            p2 = Vec3(self.sommets[face.sommets[1]])
            p2.normalize()
            p2 = p2 * 1.0001
            if general.ligneCroiseSphere(p2, self.soleil.getPos(), Vec3(0.0,0.0,0.0), 1.0) != None:
              c2=nuit
            else:
              c2=jour
            p3 = Vec3(self.sommets[face.sommets[2]])
            p3.normalize()
            p3 = p3 * 1.0001
            if general.ligneCroiseSphere(p3, self.soleil.getPos(), Vec3(0.0,0.0,0.0), 1.0) != None:
              c3=nuit
            else:
              c3=jour
            if face.enfants == None or (c1==c2 and c2==c3):
              general.gui.menuCourant.miniMap.dessineCarte(p1, p2, p3, c1, c2, c3, True)
            return not (c1==c2 and c2==c3) #Return False si tout est de la meme couleur
            
          def recur(face):
            if procFace(face):
              if face.enfants != None:
                for enfant in face.enfants:
                  recur(enfant)
          for face in self.elements:
            recur(face)
        except AttributeError:
          pass
    
    general.stopChrono("Planete::ping")
  # Fin Mise à jour ----------------------------------------------------
        
  # Fonctions diverses -------------------------------------------------
  def trouveSommet(self, point, tiensCompteDeLAngle=False):
    """
    Retourne le sommet le plus proche
    point : le point à rechercher
    """
    general.startChrono("Planete::trouveSommet")
    dst = (self.sommets[0]-point).lengthSquared()
    id = 0
    for s in self.sommets:
      d = (s-point).lengthSquared()
      if dst > d:
        #On fait attention à pouvoir aller à ce point là
        if not tiensCompteDeLAngle:
          id = self.sommets.index(s)
          dst = d
        elif self.aiNavigation.coutPassage(point, s, False)<self.aiNavigation.maxcout:
          id = self.sommets.index(s)
          dst = d
    general.stopChrono("Planete::trouveSommet")
    return id
    
  def trouveFace(self, point, sub=None):
    """
    Retourne la face dans laquelle le point se trouve
    point : le point à rechercher
    sub : la liste des faces à parcourir (utiliser None dans le doute)
    TODO utiliser testIntersectionTriangleDroite pour plus de rapidité (voir #B#)
    """
    general.startChrono("Planete::trouveFace")
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
      
      da = (cible - da).lenghSquared()
      db = (cible - db).lenghSquared()
      dc = (cible - dc).lenghSquared()
      
      #Si on a une plus proche, elle remplace la meilleure
      if math.sqrt(da*da+db*db+dc*dc) < math.sqrt(d1*d1+d2*d2+d3*d3):
        d1, d2, d3 = da, db, dc
        f = face
    general.stopChrono("Planete::trouveFace")
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
      general.stopChrono("Planete::trouveFace")
      return self.trouveFace(point, f.enfants)
    general.stopChrono("Planete::trouveFace")
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
          general.stopChrono("Planete::trouveFace")
          return self.trouveFace(point, tria.enfants)
        else:
          general.stopChrono("Planete::trouveFace")
          return tria
    general.stopChrono("Planete::trouveFace")
    return None
    ## ------------ Version avec testIntersectionTriangleDroite
    
  def altitudeCarre(self, point):
    """Retourne l'altitude (rayon) à laquelle le point devrait se trouver pour être juste sur la face en dessous (au dessus) de lui (coord cartésiennes)"""
    general.startChrono("Planete::altitude")
    #Cherche la face dans laquelle se trouve le point
    face = self.trouveFace(point).sommets
    if face==None:
      #La droite passant par un point quelconque et le centre de la sphère coupe obligatoirement la dite sphère en un point
      #Ne pas avoir de résultat dit que ça bug
      print "Bug :: testIntersectionTriangleDroite déconne"
      return point.length()
    pt1, pt2, pt3 = self.sommets[face[0]], self.sommets[face[1]], self.sommets[face[2]]
    #Calcul des distances pour pondérer la position du point
    #On utilise le carré pour gagner des sqrt
    d1 = Vec3(pt1)
    d1 = d1/d1.lengthSquared()
    d2 = Vec3(pt2)
    d2 = d2/d2.lengthSquared()
    d3 = Vec3(pt3)
    d3 = d2/d2.lengthSquared()
    pt = Vec3(point)
    pt = pt/pt.lengthSquared()
    
    d1 = (d1 - pt).lenghSquared()
    d2 = (d2 - pt).lenghSquared()
    d3 = (d3 - pt).lenghSquared()
    d=d1+d2+d3
    if d!=0:
      d1=d1/d
      d2=d2/d
      d3=d3/d
    #Attrape les altitude de chaque sommet
    r1=pt1.lenghSquared()
    r2=pt2.lenghSquared()
    r3=pt3.lenghSquared()
    
    general.stopChrono("Planete::altitude")
    #Calcule l'altitude moyenne pondérée
    return r1*d1+r2*d2+r3*d3
    
  def altitude(self, point):
    return math.sqrt(self.altitudeCarre(point))

  def placeSurSol(self, point):
    """Déplace le point pour qu'il soit juste sur la surface de la facette (coord cartésiennes)"""
    point = Vec3(point)
    point.normalize()
    return point * self.altitude(point)

  def changeCoordPoint(self, oldCoord, newCoord):
    """
    Change les coordonnées du point connu par ses anciennes coordonnées vers de nouvelles coordonnées
    Met à jour la géométrie qui en a besoin
    """
    general.startChrono("Planete::changeCoordPoint")
    if self.sommets.count(oldCoord)<1:
      print "Erreur planete::changeCoordPoint,",oldCoord,"ce sommet n'existe pas"
      raw_input()
    idx = self.sommets.index(oldCoord)
    self.sommets[idx] = Vec3(*general.floatise(newCoord))
    elements = self.sommetDansFace[idx]
    elementsParents = {}
    for element in elements:
      if element.parent!=None:
        if element.parent not in elementsParents.keys():
          elementsParents[element.parent]=[]
        elementsParents[element.parent].append(element)
      else:
        if element not in elementsParents.keys():
          elementsParents[element] = []
          elementsParents[element].append(element)
        
    for element in elements:
      element.normale = None #On a bougé un point, donc sa normale a changée
      
    for element in elementsParents.keys():
      if element.besoinOptimise:
        for enfant in elementsParents[element]:
          enfant.fabriqueModel(optimise=False)
      else:
        element.fabriqueModel(optimise=False)
    self.aiNavigation.maj(idx)
    general.stopChrono("Planete::changeCoordPoint")
    
  def elevePoint(self, idx, delta):
    """Déplace le sommet d'indice idx de delta unité et met à jour la géométrie qui en a besoin"""
    general.startChrono("Planete::elevePoint")
    norme = self.sommets[idx].length()
    tmp = Vec3(self.sommets[idx])
    tmp.normalize()
    tmp = tmp * (norme + delta)
    self.changeCoordPoint(self.sommets[idx], tmp)
    general.stopChrono("Planete::elevePoint")
    
  def ajouteJoueur(self, joueur):
    general.gui.afficheTexte(joueur.nom+" est entré dans la partie", "info")
    self.joueurs.append(joueur)
  # Fin Fonctions diverses ---------------------------------------------
