#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general

import math
import random
import sys

from pandac.PandaModules import *

class AINavigation:
  #Classe qui gère la navigation sur la surface de la planète
  graph = None #Le graph de navigation
  planete = None #L'instance de la planète
  maxcout = 100000000 #Ce coût veut dire que c'est impossible
  angleSolMax = None

  def __init__(self, planete):
    self.planete = planete
    self.angleSolMax = float(general.configuration.getConfiguration("ai","navigation", "angleSolMax","70.0"))
    
  # Création d'infos ---------------------------------------------------    
  def coutPassage(self, idxSommet1, idxSommet2):
    """Retourne le cout necessaire pour passer du sommet idxSommet1 au sommet idxSommet2"""
    #cout = (general.normeVecteur(self.planete.sommets[idxSommet2]) - general.normeVecteur(self.planete.sommets[idxSommet1]))*100
    
    sp = Vec3(*general.normaliseVecteur(self.planete.sommets[idxSommet1]))
    fc = Vec3(*self.planete.trouveFace(self.planete.sommets[idxSommet2]).calculNormale())
    angle = sp.angleDeg(fc)
    
    if angle >= self.angleSolMax or angle <= -self.angleSolMax:
      angle = self.maxcout
      
    #navigation = NodePath("nav")
    #navigation.reparentTo(self.planete.racine)
    #On ne peut pas passer sous l'eau
    if general.normeVecteur(self.planete.sommets[idxSommet2]) < self.planete.niveauEau or general.normeVecteur(self.planete.sommets[idxSommet1]) < self.planete.niveauEau:
      cout = self.maxcout
    #  navigation.attachNewNode(self.dessineLigne((0.0, 0.0, 1.0), general.multiplieVecteur(self.planete.sommets[idxSommet1], 1.25), general.multiplieVecteur(self.planete.sommets[idxSommet2], 1.25)))
    #elif angle==self.maxcout:
    #  navigation.attachNewNode(self.dessineLigne((1.0, 0.0, 0.0), general.multiplieVecteur(self.planete.sommets[idxSommet1], 1.25), general.multiplieVecteur(self.planete.sommets[idxSommet2], 1.25)))
    #else:
    #  navigation.attachNewNode(self.dessineLigne((0.0, 1.0, 0.0), general.multiplieVecteur(self.planete.sommets[idxSommet1], 1.25), general.multiplieVecteur(self.planete.sommets[idxSommet2], 1.25)))
    return angle
    
  def dessineLigne(self, couleur, depart, arrivee):
    """Dessine une ligne de depart vers arrivée et ne fait pas de doublons"""
    ls = LineSegs()
    ls.setColor(*couleur)
    ls.setThickness(1.0)
    ls.moveTo(*depart)
    ls.drawTo(*arrivee)
    return ls.create()
    
  def grapheDeplacement(self):
    """
    Fabrique le graphe de deplacement de la planète
    graph[sommet de départ]=[(sommet accessible 1, cout pour y aller), (sommet accessible 2, cout pour y aller), ...]
    """
    general.startChrono("AINavigation::grapheDeplacement")
    cpt=0.0
    self.graph = {}
    
    totclef = len(self.planete.voisinage.keys())
    
    for source in self.planete.voisinage.keys():
      if general.DEBUG_AI_GRAPHE_DEPLACEMENT_CONSTRUCTION:
        if cpt%250==0:
          self.planete.afficheTexte("Création du graphe de déplacement... %i/%i" %(cpt,totclef))
      for voisin in self.planete.voisinage[source]:
        self.ajouteNoeud(source, voisin)
      cpt+=1.0
    general.stopChrono("AINavigation::grapheDeplacement")
    #test=None
    #a=None
    #b=None
    #while test==None:
    #  a = random.choice(self.graph.keys())
    #  b = random.choice(self.graph.keys())
    #  test = self.aStar(a, b)
    #print a,"->",b,":",test
        
  def ajouteNoeud(self, pt1, pt2):
    """Ajoute un noeud au graphe"""
    general.startChrono("AINavigation::ajouteNoeud")
    cout = self.coutPassage(pt1, pt2)
    if pt1 not in self.graph.keys():
      self.graph[pt1]=[]
    
    if (pt2, cout) not in self.graph[pt1]:
      self.graph[pt1].append((pt2, cout))
    general.stopChrono("AINavigation::ajouteNoeud")
      
  def maj(self, idxSommet):
    """
    Met à jour les données après modifications d'un sommet
    """
    general.startChrono("AINavigation::maj")
    voisins = self.graph[idxSommet][:]
    del self.graph[idxSommet]
    for voisin, cout in voisins:
      self.ajouteNoeud(idxSommet, voisin)
      newCout = self.coutPassage(voisin, idxSommet)
      valeurs = self.graph[voisin][:]
      for i in range(0, len(valeurs)):
        id, cout = valeurs[i]
        if id==idxSommet:
          valeurs[i] = (id, newCout)
      self.graph[voisin] = valeurs
    general.stopChrono("AINavigation::maj")
  # Fin création d'infos -----------------------------------------------
  
  # Recherche d'itinéraire ---------------------------------------------
  def aStar(self, deb, fin):
    """
    Calcule la trajectoire la plus courte allant du sommet deb vers le sommet fin selon le graphe self.graph
    Prend en compte les changements d'élévation et la présence d'eau.
    Retourne None s'il n'y a pas de chemin possible
    """
    general.startChrono("AINavigation::aStar")
    g={} #Le cout jusqu'à présent
    h={} #Le cout estimé jusqu'à la cible
    f={} #présent + cible
    promenade={} #La trace de la promenade
    fait = [] #Les sommets que l'on a déjà parcourus
    afaire = [deb] #Les sommets que l'on doit encore parcourir
    
    #Valeurs du point de départ
    g[deb] = 0 #On a pas bougé, donc ce cout vaut 0
    h[deb] = general.distanceCarree(self.planete.sommets[deb], self.planete.sommets[fin]) #L'estimation se fait selon la distance euclidienne (on utilise le carré car sqrt est trop lent et c'est juste pour une comparaison)
    f[deb] = g[deb]+h[deb] # == h[deb] ;)
    
    #On boucle tant que l'on a des sommets à parcourir
    while len(afaire) > 0:
      #On cherche le sommet qui a un f minimal (celui qui a fait le plus court chemin et qui a potentiellement la plus courte distance à parcourir)
      x=afaire[0]
      minf = f[x]
      for noeud in afaire:
        if f[noeud]<minf:
          x=noeud
          minf = f[x]
      
      #On est arrivé 
      if x == fin:
        #On retourne le chemin
        general.stopChrono("AINavigation::aStar")
        return self.fabriqueChemin(promenade,fin)
        
      #On retire le sommet des sommets à tester
      afaire.remove(x)
      #On l'ajoute dans ceux que l'on a testé
      fait.append(x)
      
      #On parcours la liste des noeuds voisins
      for y in self.noeudsVoisins(x):
        if not y in fait:
          #Si on ne l'a pas déjà parcourut
          tmpG = g[x] + self.cout(x,y)
          
          if not y in afaire:
            #S'il n'est pas en attente, on l'y met
            afaire.append(y)
            mieux = True
          elif tmpG < g[y]:
            #S'il est en attente et a une meilleure statistique en passant par ici (g plus petit)
            mieux = True
          else:
            #On peut atteindre ce sommet par un chemin plus court
            mieux = False
          if mieux:
            #On met a jour les infos de parcours pour ce point
            promenade[y] = x
            g[y] = tmpG
            h[y] = general.distanceCarree(self.planete.sommets[y], self.planete.sommets[fin])
            f[y] = g[y] + h[y]
            
    general.gui.afficheTexte("Impossible de trouver une trajectoire pour aller de "+str(deb)+" à "+str(fin), "avertissement")
    general.stopChrono("AINavigation::aStar")
    #On a rien trouvé
    return None
    
  def cout(self, x, y):
    """Calcul le cout nécessaire pour passer du sommet x au sommet y"""
    general.startChrono("AINavigation::cout")
    for elem in self.graph[x]:
      if elem[0]==y:
        general.stopChrono("AINavigation::cout")
        return elem[1]
    #On arrive là si on ne peut pas passer de x à y directement
    #Ce qui est impossible normalement mais on sait jamais
    print "AStar : Erreur calcul de cout"
    general.stopChrono("AINavigation::cout")
    return None    
    
  def noeudsVoisins(self, id):
    """Retourne les indices des sommets voisins au sommet id"""
    general.startChrono("AINavigation::noeudsVoisins")
    #On ne peut pas utiliser self.planete.voisinage[id] car il ne prend pas en compte les couts
    voisins = []
    
    for elem in self.graph[id]:
      if elem[1] != self.maxcout:
        voisins.append(elem[0])
    general.stopChrono("AINavigation::noeudsVoisins")
    return voisins
   
  def fabriqueChemin(self, promenade,fin):
    """Construit le chemin calculé par A*"""
    if fin in promenade.keys():
      out = []
      p = self.fabriqueChemin(promenade,promenade[fin])
      for element in p:
        out.append(element)
      out.append(fin) #On ajoute le sommet courant a la fin de la pile comme on parcours la liste à l'envers
      return out
    else:
      return [fin]
       
  # Fin Recherche d'itinéraire -----------------------------------------
  
