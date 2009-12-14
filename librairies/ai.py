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
  def coutPassage(self, idxSommet1, idxSommet2, estSommets):
    """Retourne le cout necessaire pour passer du sommet idxSommet1 au sommet idxSommet2"""
    #cout = (self.planete.sommets[idxSommet2].length() - self.planete.sommets[idxSommet1].length())*100
    if estSommets:
      ptxSommet1, ptxSommet2 = Vec3(self.planete.sommets[idxSommet1]), Vec3(self.planete.sommets[idxSommet2])
    else:
      ptxSommet1, ptxSommet2 = Vec3(idxSommet1), Vec3(idxSommet1)
      
    sp = ptxSommet2 - ptxSommet1
    ptxSommet2.normalize()
    ptxSommet1.normalize()
    spH = ptxSommet2 - ptxSommet1
    angle = spH.angleDeg(sp)
    
    if angle >= self.angleSolMax or angle <= -self.angleSolMax:
      angle = self.maxcout
      
    #navigation = NodePath("nav")
    #navigation.reparentTo(self.planete.racine)
    #On ne peut pas passer sous l'eau
    if ptxSommet2.length() <= self.planete.niveauEau or ptxSommet1.length() <= self.planete.niveauEau:
      cout = self.maxcout
    #  navigation.attachNewNode(self.dessineLigne((0.0, 0.0, 1.0), self.planete.sommets[idxSommet1] * 1.25, self.planete.sommets[idxSommet2] * 1.25))
    #elif angle==self.maxcout:
    #  navigation.attachNewNode(self.dessineLigne((1.0, 0.0, 0.0), self.planete.sommets[idxSommet1] * 1.25, self.planete.sommets[idxSommet2] * 1.25))
    #else:
    #  navigation.attachNewNode(self.dessineLigne((0.0, 1.0, 0.0), self.planete.sommets[idxSommet1] * 1.25, self.planete.sommets[idxSommet2] * 1.25))
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
    cout = self.coutPassage(pt1, pt2, True)
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
      newCout = self.coutPassage(voisin, idxSommet, True)
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
    h[deb] = (self.planete.sommets[deb] - self.planete.sommets[fin]).lengthSquared() #L'estimation se fait selon la distance euclidienne (on utilise le carré car sqrt est trop lent et c'est juste pour une comparaison)
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
            h[y] = (self.planete.sommets[y] - self.planete.sommets[fin]).lengthSquared()
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
    print "TODO AI::Charge comportement type", type
    
  def ping(self, temps):
    self.comportement.ping(temps)
    acceleration = self.comportement.steeringForce / self.sprite.masse
    self.sprite.inertieSteering = acceleration
    self.sprite.direction = Vec3(self.comportement.steeringForce)
    self.sprite.direction.normalize()
    
  def clear(self):
    self.sprite = None
    self.comportement.clear()
    self.comportement = None
    
class AIComportementUnitaire:
  comportement = None
  priorite = None
  force = None
  fini = None
  
  def __init__(self, comportement, priorite):
    self.comportement = comportement
    self.priorite = priorite
    self.force = Vec3(0.0, 0.0, 0.0)
    self.fini = False
    
  def ping(self, temps):
    self.supprime()
    
  def supprime(self):
    self.comportement = None
    self.fini = True
    
