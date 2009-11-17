#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general
import math
import sys
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
  besoinOptimise = False
  
  #Coloriage des vectrices
  subSubAquatique = (38.0/255, 38.0/255, 97.0/255, 1.0)
  subAquatique = (123.0/255, 123.0/255, 229.0/255, 1.0)
  sable = (234.0/255, 212.0/255, 29.0/255, 1.0)
  herbe = (116.0/255, 212.0/255, 64.0/255, 1.0)
  terre = (209.0/255, 140.0/255, 37.0/255, 1.0)
  neige = (215.0/255, 223.0/255, 241.0/255, 1.0)
  
  pileOptimise = None #Temps écoulé depuis la dernière mise a jour
  
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
    self.pileOptimise = 0.0
    
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
         p1
         /\
      c1/__\c2
       /\  /\
      /__\/__\
    p3   c3   p2
    """
    #Si on a déjà subdivisé le niveau courant, on saute directement sur les enfants
    if self.enfants != None:
      for enfant in self.enfants:
        enfant.tesselate()
      return
      
    p1, p2, p3 = self.sommets
    p1, p2, p3 = self.planete.sommets[p1], self.planete.sommets[p2], self.planete.sommets[p3]
    #On calcul les nouveaux sommets
    c1 = general.normaliseVecteur([(p1[0]+p3[0])/2, (p1[1]+p3[1])/2, (p1[2]+p3[2])/2])
    c2 = general.normaliseVecteur([(p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2])
    c3 = general.normaliseVecteur([(p2[0]+p3[0])/2, (p2[1]+p3[1])/2, (p2[2]+p3[2])/2])

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

  def fabriqueModel(self, forceCouleur=None, optimise=True):
    """
    Fabrique le modèle 3D
    Si forceCouleur est different de None, alors sa valeur sera utilisée comme couleur pour la facette
    """
    
    #Si on recalcule le modele, on met a jour le temps depuis la derniere modification
    self.parent.pileOptimise = 0.0
    
    couleur = self.couleur
    if forceCouleur!=None:
      couleur = forceCouleur
      
    #On regarde si curseur n'est pas au dessus de cette facette
    #if self.planete.survol!=None:
    #  if self.planete.survol in self.sommets:
    #    forceCouleur = [0.0, 0.0, 1.0, 1.0] #Couleur de survol
      
    #On supprime le modèle 3D existant s'il y en a un
    if self.modele != None:
      self.modele.detachNode()
      self.modele.removeNode()
    self.modele = None
    self.lignes = []
      
    #On crée un nouveau point d'encrage pour le modèle 3D
    p1, p2, p3 = self.sommets
    
    if self.profondeur > 0 or not optimise:
      self.modele = NodePath(self.id)
    else:
      self.modele = NodePath(self.id+"-rigid")
    self.modele.reparentTo(self.planete.racine)
    
    #S'il y a eut subdivision de cette partie de la géométrie, on ne s'occupe que des enfants
    if self.enfants != None:
      for enfant in self.enfants:
        #On place hiérarchiquement les enfants en dessous des parents
        mdl = enfant.fabriqueModel(forceCouleur)
        mdl.reparentTo(self.modele)
      if self.profondeur == 0:
        if optimise:
          #On dit que la couleur proviens des vectrices et qu'il faut pas le perdre
          self.modele.setAttrib(ColorAttrib.makeVertex()) 
          #Optimise le modèle
          self.modele.flattenStrong()
          self.besoinOptimise = False
        else:
          self.besoinOptimise = True
      return self.modele
    
    #S'il n'y a pas eut de subdivision, alors on trace le triange
    a, b, c = self.sommets
    p1, p2, p3 = self.planete.sommets[a], self.planete.sommets[b], self.planete.sommets[c]
    
    if not general.WIREFRAME:
      nd = self.fabriqueTriangle(p1, p2, p3, forceCouleur)
      self.modele.attachNewNode(nd)
    else:
      nd = self.dessineLigne(couleur, p1, p2)
      self.modele.attachNewNode(nd)
      nd = self.dessineLigne(couleur, p1, p3)
      self.modele.attachNewNode(nd)
      nd = self.dessineLigne(couleur, p2, p3)
      self.modele.attachNewNode(nd)
      
    self.modele.setPythonTag("type","sol")
    return self.modele
    
  def couleurSommet(self, sommet):
    """Retourne une couleur suivant l'altitude du sommet"""
    minAlt = (1.0-self.planete.delta)*(1.0-self.planete.delta)
    maxAlt = (1.0+self.planete.delta)*(1.0+self.planete.delta)
    altitude = general.normeVecteurCarre(sommet)
    prct = (altitude-minAlt)/(maxAlt-minAlt)*100
    
    if prct < -10:
      return self.subSubAquatique #Eau super profonde
    elif prct < 0:
      return self.subAquatique #Eau
    elif prct < 10:
      return self.sable #Plage
    elif prct < 50:
      return self.herbe #Sol normal
    elif prct < 90:
      return self.terre #Montagne
    else:
      return self.neige #Haute montagne
    
  def dessineLigne(self, couleur, depart, arrivee):
    """Dessine une ligne de depart vers arrivée et ne fait pas de doublons"""
    if self.lignes.count((min(depart, arrivee), max(depart,arrivee))) == 0:
      ls = LineSegs()
      ls.setColor(*couleur)
      ls.setThickness(1.0)
      ls.moveTo(depart[0], depart[1], depart[2])
      ls.drawTo(arrivee[0], arrivee[1], arrivee[2])
      return ls.create()
    
  def fabriqueTriangle(self, p1, p2, p3, forceCouleur=None):
    """Fabrique la géométrie de la face triangulaire définie par p1, p2 et p3"""
    format = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData('TriangleVertices',format,Geom.UHStatic)

    vWriter = GeomVertexWriter(vdata, 'vertex')
    cWriter = GeomVertexWriter(vdata, 'color')
    nWriter = GeomVertexWriter(vdata, 'normal')
    
    if forceCouleur==None:
      c1=self.couleurSommet(p1)#couleur#[random.random(),random.random(),random.random(),1.0]
      c2=self.couleurSommet(p2)#couleur#[random.random(),random.random(),random.random(),1.0]
      c3=self.couleurSommet(p3)#couleur#.random(),random.random(),random.random(),1.0]
    else:
      c1 = forceCouleur
      c2 = forceCouleur
      c3 = forceCouleur

    n1=self.calculNormale(p1)
    n2=self.calculNormale(p2)
    n3=self.calculNormale(p3)
    
    #self.dessineLigne((1.0,0.0,0.0,1.0), p1, general.sommeVecteurs(p1, n1))
    #self.dessineLigne((0.0,1.0,0.0,1.0), p2, general.sommeVecteurs(p1, n2))
    #self.dessineLigne((0.0,0.0,1.0,1.0), p3, general.sommeVecteurs(p1, n3))
    
    vWriter.addData3f(*p1)
    nWriter.addData3f(*n1)
    cWriter.addData4f(*c1)
    vWriter.addData3f(*p2)
    nWriter.addData3f(*n2)
    cWriter.addData4f(*c2)
    vWriter.addData3f(*p3)
    nWriter.addData3f(*n3)
    cWriter.addData4f(*c3)

    prim = GeomTriangles(Geom.UHStatic)
    prim.addVertex(0)
    prim.addVertex(1)
    prim.addVertex(2)
    prim.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(prim)

    node = GeomNode('gnode')
    node.addGeom(geom)
    return node
    
  def calculNormale(self, point=None):
    """
    Calcul la normale en un sommet
    La normale du sommet est la moyenne des normales des faces de ce sommet
    """
    if self.normale==None: #Si on pas de normale en cette face, on la recalcule
      p1 = self.planete.sommets[self.sommets[0]]
      p2 = self.planete.sommets[self.sommets[1]]
      p3 = self.planete.sommets[self.sommets[2]]
      self.normale = general.multiplieVecteur(general.normaliseVecteur(general.crossProduct(general.retraitVecteurs(p1, p2), general.retraitVecteurs(p3, p2))), -1.0)      
    
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
    return general.normaliseVecteur((a/cpt, b/cpt, c/cpt))
      
  def sauvegarde(self):
    """Produit une ligne formattée utilisable pour la sauvegarde de la structure de données"""
    out="T:"+self.id+":"+str(self.sommets[0])+":"+str(self.sommets[1])+":"+str(self.sommets[2])+":\r\n"
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
