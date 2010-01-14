#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general
import math
import sys, os
import random

from pandac.PandaModules import *

class Element:
  id = None #Identifiant de la face, utilisé pour reconstruire la géométrie au chargement
  sommets = None #Liste des 3 sommets de la face
  modele = None #Modele 3D de la face
  lignes = None #Elements du fil de fer
  profondeur = None #Profondeur de tesselation courante de cette face
  enfants = None #Liste des sous face si elle a été tesselée
  couleur = None #Couleur de la face (Fil de fer uniquement)
  planete = None #L'instance de la planète dont cette face appartient
  
  normale = None #La normale de la face
  parent = None
  
  #Coloriage des vectrices
  subSubAquatique = (38.0/255, 38.0/255, 97.0/255, 1.0)
  subAquatique = (123.0/255, 123.0/255, 229.0/255, 1.0)
  sable = (234.0/255, 212.0/255, 29.0/255, 1.0)
  herbe = (116.0/255, 212.0/255, 64.0/255, 1.0)
  terre = (209.0/255, 140.0/255, 37.0/255, 1.0)
  neige = (215.0/255, 223.0/255, 241.0/255, 1.0)
    
  def __init__(self, id, p1, p2, p3, planete, profondeur, parent):
    """
    Prépare une nouvelle facette
    id : sont identifiant de la forme [id parent 1][id parent 2][...][id parent n-1][id facette]
    p1, p2, p3 : les indices des sommets de la face dans la liste des sommets
    planete : l'instance de la planète à laquelle cette face appartient
    profondeur : le niveau de tesselation acutel
    """
    self.id=id
    self.sommets=[p1, p2, p3]
    self.planete = planete
    self.lignes = []
    self.couleur = (random.random(),random.random(),random.random(),1.0)
    self.profondeur = profondeur
    
    if parent!=None:
      self.parent = parent
    else:
      self.parent = self
    
    
    if not p1 in self.planete.sommetDansFace.keys():
      self.planete.sommetDansFace[p1] = []
    if not p2 in self.planete.sommetDansFace.keys():
      self.planete.sommetDansFace[p2] = []
    if not p3 in self.planete.sommetDansFace.keys():
      self.planete.sommetDansFace[p3] = []
      
    self.planete.sommetDansFace[p1].append(self)
    self.planete.sommetDansFace[p2].append(self)
    self.planete.sommetDansFace[p3].append(self)
    
    if general.DEBUG_CONSTRUCTION_SPHERE:
      delta = (random.random()-0.5)/10 +1.0
      self.modele = NodePath(self.id)
      self.modele.reparentTo(self.planete.racineModel)
      p1 = self.planete.sommets[p1] * delta
      p2 = self.planete.sommets[p2] * delta
      p3 = self.planete.sommets[p3] * delta
      
      nd = self.dessineLigne((1.0,0.0,0.0,1.0), p1, p2)
      self.modele.attachNewNode(nd)
      nd = self.dessineLigne((0.0,1.0,0.0,1.0), p2, p3)
      self.modele.attachNewNode(nd)
      nd = self.dessineLigne((0.0,0.0,1.0,1.0), p3, p1)
      self.modele.attachNewNode(nd)
      
  def detruit(self):
    """Détruit la géométrie"""
    if self.enfants != None:
      for enfant in self.enfants:
        enfant.detruit()
    if self.modele != None:
      self.modele.detachNode()
      self.modele.removeNode()
      self.modele = None
    self.lignes = []
    
  def tesselate(self):
    """
    Découpe la face courante en 4 facette triangulaires
    Comme le triangle de base est équilatéral, on garde une subdivision équilatérale
         p2
         /\
      c2/__\c3
       /\  /\
      /__\/__\
    p1   c1   p3
    """
    
    print "Tesselate",self.id
    
    #Si on a déjà subdivisé le niveau courant, on saute directement sur les enfants
    if self.enfants != None:
      for enfant in self.enfants:
        enfant.tesselate()
      return
      
    p1, p2, p3 = self.sommets
    p1, p2, p3 = self.planete.sommets[p1], self.planete.sommets[p2], self.planete.sommets[p3]
    #On calcul les nouveaux sommets
    c1 = (p1+p3)/2
    c2 = (p1+p2)/2
    c3 = (p2+p3)/2
    c1.normalize()
    c2.normalize()
    c3.normalize()

    #On ajoute les nouveaux sommets s'ils n'existent pas déjà
    if self.planete.sommets.count(c1)==0:
      self.planete.sommets.append(c1)
    if self.planete.sommets.count(c2)==0:
      self.planete.sommets.append(c2)
    if self.planete.sommets.count(c3)==0:
      self.planete.sommets.append(c3)
      
    #On fabrique les nouveaux triangles
    self.enfants = []
    self.enfants.append(Element(self.id+"["+str(len(self.enfants))+"]", self.planete.sommets.index(p1), self.planete.sommets.index(c2), self.planete.sommets.index(c1), self.planete, self.profondeur+1, self.parent))
    self.enfants.append(Element(self.id+"["+str(len(self.enfants))+"]", self.planete.sommets.index(c2), self.planete.sommets.index(p2), self.planete.sommets.index(c3), self.planete, self.profondeur+1, self.parent))
    self.enfants.append(Element(self.id+"["+str(len(self.enfants))+"]", self.planete.sommets.index(c1), self.planete.sommets.index(c2), self.planete.sommets.index(c3), self.planete, self.profondeur+1, self.parent))
    self.enfants.append(Element(self.id+"["+str(len(self.enfants))+"]", self.planete.sommets.index(c1), self.planete.sommets.index(c3), self.planete.sommets.index(p3), self.planete, self.profondeur+1, self.parent))
    
  def fabriqueModel(self):
    """
    Fabrique le modèle 3D
    Si forceCouleur est different de None, alors sa valeur sera utilisée comme couleur pour la facette
    """
    lvlOpt = 1
    
    if self.modele!=None:
      self.modele.detachNode()
      self.modele.removeNode()
    
    if self.profondeur == lvlOpt:
      vdata, vWriter, nWriter, tWriter, cWriter = self.fabriqueGeomVertex()
      if self.planete.vdata == None:
        self.planete.ajouteVerteces(vdata, vWriter, nWriter, tWriter, cWriter)
      primitives = []
      for enfant in self.enfants:
        primitives += enfant.assemblePrimitives()
      geom = Geom(vdata)
      for prim in primitives:
        geom.addPrimitive(prim)

      node = GeomNode('gnode')
      node.addGeom(geom)
      self.modele = NodePath(node)
      
    else:
      self.modele = NodePath("")
      for enfant in self.enfants:
        mdl = enfant.fabriqueModel()
        mdl.reparentTo(self.modele)
        
    self.modeleReal = self.modele
    self.modele = NodePath("insertion")
    insert = NodePath("insertion-inv")
    self.modeleReal.reparentTo(insert)
    insert.reparentTo(self.modele)
    
    self.modele.setPos(general.planete.geoide.sommets[self.sommets[0]])
    insert.setPos(-general.planete.geoide.sommets[self.sommets[0]])
        
    self.modele.reparentTo(self.planete.racineModel)
    self.modele.setPythonTag("type","sol")
    
    self.fabriqueVegetation()
    return self.modele
    
    
  def fabriqueVegetation(self):
    vegetation=[]
    vegetation.append([]) #Vide
    vegetation.append(["palmier","banana","benjamina01","dypsis01","ficus01","ginger","greenhouse-palm-acai01","greenhouse-palm-acai02","greenhouse-palm-acai03","greenhouse-palm-cycas01","greenhouse-palm-jubaea01","howea01"]) #Sable/plage
    vegetation.append(["herbe", "sapin1","cerisier","boulot1","boulot2","benjamina01","bougainvillier","dypsis01","eucalyptus","ginger", "howea01", "sophora", "rose"]) #Herbe/champ
    vegetation.append(["herbe", "sapin2","cerisier","boulot1","boulot2","arbrerond","bougainvillier","dypsis01","eucalyptus","ginger", "greenhouse-if01", "greenhouse-if02", "greenhouse-if03", "howea01", "sophora"]) #Feuilluts
    vegetation.append(["herbe", "sapin3","petitarbre","sapin2","sapin1","bougainvillier","ginger", "greenhouse-if01", "greenhouse-if02", "greenhouse-if03", "rose"]) #Altitude
        
    self.vegetation = NodePath("vegetation")#RigidBodyCombiner("vegetation"))
    self.vegetation.reparentTo(self.modeleReal)
        
        
    s1 = general.planete.geoide.sommets[self.sommets[0]]
    s2 = general.planete.geoide.sommets[self.sommets[0]]
    s3 = general.planete.geoide.sommets[self.sommets[0]]
    if (s1.length()+s2.length()+s3.length())/3>general.planete.geoide.niveauEau:
        h1 = self.couleurSommet(s1)[2]
        h2 = self.couleurSommet(s2)[2]
        h3 = self.couleurSommet(s3)[2]
        if h1>0 and h2>0 and h3>0:
          for i in range(0, random.random()*general.configuration.getConfiguration("planete","Generation", "nombre-bosquet","2", int)):
            if random.random()>1.0-general.configuration.getConfiguration("planete","Generation", "densite-bosquet","0.8", float):
              r1=random.random()
              r2=random.random()
              if r1+r2>1.0:
                r2=1.0-r1
              r3=1.0-(r1+r2)
              
              p = s1*r1+s2*r2+s3*r3
              alt = p.length()
              if alt>general.planete.geoide.niveauEau:
                #p.normalize()
                #p=p*alt
                type=int((float(h1)+float(h2)+float(h3))/3.0+0.5)
                typeVegetation = random.choice(vegetation[type])
                sprite = general.planete.ajouteSprite(typeVegetation, p, typeVegetation)
                sprite.rac.reparentTo(self.vegetation)
                sprite.racine.flattenStrong()
                #on change d'échelle aléatoirement pour varier un peu
                sprite.echelle = sprite.echelle*(1.0-random.random()/8)
                sprite.racine.setScale(sprite.echelle)
                sprite.fabriqueModel()
                #On tourne les arbres aléatoirement pour plus de variation
                sprite.modele.setH(random.random()*360)
    #self.vegetation.node().collect()
                
        
  texturesValides=["subsubaquatique", "subaquatique", "sable", "champ", "herbe",
  "feuillesa", "feuillesb", "feuillesc", "cailloux", "neige"]
    
  def couleurSommet(self, sommet):
    """Retourne une couleur et une texture suivant l'altitude du sommet"""
    minAlt = self.planete.niveauEau#(1.0-self.planete.delta)*(1.0-self.planete.delta)
    maxAlt = (1.0+self.planete.delta)*(1.0+self.planete.delta)
    altitude = sommet.lengthSquared()
    prct = (altitude-minAlt)/(maxAlt-minAlt)*100

    if prct < -10:
      return self.subSubAquatique, "subsubaquatique", 0 #Eau super profonde
    elif prct < 0:
      return self.subAquatique, "subaquatique", -1 #Eau
    elif prct < 35:
      return self.sable, "sable", 1 #Plage
    elif prct < 40:
      return self.herbe, "champ", 2 #Sol normal
    elif prct < 50:
      return self.herbe, "herbe", 2 #Sol normal
    elif prct < 65:
      return self.terre, "feuillesc", 3 #Montagne
    elif prct < 70:
      return self.terre, "feuillesb", 3 #Montagne
    elif prct < 80:
      return self.terre, "feuillesa", 4 #Montagne
    elif prct < 90:
      return self.terre, "cailloux", 0 #Montagne
    else:
      return self.neige, "neige", 0 #Haute montagne
    
  def dessineLigne(self, couleur, depart, arrivee):
    """Dessine une ligne de depart vers arrivée et ne fait pas de doublons"""
    if self.lignes.count((min(depart, arrivee), max(depart,arrivee))) == 0:
      ls = LineSegs()
      ls.setColor(*couleur)
      ls.setThickness(1.0)
      ls.moveTo(depart[0], depart[1], depart[2])
      ls.drawTo(arrivee[0], arrivee[1], arrivee[2])
      return ls.create()
    
  def fabriqueGeomVertex(self):
    #Prepare la création du triangle
    if self.planete.vdata == None:
      format = GeomVertexFormat.getV3n3c4t2() #On donne les vectrices, les normales et les textures
        
      vdata = GeomVertexData('TriangleVertices',format,Geom.UHStatic)
    else:
      vdata = self.planete.vdata

    vWriter = GeomVertexWriter(vdata, 'vertex')
    nWriter = GeomVertexWriter(vdata, 'normal')
    tWriter = GeomVertexWriter(vdata, 'texcoord')
    cWriter = GeomVertexWriter(vdata, 'color')
    
    return vdata, vWriter, nWriter, tWriter, cWriter
    
  def assemblePrimitives(self):
    primitives = []
    if self.enfants != None:
      for enfant in self.enfants:
        primitives+=enfant.assemblePrimitives()
    else:
      p1, p2, p3 = self.sommets
      primitives.append(self.ajouteFace(p1, p2, p3))
    return primitives
    
  def ajouteFace(self, o1, o2, o3):
    #On fabrique la géométrie
    prim = GeomTriangles(Geom.UHStatic)
    prim.addVertex(o1)
    prim.addVertex(o2)
    prim.addVertex(o3)
    prim.closePrimitive()
    return prim
    
  def calculNormale(self, point=None):
    """
    Calcul la normale en un sommet
    La normale du sommet est la moyenne des normales des faces de ce sommet
    """
    if self.normale==None: #Si on pas de normale en cette face, on la recalcule
      p1 = self.planete.sommets[self.sommets[0]]
      p2 = self.planete.sommets[self.sommets[1]]
      p3 = self.planete.sommets[self.sommets[2]]
      self.normale = -(p1-p2).cross(p3-p2)
      self.normale.normalize()
    
    if point==None:
      #Si on ne donne pas de point, alors on renvoie la coordonnée locale
      return self.normale
      
    faces = self.planete.sommetDansFace[self.planete.sommets.index(point)]
    a,b,c = self.normale
    cpt=1.0
    for face in faces:
      d,e,f = face.calculNormale(None)
      a+=d
      b+=e
      c+=f
      cpt+=1.0
    result = Vec3(a,b,c)/cpt
    result.normalize()
    return result
      
  def sauvegarde(self):
    """Produit une ligne formattée utilisable pour la sauvegarde de la structure de données"""
    out="F:"+self.id+":"+str(self.sommets[0])+":"+str(self.sommets[1])+":"+str(self.sommets[2])+":\r\n"
    if self.enfants != None:
      for enfant in self.enfants:
        out+=enfant.sauvegarde()
    return out
    
  def charge(self, ids, pt1, pt2, pt3):
    """Recrée les structures et informations nécessaires à partir d'un fichier"""
    if len(ids)<2:
      print "erreur id", ids
    elif len(ids)==2:
      if self.enfants==None:
        self.enfants=[]
      self.enfants.append(Element(self.id+"["+str(ids[0])+"]", int(pt1), int(pt2), int(pt3), self.planete, self.profondeur+1, self.parent))
    else:
      self.enfants[int(ids[0])].charge(ids[1:], pt1, pt2, pt3)
