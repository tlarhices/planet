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
    
    if general.DEBUG_CONSTRUCTION_SPHERE:
      delta = (random.random()-0.5)/10 +1.0
      self.modele = NodePath(self.id)
      self.modele.reparentTo(self.planete.racine)
      p1 = general.multiplieVecteur(self.planete.sommets[p1], delta)
      p2 = general.multiplieVecteur(self.planete.sommets[p2], delta)
      p3 = general.multiplieVecteur(self.planete.sommets[p3], delta)
      
      
      A=general.crossProduct((p2[0]-p1[0],p2[1]-p1[1],p2[2]-p1[2]), (p3[0]-p2[0],p3[1]-p2[1],p3[2]-p2[2]))
      B=general.crossProduct((p3[0]-p2[0],p3[1]-p2[1],p3[2]-p2[2]), (p1[0]-p3[0],p1[1]-p3[1],p1[2]-p3[2]))
      C=general.crossProduct((p1[0]-p3[0],p1[1]-p3[1],p1[2]-p3[2]), (p2[0]-p1[0],p2[1]-p1[1],p2[2]-p1[2]))
      if general.distance(A, B)>0.00001:
        print A,B,C
        print A[0]-B[0], A[1]-B[1], A[2]-B[2]
        raw_input("Erreur tournicotte")
      if general.distance(C, B)>0.00001:
        print A,B,C
        print B[0]-C[0], B[1]-C[1], B[2]-C[2]
        raw_input("Erreur tournicotte")
      
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
    
  textures={}
    
  def textureMixer(self, t1, t2, t3):
    """Mixe les textures t1, t2 et t3"""
    tailleTexture = int(general.configuration.getConfiguration("affichage-general", "taille-texture","256"))
    if t1 not in self.texturesValides:
      print "Avertissement :: Texture non validee :",t1
    if t2 not in self.texturesValides:
      print "Avertissement :: Texture non validee :",t2
    if t3 not in self.texturesValides:
      print "Avertissement :: Texture non validee :",t3
    #On regarde si on a pas déjà calculé cette texture
    clef = t1+"-"+t2+"-"+t3
    if clef in self.textures.keys():
      return self.textures[clef]
    if general.configuration.getConfiguration("affichage-general", "cache-texture","1")=="1":
      if clef+".png" in os.listdir(os.path.join(".","data","cache")):
        texture = loader.loadTexture("data/cache/"+clef+".png")
        self.textures[clef] = texture
        return texture
    print "Création de la texture", clef
    #Charge les 3 textures et les redimentionne en 256x256
    tmp1 = PNMImage()
    tmp1.read(Filename("data/textures/"+t1+".png"))
    i1 = PNMImage(tailleTexture, tailleTexture)
    i1.gaussianFilterFrom(1.0, tmp1)
    tmp2 = PNMImage()
    tmp2.read(Filename("data/textures/"+t2+".png"))
    i2 = PNMImage(tailleTexture, tailleTexture)
    i2.gaussianFilterFrom(1.0, tmp2)
    tmp3 = PNMImage()
    tmp3.read(Filename("data/textures/"+t3+".png"))
    i3 = PNMImage(tailleTexture, tailleTexture)
    i3.gaussianFilterFrom(1.0, tmp3)
    
    #On produit une image vierge qui contiendra notre texture finale
    imageFinale = PNMImage(tailleTexture, tailleTexture)
    imageFinale.fill(1, 1, 1)
    
    for x in range(0, tailleTexture):
      for y in range(0, tailleTexture):
        c1 = i1.getXel(x,y)
        c2 = i2.getXel(x,y)
        c3 = i3.getXel(x,y)
        
        #Interpole les couleurs de pixels
        def interpole(a, b, c, x, y):
          fa = general.distance((x,y,0),(0.0,0.0,0.0)) #HG
          fb = general.distance((x,y,0),(tailleTexture,tailleTexture,0.0)) #BD
          fc = general.distance((x,y,0),(0.0,tailleTexture,0.0)) #BG
          fac = (fa+fb+fc)/2
          fa = 1-fa/fac
          fb = 1-fb/fac
          fc = 1-fc/fac
          return b*fa+c*fb+a*fc
        c = interpole(c1[0], c2[0], c3[0], x, y), interpole(c1[1], c2[1], c3[1], x, y), interpole(c1[2], c2[2], c3[2], x, y)
        
        imageFinale.setXel(x, y, c)
        
    #On garde la texture en mémoire pour de futures utilisations
    if general.configuration.getConfiguration("affichage-general", "cache-texture","1")=="1":
      imageFinale.write(Filename("data/cache/"+clef+".png")); 
    texture = Texture("imageFinale")
    texture.load(imageFinale)
    self.textures[clef] = texture
    return texture
    
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
    if general.DEBUG_CONSTRUCTION_SPHERE:
      return self.modele
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
          ##On dit que la couleur proviens des vectrices et qu'il faut pas le perdre
          #self.modele.setAttrib(ColorAttrib.makeVertex()) 
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
      nd.reparentTo(self.modele)
    else:
      nd = self.dessineLigne(couleur, p1, p2)
      self.modele.attachNewNode(nd)
      nd = self.dessineLigne(couleur, p1, p3)
      self.modele.attachNewNode(nd)
      nd = self.dessineLigne(couleur, p2, p3)
      self.modele.attachNewNode(nd)
      
    self.modele.setPythonTag("type","sol")
    return self.modele
    
  texturesValides=["subsubaquatique", "subaquatique", "sable", "champ", "herbe",
  "feuillesa", "feuillesb", "feuillesc", "cailloux", "neige"]
    
  def couleurSommet(self, sommet):
    """Retourne une couleur et une texture suivant l'altitude du sommet"""
    minAlt = self.planete.niveauEau#(1.0-self.planete.delta)*(1.0-self.planete.delta)
    maxAlt = (1.0+self.planete.delta)*(1.0+self.planete.delta)
    altitude = general.normeVecteurCarre(sommet)
    prct = (altitude-minAlt)/(maxAlt-minAlt)*100

    if prct < -10:
      return self.subSubAquatique, "subsubaquatique" #Eau super profonde
    elif prct < 0:
      return self.subAquatique, "subaquatique" #Eau
    elif prct < 35:
      return self.sable, "sable" #Plage
    elif prct < 40:
      return self.herbe, "champ" #Sol normal
    elif prct < 50:
      return self.herbe, "herbe" #Sol normal
    elif prct < 65:
      return self.terre, "feuillesc" #Montagne
    elif prct < 70:
      return self.terre, "feuillesb" #Montagne
    elif prct < 80:
      return self.terre, "feuillesa" #Montagne
    elif prct < 90:
      return self.terre, "cailloux" #Montagne
    else:
      return self.neige, "neige" #Haute montagne
    
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
    #Prepare la création du triangle
    if general.TEXTURES:
      format = GeomVertexFormat.getV3n3t2() #On donne les vectrices, les normales et les textures
    else:
      format = GeomVertexFormat.getV3n3c4() #On donne les vectrices, les normales et les couleurs
      
    vdata = GeomVertexData('TriangleVertices',format,Geom.UHStatic)

    vWriter = GeomVertexWriter(vdata, 'vertex')
    nWriter = GeomVertexWriter(vdata, 'normal')
    if general.TEXTURES:
      tWriter = GeomVertexWriter(vdata, 'texcoord')
    else:
      cWriter = GeomVertexWriter(vdata, 'color')
    
    #On attrape les couleurs pour chaque sommet
    if forceCouleur==None:
      c1,t1=self.couleurSommet(p1)
      c2,t2=self.couleurSommet(p2)
      c3,t3=self.couleurSommet(p3)
    else:
      c1,t1 = forceCouleur
      c2,t2 = forceCouleur
      c3,t3 = forceCouleur

    #On calcule les normales à chaque sommet
    n1=self.calculNormale(p1)
    n2=self.calculNormale(p2)
    n3=self.calculNormale(p3)
    
    #On écrit le modèle dans cet ordre :
    #-vectrice
    #-normale
    #-texture | couleur
    #3 fois
    vWriter.addData3f(*p1)
    nWriter.addData3f(*n1)
    if general.TEXTURES:
      tWriter.addData2f(0,0)
    else:
      cWriter.addData4f(*c1)
    vWriter.addData3f(*p2)
    nWriter.addData3f(*n2)
    if general.TEXTURES:
      tWriter.addData2f(0,1)
    else:
      cWriter.addData4f(*c2)
    vWriter.addData3f(*p3)
    nWriter.addData3f(*n3)
    if general.TEXTURES:
      tWriter.addData2f(1,0)
    else:
      cWriter.addData4f(*c3)

    #On fabrique la géométrie
    prim = GeomTriangles(Geom.UHStatic)
    prim.addVertex(0)
    prim.addVertex(1)
    prim.addVertex(2)
    prim.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(prim)

    node = GeomNode('gnode')
    node.addGeom(geom)
    nd = NodePath(node)
    
    #On applique la texture
    tex = self.textureMixer(t1, t2, t3)
    nd.setTexture(tex)
    if general.configuration.getConfiguration("affichage-effets", "normalmapping","0")=="1":
      ts = TextureStage('ts')
      ts.setMode(TextureStage.MNormal)
      nd.setTexture(ts, tex)
      
    if general.gui.menuCourant !=None:
      if general.gui.menuCourant.miniMap !=None:
        general.gui.menuCourant.miniMap.dessineCarte(p1,p2,p3,c1,c2,c3)
      
    return nd
    
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