class AI:
  sprite = None
  comportement = None
  
  def __init__(self, sprite):
    self.sprite = sprite
    self.comportement = AIComportement(self)
    
  def choisitComportement(self, type):
    print "AI::Charge comportement type"
    
  def ping(self, temps):
    self.comportement.ping()
    acceleration = self.comportement.steeringForce / self.sprite.masse;
    self.sprite.inertieSteering = acceleration
    self.sprite.direction = general.normaliseVecteur(self.comportement.steeringForce)
    
  def clear(self):
    self.sprite = None
    self.comportement.clear()
    self.comportement = None
    
class AIComportementUnitaire:
  comportement = None
  priorite = None
  force = None
  
  def __init__(self, comportement):
    self.comportement = comportement
    self.priorite = 0.5
    self.force = [0.0, 0.0, 0.0]
    
  def ping(self, temps):
    pass
    
class AIComportement:
  ai = None
  leader = None
  recrues = None
  checklist = None
  steeringForce = None
  
  _vaVers = None
  _fuit = None
  _poursuit = None
  _reconnaissance = None
  _cherche = None
  _routine = None
  _suitChemin = None
  
  def __init__(self, AI):
    self.ai = AI
    self.recrues = []
    self.checklist=[]
    self.steeringForce = [0.0, 0.0, 0.0]
    
  def ping(self, temps):
    force = [0.0,0.0,0.0]
    facteurs = 0.0
    if self._vaVers != None:
      composant = self._vaVers
      composant.ping(temps)
      force = force[0]+composant.force[0]*composant.priorite, force[1]+composant.force[1]*composant.priorite, force[2]+composant.force[2]*composant.priorite
      facteurs+=composant.priorite
    if self._fuit != None:
      composant = self._fuit
      composant.ping(temps)
      force = force[0]+composant.force[0]*composant.priorite, force[1]+composant.force[1]*composant.priorite, force[2]+composant.force[2]*composant.priorite
      facteurs+=composant.priorite
    if self._poursuit != None:
      composant = self._poursuit
      composant.ping(temps)
      force = force[0]+composant.force[0]*composant.priorite, force[1]+composant.force[1]*composant.priorite, force[2]+composant.force[2]*composant.priorite
      facteurs+=composant.priorite
    if self._reconnaissance != None:
      composant = self._reconnaissance
      composant.ping(temps)
      force = force[0]+composant.force[0]*composant.priorite, force[1]+composant.force[1]*composant.priorite, force[2]+composant.force[2]*composant.priorite
      facteurs+=composant.priorite
    if self._cherche != None:
      composant = self._cherche
      composant.ping(temps)
      force = force[0]+composant.force[0]*composant.priorite, force[1]+composant.force[1]*composant.priorite, force[2]+composant.force[2]*composant.priorite
      facteurs+=composant.priorite
    if self._routine != None:
      composant = self._routine
      composant.ping(temps)
      force = force[0]+composant.force[0]*composant.priorite, force[1]+composant.force[1]*composant.priorite, force[2]+composant.force[2]*composant.priorite
      facteurs+=composant.priorite
    if self._suitChemin != None:
      composant = self._suitChemin
      composant.ping(temps)
      force = force[0]+composant.force[0]*composant.priorite, force[1]+composant.force[1]*composant.priorite, force[2]+composant.force[2]*composant.priorite
      facteurs+=composant.priorite
      
    delta = 1.0/facteurs
    force = force[0]*delta, force[1]*delta, force[2]*delta
    self.steeringForce = force
    
  def clear(self):
    self.ai = None
    
  def suitChemin(self, chemin, priorite):
    self._suitChemin = SuitChemin(self, chemin, priorite)
    
  def vaVers(self, cible, priorite):
    self._vaVers = VaVers(self, cible, priorite)

  def fuit(self, cible, distancePanique, distanceOK, priorite):
    self._fuit = _fuit(self, cible, distancePanique, distanceOK, priorite)

  def poursuit(self, cible, distanceMax, priorite):
    self._poursuit = Poursuit(self, cible, distanceMax, priorite)

  def reconnaissance(self, rayonZone, rayonChangeDirection, priorite):
    self._reconnaissance = Reconnaissance(self, rayonZone, rayonChangeDirection, priorite)

  def cherche(self, cible, priorite):
    self._cherche = Cherche(self, cible, priorite)
    
  def routine(self, checklist, priorite):
    if self._routine ==None:
      self._routine = Routine(self)
      
    for element in checklist:
      self._routine.ajouteCheck(element, priorite)
    
  def devientChef(self):
    self.leader = self
    
  def recrute(self, ai):
    if self.leader!=None and self.leader!=self:
      self.leader.recrute(ai)
    else:
      elif self.leader==None:
        self.devientChef()
      ai.leader=self
      ai.comportement.poursuit(self, -1, 0.75)
      self.recrues.append(ai)
      
  def dissolution(self):
    for ai in self.recrues:
      ai.dissolution()
      ai.comportement._poursuit = None
    self.recrues = []
    self.leader = None
    
  def clear(self):
    self._vaVers = None
    self._fuit = None
    self._poursuit = None
    self._reconnaissance = None
    self._cherche = None
    self._routine = None
    self._suitChemin = None
    if len(self.recrues)>1:
      leader = self.recrues[0]
      leader.dissolution()
      for ai in self.recrues:
        leader.recrute(ai)
    self.dissolution()