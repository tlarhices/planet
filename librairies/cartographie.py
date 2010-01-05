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
import ImageFilter
import Image

class Cartographie:
  """Contient toute la gestion des cartes 2D"""
  miniMap = None
  heightMap = None
  
  def __init__(self):
    """Gère les cartes 2D"""
    self.miniMap = None
    self.heightMap = None

  def triangleVersCarte(self, p1, p2, p3, taille=None):
    if taille == None:
      taille = 0.2
    p1=self.point3DVersCarte(p1, taille)
    p2=self.point3DVersCarte(p2, taille)
    p3=self.point3DVersCarte(p3, taille)
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
    
  def point3DVersCarte(self, point, taille):
    general.TODO("voir pourquoi type=1 fait des jolies cartes et un mauvais texturage alors que type=0 a un texturage parfait, mais des cartes moches")
    
    type=1
    
    x, y, z = point
    tx, ty = taille
   
    if type==0:
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
    
  def carteVersPoint3D(self, point):
    if point==None:
      return None
      
    lat, z = point
    z=-(float(z)-float(self.tailleMiniMapY)/2)/(float(self.tailleMiniMapY)/2)
    
    lat = float(lat)*(2*math.pi)/float(self.tailleMiniMapX)
    x=math.cos(lat)
    y=math.sin(lat)
    if z==1.0 or z==-1.0:
      x=0.0
      y=0.0
    return (x, y, z)


  def calculHeightMap(self, listeElements=None):
    tailleHeightMap = 800
    if self.heightMap == None:
      self.heightMap = Image.new(mode="RGB",size=(tailleHeightMap, tailleHeightMap),color=(0,0,0))
    image = self.heightMap
    draw  =  ImageDraw.Draw(image)
    
    if listeElements==None:
      listeElements=general.planete.geoide.elements
      
    """def procedeElement(element, taille, draw):
      s1,s2,s3 = element.sommets
      s1=general.planete.geoide.sommets[s1]
      s2=general.planete.geoide.sommets[s2]
      s3=general.planete.geoide.sommets[s3]
      c1 = (max(general.planete.geoide.niveauEau, min(1.0+general.planete.geoide.delta, s1.length()))-1.0)/(general.planete.geoide.delta+general.planete.geoide.niveauEau-1.0)
      c2 = (max(general.planete.geoide.niveauEau, min(1.0+general.planete.geoide.delta, s1.length()))-1.0)/(general.planete.geoide.delta+general.planete.geoide.niveauEau-1.0)
      c3 = (max(general.planete.geoide.niveauEau, min(1.0+general.planete.geoide.delta, s1.length()))-1.0)/(general.planete.geoide.delta+general.planete.geoide.niveauEau-1.0)
      a1,a2,a3 = self.triangleVersCarte(s1, s2, s3, tailleHeightMap)
      a1 = a1[0], a1[1]
      a2 = a2[0], a2[1]
      a3 = a3[0], a3[1]
      c = int((c1+c2+c3)/3*255)
      draw.polygon((a1,a2,a3), fill=(c,c,c), outline=None)
      
      if element.enfants!=None:
        for element2 in element.enfants:
          procedeElement(element2, taille, draw)"""
          
    cpt = 0
    for element in listeElements:
      general.planete.afficheTexte("Rendu de la heightmap : %.2f%%" %((cpt*1.0)/len(listeElements)*100))
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
      a1,a2,a3 = self.triangleVersCarte(p1, p2, p3, taille)
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
            general.planete.afficheTexte("Rendu de la minimap : %.2f%%" %((compte*1.0)/len(listeElements)*100))
          compte+=1
          self.procedeRenduElement(element, taille, draw, False)
    del draw
    """for i in range(0, 1):
      image = image.filter(ImageFilter.BLUR)"""
    image.save(os.path.join(".","data","cache","minimap.png"), "PNG")
    #image.show()
    
  def dessineCarte(self, p1, p2, p3, c1, c2, c3, taille, carteDure, carteFloue):
    minx = min(p1[0], p2[0], p3[0])
    maxx = max(p1[0], p2[0], p3[0])
    miny = min(p1[1], p2[1], p3[1])
    maxy = max(p1[1], p2[1], p3[1])
    taille = float(taille)
    
    def signe(p1, p2, p3):
      return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1]);
    def estDansTriangle(pt, s1, s2, s3):
      b1 = signe(pt, s1, s2) < 0.0
      b2 = signe(pt, s2, s3) < 0.0
      b3 = signe(pt, s3, s1) < 0.0
      return ((b1 == b2) and (b2 == b3))
    
    #Test des points à cheval sur les bords, s'il y en a, on dessine 2 triangles qui débordent de chaque coté de la carte
    if maxx-minx>float(taille)*2.0/3.0:
      p1min = Vec2(p1)
      p2min = Vec2(p2)
      p3min = Vec2(p3)
      if p1min[0]<taille/2.0:
        p1min[0]=p1min[0]+taille
      if p2min[0]<taille/2.0:
        p2min[0]=p2min[0]+taille
      if p3min[0]<taille/2.0:
        p3min[0]=p3min[0]+taille
      
      if p1!=p1min or p2!=p2min or p3!=p3min:
        self.dessineCarte(p1min, p2min, p3min, c1, c2, c3, taille, carteDure, carteFloue)

      p1max = Vec2(p1)
      p2max = Vec2(p2)
      p3max = Vec2(p3)
      if p1max[0]>taille/2.0:
        p1max[0]=p1max[0]-taille
      if p2max[0]>taille/2.0:
        p2max[0]=p2max[0]-taille
      if p3max[0]>taille/2.0:
        p3max[0]=p3max[0]-taille
      
      if p1!=p1max or p2!=p2max or p3!=p3max:
        self.dessineCarte(p1max, p2max, p3max, c1, c2, c3, taille, carteDure, carteFloue)
      return
      
    if maxy-miny>taille*2.0/3.0:
      p1min = Vec2(p1)
      p2min = Vec2(p2)
      p3min = Vec2(p3)
      if p1min[1]<taille/2.0:
        p1min[1]=p1min[1]+taille
      if p2min[1]<taille/2.0:
        p2min[1]=p2min[1]+taille
      if p3min[1]<taille/2.0:
        p3min[1]=p3min[1]+taille
      print p1,p2,p3,"min ->", p1min, p2min, p3min
      if p1!=p1min or p2!=p2min or p3!=p3min:
        self.dessineCarte(p1min, p2min, p3min, c1, c2, c3, taille, carteDure, carteFloue)

      p1max = Vec2(p1)
      p2max = Vec2(p2)
      p3max = Vec2(p3)
      if p1max[1]>taille/2.0:
        p1max[1]=p1max[1]-taille
      if p2max[1]>taille/2.0:
        p2max[1]=p2max[1]-taille
      if p3max[1]>taille/2.0:
        p3max[1]=p3max[1]-taille
      print p1,p2,p3,"max ->", p1max, p2max, p3max
      if p1!=p1max or p2!=p2max or p3!=p3max:
        self.dessineCarte(p1max, p2max, p3max, c1, c2, c3, taille, carteDure, carteFloue)
      return
      
      
    #Dessine le triangle
    for x in range(int(minx+0.5), int(maxx+0.5)):
      if x in range(0, int(taille)):
        for y in range(int(miny+0.5), int(maxy+0.5)):
          if y in range(0, int(taille)):
            d1=(Vec2(x,y)-Vec2(p1[0], p1[1])).length()
            d2=(Vec2(x,y)-Vec2(p2[0], p2[1])).length()
            d3=(Vec2(x,y)-Vec2(p3[0], p3[1])).length()
            fact=(d1+d2+d3)/2
            d1=1-d1/fact
            d2=1-d2/fact
            d3=1-d3/fact
            couleur=c1[0]*d1+c2[0]*d2+c3[0]*d3, c1[1]*d1+c2[1]*d2+c3[1]*d3, c1[2]*d1+c2[2]*d2+c3[2]*d3
            carteFloue.setXel(x, y, couleur[0], couleur[1], couleur[2])
            if estDansTriangle((x,y),p1,p2,p3):
                carteDure.setXel(x, y, couleur[0], couleur[1], couleur[2])
                self.carteARedessiner = True