class SuitChemin(AIComportementUnitaire):
  chemin = None
  courant = None
  
  def __init__(self, chemin, comportement, priorite):
    AIComportementUnitaire.__init__(self, comportement, priorite)
    self.chemin = chemin
    
    if general.DEBUG_AI_SUIT_CHEMIN:
      prev=None
      for element in self.chemin:
        if isinstance(element, int):
          element = self.comportement.ai.sprite.planete.sommets[element]
        if prev!=None:
          self.comportement.ai.sprite.planete.racine.attachNewNode(self.comportement.ai.sprite.dessineLigne((0.0,1.0,0.0), prev * 1.2, element * 1.2))
        prev = element
    
  def ping(self, temps):
    if self.chemin == None:
      #On a pas de chemin à suivre
      self.supprime()
      return
      
    if len(self.chemin) < 1:
      #On est arrivé au bout du chemin
      self.supprime()
      return
      
    if self.courant == None:
      if general.DEBUG_AI_SUIT_CHEMIN:
        print "va vers checkpoint suivant..."
      #Comme on a pas de cible au chemin pour le moment
      #On prend le point suivant sur le chemin
      cible = self.comportement.ai.sprite.planete.sommets[self.chemin.pop(0)]
      if general.configuration.getConfiguration("debug", "ai", "DEBUG_AI_GRAPHE_DEPLACEMENT_PROMENADE", "t")=="t":
        self.comportement.ai.sprite.planete.racine.attachNewNode(self.comportement.ai.sprite.dessineLigne((1.0,0.0,0.0), self.comportement.ai.sprite.position * 1.2, cible * 1.2))
        mdl = loader.loadModel("./data/modeles/sphere.egg")
        mdl.setScale(0.1)
        mdl.setPos(cible * 1.2)
        mdl.setColor(1.0,0.0,0.0)
        mdl.reparentTo(self.comportement.ai.sprite.planete.racine)
      #On fait un nouveau comportement pour y aller
      self.courant = VaVers(cible, self.comportement, self.priorite)
      #On ajoute le comportement à l'IA
      self.comportement.comportements.append(self.courant)
    elif self.courant.fini:
      if general.DEBUG_AI_SUIT_CHEMIN:
        print "arrivé au checkpoint"
      #On a fini d'aller au point courant
      self.courant = None
    
class VaVers(AIComportementUnitaire):
  cible = None
  fini = False
  
  def __init__(self, cible, comportement, priorite):
    AIComportementUnitaire.__init__(self, comportement, priorite)
    self.cible = cible
    
  def ping(self, temps):
    if self.cible == None:
      #on a nulle part où aller
      self.supprime()
      return
    
    position = self.comportement.ai.sprite.position
    dist = (position - self.cible).length()
    if general.DEBUG_AI_VA_VERS:
      print self.comportement.ai.sprite.id,"va vers",self.cible
      print self.comportement.ai.sprite.id,"distance",dist
    
    if dist<=self.comportement.ai.sprite.distanceProche:
      if general.DEBUG_AI_VA_VERS:
        print "arrivé au checkpoint"
      #on est arrivé
      self.cible=None
      self.supprime()
      return
      
    #on n'est pas encore arrivé
    #vecteur -position-cible->
    v = self.cible-position
    #la force de steering ici est le vecteur vitesse selon ce vecteur
    if general.DEBUG_AI_VA_VERS:
      print self.comportement.ai.sprite.id,"position",position
    v.normalize()
    self.force = v * self.comportement.ai.sprite.vitesse*temps
    if general.DEBUG_AI_VA_VERS:
      print self.comportement.ai.sprite.id,"force vavers", self.force
    
class AppelFonction(AIComportementUnitaire):
  fonction = None
  dico = None
  
  def __init__(self, fonction, dico, comportement, priorite):
    AIComportementUnitaire.__init__(self, comportement, priorite)
    self.fonction = fonction
    self.dico = dico
    
  def ping(self, temps):
    if self.fini:
      return
      
    if "temps" in self.dico.keys():
      self.dico["temps"]=temps
      
    ret = self.fonction(**self.dico)
    if ret<0:
      self.fini=True
    
    
class Routine(AIComportementUnitaire):
  elements = None
  courant = None
  
  def __init__(self, comportement, priorite):
    AIComportementUnitaire.__init__(self, comportement, priorite)
    self.elements = []
    
  def ajouteCheck(self, element, cyclique, priorite):
    self.elements.append((element, cyclique, priorite))
    
  def ping(self, temps):
    if self.elements == None:
      #on a rien à faire
      self.supprime()
      if self.courant!=None:
        self.courant.fini = True
        self.courant = None
      return
    if len(self.elements)<1:
      #on a rien à faire
      self.supprime()
      if self.courant!=None:
        self.courant.fini = True
        self.courant = None
      return
      
    if self.courant==None:
      #On fait rien en ce moment, on attrape un nouvelle tache
      tache, cyclique, priorite = self.elements.pop(0)
      self.priorite = priorite
      #Si la tache est cyclique, on la remet à la fin de la liste
      if cyclique:
        self.ajouteCheck(tache, cyclique, priorite)
      #On en fait un nouveau comportement
      self.courant=self.produitTache(tache, priorite)
      #On ajoute le comportement à l'IA
      self.comportement.comportements.append(self.courant)
    elif self.courant.fini:
      #On a fini la tâche courante
      self.courant = None
      
  def produitTache(self, tache, priorite):
    if True:#isinstance(tache, list):
      fonction, dico = tache
      return AppelFonction(fonction, dico, self.comportement, priorite)
    print "TODO IA::produitTache pour ", tache, priorite
    return VaVers(self.comportement.ai.sprite.position, self.comportement, priorite)
      
  def supprime(self):
    AIComportementUnitaire.supprime(self)
    self.elements = None
    self.courant = None
    
