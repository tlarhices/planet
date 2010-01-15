#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general
import math
import os

from pandac.PandaModules import *

import ImageDraw
import ImageMath
import ImageFilter
import Image

class Cartographie:
  """Contient toute la gestion des cartes 2D"""
  miniMap = None
  heightMap = None
  zoneOmbre = None
  
  def __init__(self):
    """Gère les cartes 2D"""
    self.miniMap = None
    self.heightMap = None
    self.zoneOmbre = None

  def triangleVersCarte(self, p1, p2, p3, taille=None, coordonneesTexturage=False):
    if taille == None:
      taille = 0.2
    p1=self.point3DVersCarte(p1, taille, coordonneesTexturage)
    p2=self.point3DVersCarte(p2, taille, coordonneesTexturage)
    p3=self.point3DVersCarte(p3, taille, coordonneesTexturage)
    tx, ty = taille
    
    test=False
    while not test:
      test=True
      minx=min(p1[0], p2[0], p3[0])
      maxx=max(p1[0], p2[0], p3[0])
      miny=min(p1[1], p2[1], p3[1])
      maxy=max(p1[1], p2[1], p3[1])
      
      if maxx-minx>tx*2.0/3.0:
        test=False
        if p1[0]==minx:
          p1[0]=p1[0]+tx
        if p2[0]==minx:
          p2[0]=p2[0]+tx
        if p3[0]==minx:
          p3[0]=p3[0]+tx
      if maxy-miny>ty*2.0/3.0:
        test=False
        if p1[1]==miny:
          p1[1]=p1[1]+tz
        if p2[1]==miny:
          p2[1]=p2[1]+tz
        if p3[1]==miny:
          p3[1]=p3[1]+tz
    
    return p1, p2, p3
    
  def point3DVersCarte(self, point, taille, coordonneesTexturage=False):
    general.TODO("voir pourquoi type=1 fait des jolies cartes et un mauvais texturage alors que type=0 a un texturage parfait, mais des cartes moches")
    
    x, y, z = point
    tx, ty = taille
   
    if coordonneesTexturage:
      r = math.sqrt((x*x) + (y*y))
      radiansLatitude = math.atan2(r,z)
      v = 1 - (radiansLatitude / (math.pi))
     
      radiansLongitude = math.atan2(y,x)
      u = 1 + (radiansLongitude / (2 * math.pi))
      return Vec2(u*tx,v*ty)
    
    point = Vec3(point)
    point.normalize()
    x,y,z = point
    lon = math.acos(z)
    
    tmp = Vec2(x,y)
    tmp.normalize()
    x,y=tmp
    
    if x==0.0 and y==0.0:
      lat=0.0
    elif y>=0:
      if x==0:
        lat=math.acos(0.0)
      else:
        lat=math.acos(x/math.sqrt(x*x+y*y))
    else:
      lat=2 * math.pi - math.acos(x/math.sqrt(x*x+y*y))
    lat=lat*tx/(2*math.pi)
    
    z=(-z*ty/2+ty/2)
    return Vec2(lat, z)
    
  def carteVersPoint3D(self, point, taille):
    if point==None:
      return None
      
    tx, ty = taille
      
    lat, z = point
    z=-(float(z)-float(ty)/2)/(float(ty)/2)
    
    lat = float(lat)*(2*math.pi)/float(tx)
    x=math.cos(lat)
    y=math.sin(lat)
    if z==1.0 or z==-1.0:
      x=0.0
      y=0.0
    return (x, y, z)

  def calculZoneOmbre(self, taille, listeElements=None):
    if self.zoneOmbre == None:
      self.zoneOmbre = Image.new(mode="RGB",size=taille,color=(0,0,0))
    image = self.zoneOmbre
    draw  =  ImageDraw.Draw(image)
    
    if general.interface.menuCourant:
      if general.interface.menuCourant.miniMap and general.planete.soleil:
        
        if listeElements == None:
          listeElements = general.planete.geoide.elements
    
        def procFace(face):
          if face.enfants:
            return True
          jour = Vec3(1.0,1.0,1.0)
          nuit = Vec3(0.2,0.2,0.4)
          p1 = Vec3(general.planete.geoide.sommets[face.sommets[0]])
          p1.normalize()
          p1 = p1 * 1.0001
          if general.ligneCroiseSphere(p1, general.planete.soleil.getPos(), Vec3(0.0,0.0,0.0), 1.0) != None:
            c1=nuit
          else:
            c1=jour
          p2 = Vec3(general.planete.geoide.sommets[face.sommets[1]])
          p2.normalize()
          p2 = p2 * 1.0001
          if general.ligneCroiseSphere(p2, general.planete.soleil.getPos(), Vec3(0.0,0.0,0.0), 1.0) != None:
            c2=nuit
          else:
            c2=jour
          p3 = Vec3(general.planete.geoide.sommets[face.sommets[2]])
          p3.normalize()
          p3 = p3 * 1.0001
          if general.ligneCroiseSphere(p3, general.planete.soleil.getPos(), Vec3(0.0,0.0,0.0), 1.0) != None:
            c3=nuit
          else:
            c3=jour
            
          c = (c1+c2+c3)/3
          c = int(c[0]*255+0.5), int(c[1]*255+0.5), int(c[2]*255+0.5)
          
          a1,a2,a3 = self.triangleVersCarte(p1, p2, p3, taille, coordonneesTexturage=False)
          a1 = int(a1[0]+0.5), int(a1[1]+0.5)
          a2 = int(a2[0]+0.5), int(a2[1]+0.5)
          a3 = int(a3[0]+0.5), int(a3[1]+0.5)
          draw.polygon((a1,a2,a3), fill=c, outline=None)
          return True
          
        def recur(face):
          if procFace(face):
            if face.enfants != None:
              for enfant in face.enfants:
                recur(enfant)
        for face in listeElements:
          recur(face)
    image.save(os.path.join(".","data","cache","zoneombre.png"), "PNG")
    general.miniMapAchangee = True
    if self.miniMap != None:
      out = ImageMath.eval("int(float(a) * float(b))", a=self.miniMap, b=image)
      out.save(os.path.join(".","data","cache","minimapombre.png"), "PNG")

  def calculHeightMap(self, listeElements=None):
    tailleHeightMap = 800
    if self.heightMap == None:
      self.heightMap = Image.new(mode="RGB",size=(tailleHeightMap, tailleHeightMap),color=(0,0,0))
    image = self.heightMap
    draw  =  ImageDraw.Draw(image)
    
    if listeElements==None:
      listeElements=general.planete.geoide.elements
          
    cpt = 0
    for element in listeElements:
      general.planete.afficheTexte("Rendu de la heightmap : %(a).2f%%", parametres={"a": (cpt*1.0)/len(listeElements)*100}, type="carte")
      self.procedeRenduElement(element, (tailleHeightMap, tailleHeightMap), draw, True)
      cpt+=1

    del draw
    image.save(os.path.join(".","data","cache","zoneherbe.png"), "PNG")
    import ImageEnhance
    enhancer = ImageEnhance.Contrast(image)
    for i in range(0, 5):
      image = enhancer.enhance(2.0)
    image.save(os.path.join(".","data","cache","zoneneige.png"), "PNG")
    
  def procedeRenduElement(self, element, taille, draw, heightMap):
    if element.enfants!=None:
      for element2 in element.enfants:
        self.procedeRenduElement(element2, taille, draw, heightMap)
    else:
      p1,p2,p3 = element.sommets
      p1=general.planete.geoide.sommets[p1]
      p2=general.planete.geoide.sommets[p2]
      p3=general.planete.geoide.sommets[p3]
      if not heightMap:
        c1 = element.couleurSommet(p1)[0]
        c2 = element.couleurSommet(p2)[0]
        c3 = element.couleurSommet(p3)[0]
      else:
        c1 = (max(general.planete.geoide.niveauEau, min(1.0+general.planete.geoide.delta, p1.length()))-1.0)/(general.planete.geoide.delta+general.planete.geoide.niveauEau-1.0)
        c2 = (max(general.planete.geoide.niveauEau, min(1.0+general.planete.geoide.delta, p2.length()))-1.0)/(general.planete.geoide.delta+general.planete.geoide.niveauEau-1.0)
        c3 = (max(general.planete.geoide.niveauEau, min(1.0+general.planete.geoide.delta, p3.length()))-1.0)/(general.planete.geoide.delta+general.planete.geoide.niveauEau-1.0)
      c = (Vec4(c1)+Vec4(c2)+Vec4(c3))/3.0
      c = int(c[0]*255), int(c[1]*255), int(c[2]*255)
      a1,a2,a3 = self.triangleVersCarte(p1, p2, p3, taille, coordonneesTexturage=heightMap)
      a1 = int(a1[0]+0.5), int(a1[1]+0.5)
      a2 = int(a2[0]+0.5), int(a2[1]+0.5)
      a3 = int(a3[0]+0.5), int(a3[1]+0.5)
      draw.polygon((a1,a2,a3), fill=c, outline=None)
  
  def calculMiniMap(self, taille, listeElements=None):
    if self.miniMap == None:
      self.miniMap = Image.new(mode="RGB",size=taille,color=(0,0,0))
    image = self.miniMap
    draw  =  ImageDraw.Draw(image)

    if general.interface.menuCourant !=None:
      if general.interface.menuCourant.miniMap !=None:
        
        if listeElements == None:
          listeElements = general.planete.geoide.elements
          
        compte=0
        for element in listeElements:
          if listeElements == general.planete.geoide.elements:
            general.planete.afficheTexte("Rendu de la minimap : %(a).2f%%", parametres={"a": (compte*1.0)/len(listeElements)*100}, type="carte")
          compte+=1
          self.procedeRenduElement(element, taille, draw, False)
    del draw
    """for i in range(0, 1):
      image = image.filter(ImageFilter.BLUR)"""
    image.save(os.path.join(".","data","cache","minimap.png"), "PNG")
    general.miniMapAchangee = True
    #image.show()