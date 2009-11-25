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

  def __init__(self, planete):
    self.planete = planete
    
  # Création d'infos ---------------------------------------------------    
  def coutPassage(self, idxSommet1, idxSommet2):
    """Retourne le cout necessaire pour passer du sommet idxSommet1 au sommet idxSommet2"""
    general.startChrono("AINavigation::coutPassage")
    deltaMax = 1
    cout = (general.normeVecteur(self.planete.sommets[idxSommet2]) - general.normeVecteur(self.planete.sommets[idxSommet1]))*100
    cout = cout*cout*cout
    if cout > deltaMax or cout < -deltaMax:
      cout = self.maxcout
      
    #On ne peut pas passer sous l'eau
    if general.normeVecteur(self.planete.sommets[idxSommet2]) < self.planete.niveauEau or general.normeVecteur(self.planete.sommets[idxSommet1]) < self.planete.niveauEau:
      cout = self.maxcout
      
    #if cout==self.maxcout:
    #  render.attachNewNode(self.dessineLigne((1.0, 0.0, 0.0), general.multiplieVecteur(self.planete.sommets[idxSommet1], 1.25), general.multiplieVecteur(self.planete.sommets[idxSommet2], 1.25)))
    #else:
    #  render.attachNewNode(self.dessineLigne((0.0, 1.0, 0.0), general.multiplieVecteur(self.planete.sommets[idxSommet1], 1.25), general.multiplieVecteur(self.planete.sommets[idxSommet2], 1.25)))
      
    general.stopChrono("AINavigation::coutPassage")
    return cout
    
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
    general.startChrono("AINavigation::fabriqueChemin")
    if fin in promenade.keys():
      out = []
      p = self.fabriqueChemin(promenade,promenade[fin])
      for element in p:
        out.append(element)
      out.append(fin) #On ajoute le sommet courant a la fin de la pile comme on parcours la liste à l'envers
      general.stopChrono("AINavigation::fabriqueChemin")
      return out
    else:
      general.stopChrono("AINavigation::fabriqueChemin")
      return [fin]
       
  # Fin Recherche d'itinéraire -----------------------------------------

#Basé sur http://www.red3d.com/cwr/steer/
class ComportementAIUnitaire:
  def __init__(self, personnage):
    self.personnage = personnage
  
class ComportementAIFuite(ComportementAIUnitaire):
  #Définit les règles de quand un personnage abandonne ce qu'il fait pour fuir
  def __init__(self, personnage):
    ComportementAI.__init__(self, personnage)

class ComportementAIManoeuvreDeGroupe(ComportementAIUnitaire):
  #Définit les règles de quand un personnage se déplace au sein d'un groupe
  #(suivit du chef, organisation spatiale, ...)
  def __init__(self, personnage):
    ComportementAI.__init__(self, personnage)

class ComportementAIFileAttente(ComportementAIUnitaire):
  #Définit les règles de quand un personnage doit attendre dans une file (toilettes occupées)
  def __init__(self, personnage):
    ComportementAI.__init__(self, personnage)
    
class ComportementAIReconnaissance(ComportementAIUnitaire):
  #Définit les règles de quand un personnage se promène pour découvrir le coin
  def __init__(self, personnage):
    ComportementAI.__init__(self, personnage)
    
class ComportementAITraqueur(ComportementAIUnitaire):
  #Définit les règles de quand un personnage poursuit quelque chose / quelqu'un
  def __init__(self, personnage):
    ComportementAI.__init__(self, personnage)
    

class ComportementAI:
  #Le blob qui gère le comportement d'une IA
  personnage = None
  
  def __init__(self, personnage):
    self.personnage = personnage
    
  def ping(self, temps):
    pass
    
class ComportementAIRecolteur(ComportementAI):
  #Un gars qui va choper des ressources et les ramène au bâtiment le plus proche
  dernierRessource = None
  dernierBatiment = None
  
  def __init__(self, personnage):
    ComportementAI.__init__(self, personnage)
    
  def ping(self, temps):
    pass
    
  def rechercheRessource(self, typeRessource=[]):
    pass
    
  def rechercheBatiment(self, typeBatiment=[]):
    pass
    
  def recolte(self):
    pass
    
  def ramene(self):
    pass

