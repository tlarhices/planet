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

from element import *
from ai import *
from pandaui import *
from i18n import *
from sprite import *

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
  
  aiNavigation = None #Le bout d'AI qui contient le graphe de navigation qui est commun a toute entité de la planète
  sprites = None #La liste des objets du monde dérivant de la classe sprite
  joueurs = None
  
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
    self.gui = GUI(i18n(None, "fr"), "./data/gui")
    
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
        self.ajouteNoeud(sommet, face.sommets[0])
        self.ajouteNoeud(sommet, face.sommets[1])
        self.ajouteNoeud(sommet, face.sommets[2])
    if general.DEBUG_GENERE_PLANETE:
      self.afficheTexte(None)
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
    self.sprites = []
    self.joueurs = []
  # Fin Initialisation -------------------------------------------------
    
  def afficheTexte(self, texte):
    """Affiche le texte sur l'écran, si texte==None, alors efface le dernier texte affiché"""
    self.gui.purge(section="afficheTexte")
    if texte!=None:
      print texte
      self.gui.ajouteComposant(Titre(gui=self.gui, texte=texte), section="afficheTexte")
    else:
      print "Fin"
    base.graphicsEngine.renderFrame()
    base.graphicsEngine.renderFrame()
    
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

      #On tesselate la sphère courante
      for i in range(last, self.tesselation):
        cpt=0.0
        tot=len(self.elements)
        for element in self.elements:
          cpt+=1
          if general.DEBUG_GENERE_PLANETE:
            self.afficheTexte("Tesselation en cours... %i/%i::%i/%i" %(i+1, self.tesselation, cpt, tot))
          element.tesselate()
        #On sauvegarde la tesselation courante pour gagner du temps pour les prochains chargements
        self.sauvegarde(os.path.join(".","data","pre-tesselate",str(i+1)), i+1)
      if general.DEBUG_GENERE_PLANETE:
        self.afficheTexte(None)
        
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
    
    sommet = random.choice(self.sommets)
    
    self.afficheTexte(None)
    
    general.stopChrono("Planete::fabriqueNouvellePlanete")
    
    
  def fabriqueSphere(self):
    """fabrique un icohèdre régulier de rayon 1.0"""
    general.startChrono("Planete::fabriqueSphere")
    t=(1.0+math.sqrt(5.0))/2.0
    tau=t/math.sqrt(1.0+t*t)
    one=1.0/math.sqrt(1.0+t*t)
    
    #Sommets
    ZA = general.normaliseVecteur([tau, one, 0])
    ZB = general.normaliseVecteur([-tau, one, 0])
    ZC = general.normaliseVecteur([-tau, -one, 0])
    ZD = general.normaliseVecteur([tau, -one, 0])
    YA = general.normaliseVecteur([one, 0 , tau])
    YB = general.normaliseVecteur([one, 0 , -tau])
    YC = general.normaliseVecteur([-one, 0 , -tau])
    YD = general.normaliseVecteur([-one, 0 , tau])
    XA = general.normaliseVecteur([0 , tau, one])
    XB = general.normaliseVecteur([0 , -tau, one])
    XC = general.normaliseVecteur([0 , -tau, -one])
    XD = general.normaliseVecteur([0 , tau, -one])
    
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
      self.sommets[i] = general.multiplieVecteur(self.sommets[i], rn)
        
    if general.DEBUG_GENERE_PLANETE:
      self.afficheTexte(None)
    general.stopChrono("Planete::fabriqueSol")
      
  def normaliseSol(self):
    """
    Étend la gamme des valeurs aléatoires pour les ramener dans l'échelle [1.0-delta;1.0+delta]
    """
    general.startChrono("Planete::normaliseSol")
    if general.DEBUG_GENERE_PLANETE:
      self.afficheTexte("Normalisation...")
    A=general.normeVecteur(self.sommets[0])
    B=A
    
    for sommet in self.sommets:
      A = min(A, general.normeVecteur(sommet))
      B = max(B, general.normeVecteur(sommet))
      
    C=1.0-self.delta
    D=1.0+self.delta
    
    facteur = (B-A)/(D-C)
    
    totlen= len(self.sommets)
    for i in range(0, len(self.sommets)):
      if general.DEBUG_GENERE_PLANETE:
        if i%250==0:
          self.afficheTexte("Normalisation... %i/%i" %(i, totlen))
      V=general.normeVecteur(self.sommets[i])
      V=(V-A)/facteur+C
      self.sommets[i]=general.multiplieVecteur(general.normaliseVecteur(self.sommets[i]), V)
      
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
      
      tot = general.normeVecteur(self.sommets[sommet])*4
      for id in voisins:
        tot += general.normeVecteur(self.sommets[id])
      tot = tot / (len(voisins)+4)
      self.sommets[sommet] = general.multiplieVecteur(general.normaliseVecteur(self.sommets[sommet]),tot)
    if general.DEBUG_GENERE_PLANETE:
      self.afficheTexte(None)
    general.stopChrono("Planete::flouifieSol")
      
  def fabriqueModel(self):
    """Produit un modèle 3D à partir du nuage des faces"""
    general.startChrono("Planete::fabriqueModel")
    
    #Place une sphère à la place de la planète pendant la construction
    tmp = loader.loadModel("data/modeles/sphere.egg")
    tmp.reparentTo(render)
    tmp.setColor(0.0, 0.0, 0.8, 1.0)
    tmp.setScale(1.0+self.delta)
    tmp.setLightOff()
    
    cpt=0.0
    totlen = len(self.elements)
    #Dessine les triangles
    for element in self.elements:
      cpt+=1.0
      if general.DEBUG_GENERE_PLANETE:
        self.afficheTexte("Création du modèle... %i/%i" %(cpt, totlen))
      #Ce sont les faces qui vont se charger de faire le modèle pour nous
      element.fabriqueModel()
      
    #Retire la sphère temporaire
    tmp.detachNode()
    tmp.removeNode()
      
    #On ajoute l'eau
    self.fabriqueEau()
    #On ajoute le ciel
    self.fabriqueCiel()

    if general.DEBUG_GENERE_PLANETE:
      self.afficheTexte(None)
      
    general.stopChrono("Planete::fabriqueModel")

  def fabriqueEau(self):
    """Ajoute une sphère qui représente l'eau"""
    general.startChrono("Planete::fabriqueEau")
    
    #Crée le modèle de l'eau
    self.modeleEau = loader.loadModel("data/modeles/sphere.egg")
    self.modeleEau.reparentTo(self.racine)
    self.modeleEau.setTransparency(TransparencyAttrib.MAlpha )
    #self.modeleEau.setColor(0.0,0.1,0.3,1.0)
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
    general.startChrono("Planete::fabriqueCiel")
    
    #Crée le modèle du ciel
    self.modeleCiel = NodePath("ciel")
    self.modeleCiel.reparentTo(self.racine)
    self.niveauCiel = 1.0+self.delta*1.25+0.0001
    
    nuages = NodePath("nuage")
    for i in range(0, 30):
      a = Nuage(self)
      a.fabriqueModel().reparentTo(nuages)
    nuages.reparentTo(self.modeleCiel)
      
    #Fabrique une lumière ambiante pour que la nuit soit moins noire
    alight = AmbientLight('alight')
    alight.setColor(VBase4(0.2, 0.2, 0.275, 1))
    alnp = render.attachNewNode(alight)
    render.setLight(alnp)
    
    #Ciel bleu
    azure = loader.loadModel("data/modeles/sphere.egg")
    azure.setTransparency(TransparencyAttrib.MDual )
    azure.setColor(0.6, 0.6, 1.0, 1.0)
    azure.setTwoSided(False)
    azure.setScale((self.niveauCiel+0.001+0.0001))
    azure.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
    azure.reparentTo(self.modeleCiel)
    #L'azure n'est pas affectée par la lumière ambiante
    azure.setLightOff(alnp)
    
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
    etoiles.setScale((float(general.configuration.getConfiguration("generationPlanete", "distanceSoleil","10.0"))*3.0/2.0))
    etoiles.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
    etoiles.reparentTo(self.modeleCiel)    
    etoiles.setLightOff()
    
    self.modeleCiel.setPythonTag("type","ciel")
    
    #On coupe la collision avec le ciel pour pas qu'on détecte de clics sur le ciel
    self.modeleCiel.setCollideMask(BitMask32.allOff())
    general.stopChrono("Planete::fabriqueCiel")

  # Fin Constructions géométriques -------------------------------------
      
  # Import / Export ----------------------------------------------------
  def sauvegarde(self, fichier, tess=None):
    general.startChrono("Planete::sauvegarde")
    """Sauvegarde le géoïde dans un fichier"""
    if tess==None:
      tess = self.tesselation
      
    fichier = open(fichier, "w")
    fichier.write("Z:"+str(tess)+":\r\n")
    
    for point in self.sommets:
      fichier.write("P:"+str(point[0])+":"+str(point[1])+":"+str(point[2])+":\r\n")
    for element in self.elements:
      fichier.write(element.sauvegarde())
    for joueur in self.joueurs:
      fichier.write(joueur.sauvegarde())
    fichier.close()
    general.stopChrono("Planete::sauvegarde")
    
  def charge(self, fichier, simple=False):
    """Charge le géoïde depuis un fichier"""
    general.startChrono("Planete::charge")
    if general.DEBUG_CHARGE_PLANETE:
      self.afficheTexte("Chargement de la planète...")
    fichier = open(fichier)
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
    lignes = fichier.readlines()

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
      if type=="z":
        #Attrapage des infos de tesselation
        self.tesselation = int(elements[0])
      elif type=="p":
        #Création d'un sommet
        self.sommets.append([float(elements[0]), float(elements[1]), float(elements[2])])
      elif type=="t":
        #Création d'une face
        ids = elements[0].replace("[","").split("]")
        if len(ids)<2:
          print
          print "Erreur ID", ids
        elif len(ids)==2:
          self.elements.append(Element("["+str(ids[0])+"]", int(elements[1]), int(elements[2]), int(elements[3]), self, 0, None))
        else:
          self.elements[int(ids[0])].charge(ids[1:], elements[1], elements[2], elements[3])
      elif type=="nj":
        #Création d'un joueur
        print "TODO"
        #inutile, position, modele, inutile2 = elements
        #position = general.floatise(position.replace("(","").replace(")","").split(","))
        #self.sprites.append(Sprite(position, modele, self))
      elif type=="ij":
        #Informations d'un joueur
        print "TODO"
      else:
        print
        print "Avertissement : Planete::charge, type de ligne inconnue :", type,"sur la ligne :\r\n",ligne.strip()
        
    if general.DEBUG_CHARGE_PLANETE:
      self.afficheTexte("Chargement des sommets... %i sommets chargés" %(len(self.sommets)))
    if general.DEBUG_CHARGE_PLANETE:
      self.afficheTexte(None)
    fichier.close()
    
    if not simple:
      self.fabriqueVoisinage()
      
      #On ajoute le gestionnaire d'intelligence artificielle
      self.aiNavigation = AINavigation(self)
      self.aiNavigation.grapheDeplacement()
    general.stopChrono("Planete::charge")
  # Fin Import / Export ------------------------------------------------
      
  # Mise à jour --------------------------------------------------------
  def ping(self, temps):
    general.startChrono("Planete::ping")
    """Fonction appelée a chaque image, temps indique le temps écoulé depuis l'image précédente"""
    
    #Regarde s'il faut optimiser le modèle 3D, passe au minimum (apr défaut) 3 secondes après la dernière modification du modèle
    dureeOptimise = float(general.configuration.getConfiguration("generationPlanete","duree-optimisation",3.0))
    for element in self.elements:
      if element.besoinOptimise:
        element.pileOptimise+=temps
        if element.pileOptimise > dureeOptimise:
          element.fabriqueModel(optimise=True)
      
    #Met à jour l'état des joueurs
    for joueur in self.joueurs:
      joueur.ping(temps)
      
    #Met à jour les états des sprites
    for sprite in self.sprites:
      sprite.ping(temps)
    general.stopChrono("Planete::ping")
  # Fin Mise à jour ----------------------------------------------------
        
  # Fonctions diverses -------------------------------------------------
  def trouveSommet(self, point):
    """
    Retourne le sommet le plus proche
    point : le point à rechercher
    """
    general.startChrono("Planete::trouveSommet")
    dst = general.distanceCarree(point, self.sommets[0])
    id = 0
    for s in self.sommets:
      d = general.distanceCarree(point, s)
      if dst > d:
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
    cible = general.normaliseVecteur(point)
    
    #On initialise a des valeurs stupides
    f = None
    d1, d2, d3 = 10, 10, 10
    for face in faces:
      tri = face.sommets
      #On fait des comparaisons, pas du travail sur des valeurs exactes, donc on utilise le carré pour gagner le temps du sqrt
      da = general.distanceCarree(cible, general.normaliseVecteur(self.sommets[tri[0]]))
      db = general.distanceCarree(cible, general.normaliseVecteur(self.sommets[tri[1]]))
      dc = general.distanceCarree(cible, general.normaliseVecteur(self.sommets[tri[2]]))
      
      #Si on a une plus proche, elle remplace la meilleure
      if math.sqrt(da*da+db*db+dc*dc) < math.sqrt(d1*d1+d2*d2+d3*d3):
        d1, d2, d3 = da, db, dc
        f = face
    general.stopChrono("Planete::trouveFace")
    return f.sommets
    ## ------------ Version avec self.sommetDansFace
        
    ## ------------ Version avec self.elements
    #Si on a pas de liste de faces, on utilise la liste complète de la planète
    if sub==None:
      sub = self.elements
    cible = general.normaliseVecteur(point)
    
    #On initialise a des valeurs stupides
    f = None
    d1, d2, d3 = 10, 10, 10
    
    #On teste toutes les facettes de l'ensemble
    for tria in sub:
      tri = tria.sommets
      #On fait des comparaisons, pas du travail sur des valeurs exactes, donc on utilise le carré pour gagner le temps du sqrt
      da = general.distanceCarree(cible, general.normaliseVecteur(self.sommets[tri[0]]))
      db = general.distanceCarree(cible, general.normaliseVecteur(self.sommets[tri[1]]))
      dc = general.distanceCarree(cible, general.normaliseVecteur(self.sommets[tri[2]]))
      
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
    return f.sommets
    ## ------------ Version avec self.elements
    
    ## ------------ Version avec testIntersectionTriangleDroite
    #Si on a pas de liste de faces, on utilise la liste complète de la planète
    if sub==None:
      sub = self.elements
    cible = general.multiplieVecteur(general.normaliseVecteur(point), 100)
    
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
          return tri
    general.stopChrono("Planete::trouveFace")
    return None
    ## ------------ Version avec testIntersectionTriangleDroite
    
  def altitude(self, point):
    """Retourne l'altitude (rayon) à laquelle le point devrait se trouver pour être juste sur la face en dessous (au dessus) de lui (coord cartésiennes)"""
    general.startChrono("Planete::altitude")
    #Cherche la face dans laquelle se trouve le point
    face = self.trouveFace(point)
    if face==None:
      #La droite passant par un point quelconque et le centre de la sphère coupe obligatoirement la dite sphère en un point
      #Ne pas avoir de résultat dit que ça bug
      print "Bug :: testIntersectionTriangleDroite déconne"
      return general.normeVecteur(point)
    pt1, pt2, pt3 = self.sommets[face[0]], self.sommets[face[1]], self.sommets[face[2]]
    #Calcul des distances pour pondérer la position du point
    #On utilise le carré pour gagner des sqrt
    d1 = general.distanceCarree(general.normaliseVecteurCarre(pt1), general.normaliseVecteurCarre(point))
    d2 = general.distanceCarree(general.normaliseVecteurCarre(pt2), general.normaliseVecteurCarre(point))
    d3 = general.distanceCarree(general.normaliseVecteurCarre(pt3), general.normaliseVecteurCarre(point))
    d=d1+d2+d3
    d1=d1/d
    d2=d2/d
    d3=d3/d
    #Attrape les altitude de chaque sommet
    r1=general.normeVecteurCarre(pt1)
    r2=general.normeVecteurCarre(pt2)
    r3=general.normeVecteurCarre(pt3)
    
    general.stopChrono("Planete::altitude")
    #Calcule l'altitude moyenne pondérée
    return r1*d1+r2*d2+r3*d3
    
  def placeSurSol(self, point):
    """Déplace le point pour qu'il soit juste sur la surface de la facette (coord cartésiennes)"""
    return general.multiplieVecteur(general.normaliseVecteur(point), self.altitude(point))

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
    self.sommets[idx] = general.floatise(newCoord)
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
    norme = general.normeVecteur(self.sommets[idx])
    self.changeCoordPoint(self.sommets[idx], general.multiplieVecteur(general.normaliseVecteur(self.sommets[idx]), norme+delta))
    general.stopChrono("Planete::elevePoint")
    
  def ajouteJoueur(self, joueur):
    print joueur.nom,"est entré dans la partie"
    self.joueurs.append(joueur)
  # Fin Fonctions diverses ---------------------------------------------