class AIComportement:
  ai = None
  leader = None
  recrues = None
  checklist = None
  steeringForce = None
  comportements = None
  ennui = None
  
  def __init__(self, AI):
    self.ai = AI
    self.recrues = []
    self.checklist = []
    self.steeringForce = Vec3(0.0, 0.0, 0.0)
    self.comportements = []
    self.ennui = False
    
    
  def ping(self, temps):
    force = Vec3(0.0,0.0,0.0)
    facteurs = 0.0
    
    finis = []
    
    for comportement in self.comportements:
      comportement.ping(temps)
      if not comportement.fini:
        force = force+comportement.force*comportement.priorite
        facteurs+=comportement.priorite
      else:
        finis.append(comportement)
        
    for comportement in finis:
      while self.comportements.count(comportement)>0:
        self.comportements.remove(comportement)
      
    if general.DEBUG_AI_PING_PILE_COMPORTEMENT:
      print self.ai.sprite.id,"somme forces",force
      print self.ai.sprite.id,"somme facteurs", facteurs
      
    if facteurs!=0:
      delta = 1.0/facteurs
    else:
      delta = 0.0
      
    force = force*delta
    self.steeringForce = force
    if general.DEBUG_AI_PING_PILE_COMPORTEMENT:
      print self.ai.sprite.id,"steering force", facteurs
      
    if len(self.comportements)<=0:
      self.ennui = True
      print self.ai.sprite.id,"s'ennuie"
    else:
      self.ennui = False
        
  def clear(self):
    self.ai = None
    
  def calculChemin(self, debut, fin, priorite):
    if isinstance(debut, int):
      idP=debut
    else:
      idP = self.ai.sprite.planete.trouveSommet(debut, tiensCompteDeLAngle=True)
    if isinstance(fin, int):
      idC=fin
    else:
      idC = self.ai.sprite.planete.trouveSommet(fin, tiensCompteDeLAngle=True)
    chemin = self.ai.sprite.planete.aiNavigation.aStar(idP, idC)
    print "De",idP,"à",idC,":",
    if chemin!=None:
      print chemin
      self.suitChemin(chemin, priorite)
    else:
      print "impossible"
    
  def loot(self, sprite, priorite):
    print self.ai.sprite.id, "va chopper des ressources à",sprite.id
    self.routine([self.ai.sprite.loot, {"sprite":sprite, "temps":0.0}], False, priorite)
    
  def suitChemin(self, chemin, priorite):
    self.comportements.append(SuitChemin(chemin, self, priorite))
    
  def vaVers(self, cible, priorite):
    self.comportements.append(VaVers(cible, self, priorite))

  def fuit(self, cible, distancePanique, distanceOK, priorite):
    self.comportements.append(Fuit(cible, distancePanique, distanceOK, self, priorite))

  def poursuit(self, cible, distanceMax, priorite):
    self.comportements.append(Poursuit(cible, distanceMax, self,priorite))

  def reconnaissance(self, rayonZone, rayonChangeDirection, priorite):
    self.comportements.append(Reconnaissance(rayonZone, rayonChangeDirection, self, priorite))

  def routine(self, checklist, cyclique, priorite):
    routine = None
    for comportement in self.comportements:
      if isinstance(comportement, Routine):
        routine = comportement
    if routine == None:
      routine = Routine(self, 1.0)
      self.comportements.append(routine)
    routine.ajouteCheck(checklist, cyclique, priorite)
    
  def devientChef(self):
    self.leader = self
    
  def recrute(self, ai):
    if self.leader!=None and self.leader!=self:
      self.leader.recrute(ai)
    else:
      if self.leader==None:
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
