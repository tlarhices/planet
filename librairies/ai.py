#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general

import math
import random
import os, sys
import time

from pandac.PandaModules import *
from multiprocessing import Process, Pipe

from weakref import ref, proxy

class AIPlugin:
  plugins=None
  
  def __init__(self):
    """Gère les plugins d'IA, à ne créer qu'une fois"""
    self.plugins={}
    
  def scan(self):
    """Scan le dossier de plugins d'IA et en fait la liste"""
    for fichier in os.listdir(os.path.join(".","librairies","ai")):
      if fichier.endswith(".py"):
        try:
          _temp = __import__(fichier[:-3], globals(), locals(), ['Bulbe'], -1)
          bulbe = _temp.Bulbe(None) #On appel le constructeur pour être sûr que ça marche et attraper les infos de classe
          if general.configuration.getConfiguration("Debug", "ai", "debug_aiplugin_scan_plugin", "f", bool):
            print "AIPlugin :: trouvé plugin `",bulbe._classe_,"` dans le fichier",os.path.join(".","librairies","ai",fichier)
          self.plugins[bulbe._classe_]=_temp.Bulbe
        except AttributeError:
          if general.configuration.getConfiguration("Debug", "ai", "debug_aiplugin_scan_plugin", "f", bool):
            print "Avertissement :: ",os.path.join(".","librairies","ai",fichier),"n'est pas un plugin d'IA valide"
          
  def getIA(self, type):
    """Retourne le plugin d'IA demandé s'il existe ou None"""
    if not type in self.plugins.keys():
      print "Erreur AIPlugin :: Plugin d'IA '"+str(type)+"' inexistant ou invalide"
      if self.plugins:
        print "Plugins chargés :"
        for element in self.plugins.keys():
          print "-",element
      else:
        print "Aucun plugin valide trouvé"
      return None
    return self.plugins[type]

class AINavigation:
  #Classe qui gère la navigation sur la surface de la planète
  graph = None #Le graph de navigation
  angleSolMax = None

  def __init__(self):
    general.TODO("Prise en compte des bateaux lors des calculs de déplacement")
    self.angleSolMax = general.configuration.getConfiguration("ai","navigation", "angleSolMax","70.0", float)
    
  def detruit(self):
    self.graph = None
    
  # Création d'infos ---------------------------------------------------    
  def anglePassage(self, idxSommet1, idxSommet2, estSommets):
    """Retourne l'angle necessaire pour passer du sommet idxSommet1 au sommet idxSommet2"""
    general.TODO("Vérifier que l'angle soit calculé comme il devrait être")
    
    if estSommets:
      ptxSommet1, ptxSommet2 = Vec3(general.planete.geoide.sommets[idxSommet1]), Vec3(general.planete.geoide.sommets[idxSommet2])
    else:
      ptxSommet1, ptxSommet2 = Vec3(idxSommet1), Vec3(idxSommet1)
      
    sp = ptxSommet2 - ptxSommet1
    ptxSommet2.normalize()
    ptxSommet1.normalize()
    spH = ptxSommet2 - ptxSommet1
    angle = spH.angleDeg(sp)
      
    return angle
    
  def peutPasser(self, idxSommet1, idxSommet2, angleSolMax=None):
    """
    Retourne True si l'angle pour passer de idxSommet1 à idxSommet2
    est inférieur à angleSolMax et si aucun des 2 sommets ne se trouve
    sous l'eau
    """
    general.TODO("Ajouter le support des sprites qui savent nager et voler")
    
    if angleSolMax==None:
      angleSolMax = self.angleSolMax
      
    connu = False
      
    if idxSommet1 in self.graph.keys():
      if idxSommet2 in self.graph[idxSommet1].keys():
        angle = self.graph[idxSommet1][idxSommet2]
        
        connu = True
        
        #Le terrain est trop pentu
        if angle >= angleSolMax or angle <= -angleSolMax:
          return False
        
        #On ne peut pas passer sous l'eau
        if general.planete.geoide.sommets[idxSommet2].length() <= general.planete.geoide.niveauEau or general.planete.geoide.sommets[idxSommet1].length() <= general.planete.geoide.niveauEau:
          return False
          
    #idxSommet1 n'est pas à coté de idxSommet2
    if not connu :
      print "Erreur navigation, arc inconnu", idxSommet1, idxSommet2
      
    return connu
          
  def grapheDeplacement(self):
    """
    Fabrique le graphe de deplacement de la planète
    graph[sommet de départ][sommet d'arrivée possible]=angle entre les 2
    """
    general.startChrono("AINavigation::grapheDeplacement")
    cpt=0.0
    self.graph = {}
    
    totclef = len(general.planete.geoide.voisinage.keys())
    
    for source in general.planete.geoide.voisinage.keys():
      if general.DEBUG_AI_GRAPHE_DEPLACEMENT_CONSTRUCTION:
        if cpt%250==0:
          general.planete.afficheTexte("Création du graphe de déplacement... %(a)i/%(b)i", parametres={"a": cpt, "b": totclef}, type="ai")
      for voisin in general.planete.geoide.voisinage[source]:
        if source!=voisin:
          self.ajouteNoeud(source, voisin)
      cpt+=1.0
    general.stopChrono("AINavigation::grapheDeplacement")
        
  def ajouteNoeud(self, pt1, pt2):
    """Ajoute un noeud au graphe"""
    general.startChrono("AINavigation::ajouteNoeud")
    angle = self.anglePassage(pt1, pt2, True)
    if pt1 not in self.graph.keys():
      self.graph[pt1]={}
    
    self.graph[pt1][pt2] = angle
    general.stopChrono("AINavigation::ajouteNoeud")
      
  def maj(self, idxSommet):
    """
    Met à jour les données après modifications d'un sommet
    """
    general.startChrono("AINavigation::maj")
    voisins = self.graph[idxSommet].keys()
    for voisin in voisins:
      self.ajouteNoeud(idxSommet, voisin)
      self.ajouteNoeud(voisin, idxSommet)
    general.stopChrono("AINavigation::maj")
  # Fin création d'infos -----------------------------------------------
  
  # Recherche d'itinéraire ---------------------------------------------
  def aStar(self, deb, fin, angleSolMax=None, horizonAStar=1):
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
    h[deb] = (general.planete.geoide.sommets[deb] - general.planete.geoide.sommets[fin]).lengthSquared() #L'estimation se fait selon la distance euclidienne (on utilise le carré car sqrt est trop lent et c'est juste pour une comparaison)
    f[deb] = g[deb]+h[deb] # == h[deb] ;)
    
    atteindHorizon = False
    
    #On boucle tant que l'on a des sommets à parcourir
    while afaire:
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
      if f[x]>horizonAStar*general.configuration.getConfiguration("ai", "navigation", "profondeurmax", "0.2", float):
        #On coupe la branche car elle est trop longue
        atteindHorizon = True
      else:
        #On parcours la liste des noeuds voisins
        for y in self.noeudsVoisins(x, angleSolMax):
          if not y in fait:
            #Si on ne l'a pas déjà parcourut
            angle = self.angle(x, y)
            tmpG = g[x] + angle*(general.planete.geoide.sommets[x]-general.planete.geoide.sommets[y]).lengthSquared()
            
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
              h[y] = angle*(general.planete.geoide.sommets[x]-general.planete.geoide.sommets[y]).lengthSquared()
              f[y] = g[y] + h[y]
            
    #general.interface.afficheTexte("Impossible de trouver une trajectoire pour aller de %(a)s à %(b)s.", parametres={"a": deb, "b":fin}, type="avertissement")
    general.stopChrono("AINavigation::aStar")
    #On a rien trouvé
    return atteindHorizon
    
  def angle(self, x, y):
    """Calcul l'angle pour passer du sommet x au sommet y"""
    if x in self.graph.keys():
      if y in self.graph[x].keys():
        return self.graph[x][y]
    #On arrive là si on ne peut pas passer de x à y directement
    #Ce qui est impossible normalement mais on sait jamais
    print "AStar : Erreur calcul d'angle de",x,"à",y
    return None    
    
  def noeudsVoisins(self, id, angleSolMax=None):
    """Retourne les indices des sommets voisins au sommet id"""
    general.startChrono("AINavigation::noeudsVoisins")
    
    if angleSolMax==None:
      angleSolMax = self.angleSolMax
    
    #On ne peut pas utiliser general.planete.geoide.voisinage[id] car il ne prend pas en compte les angles
    voisins = []
    
    for elem in self.graph[id].keys():
      if self.graph[id][elem] <= angleSolMax:
        voisins.append(elem)
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
  """Le centre de l'IA des sprite"""
  sprite = None
  comportement = None
  bulbe = None
  
  def __init__(self, sprite):
    """Construit une IA pour sprite"""
    self.sprite = proxy(sprite)
    #Prépare les moulinettes de base
    self.comportement = AIComportement(self)
    
  def stop(self):
    """Stoppe toutes les actions de l'IA"""
    self.comportement.stop()
    if self.bulbe != None:
      self.bulbe.stop()
    
  def choisitComportement(self, type):
    """Choisit un type de comportement pour cette IA"""
    #On charge un nouveau type de comportement depuis le plugin
    self.bulbe = general.aiPlugin.getIA(type)
    if self.bulbe == None:
      print "AI :: Impossible de charger comportement"
    else:
      self.bulbe=self.bulbe(self.sprite)
    
  def ping(self, temps):
    """Boucle de calcul de l'IA"""
    return
    #On calcul chaque comportement
    self.comportement.ping(temps)
    
    #On calcul l'accélération et la direction du déplacement
    acceleration = self.comportement.steeringForce / self.sprite.masse
    self.sprite.inertieSteering = acceleration
    self.sprite.direction = Vec3(self.comportement.steeringForce)
    self.sprite.direction.normalize()
    
    #On ping l'IA comportementale
    if self.bulbe != None:
      self.bulbe.ping(temps)
    
  def clear(self):
    """Purge l'IA"""
    self.sprite = None
    if self.comportement!=None:
      self.comportement.clear()
      self.comportement = None
    if self.bulbe!=None:
      self.bulbe.detruit()
    
  def sauvegarde(self):
    """Sauvegarde l'IA dans un fichier"""
    out = ""
    if self.comportement != None:
      out+=self.comportement.sauvegarde()
    if self.bulbe != None:
      out+=self.bulbe.sauvegarde()
    return out
    
class AIComportementUnitaire:
  """Définit la classe de base de la gestion des comportements"""
  comportement = None
  priorite = None
  force = None
  fini = None
  
  def __init__(self, comportement, priorite):
    self.comportement = comportement
    self.priorite = priorite
    self.force = Vec3(0.0, 0.0, 0.0)
    self.fini = False
    
  def sauvegarde(self):
    out = ""
    general.TODO("Sauvegarde des comportements unitaires de type :"+str(self.__class__))
    return out
    
  def ping(self, temps):
    self.supprime()
    
  def stop(self):
    pass
    
  def supprime(self):
    self.comportement = None
    self.fini = True
    
class SuitChemin(AIComportementUnitaire):
  chemin = None
  courant = None
  cible = None
  
  def __init__(self, chemin, cible, comportement, priorite):
    """Fait suivre au sprite le chemin allant à cible"""
    AIComportementUnitaire.__init__(self, comportement, priorite)
    self.chemin = chemin
    self.cible = cible
    
    #if isinstance(self.chemin, list):
    #  self.nettoieChemin()
    
  def nettoieChemin(self):
    """Simplifie le début et la fin des chemins supprimant des points de passages inutiles"""
    if self.chemin==None:
      return
      
    general.TODO("Vérifier si en troncant, on ne jette pas le sprite à la mer")
      
    if len(self.chemin)>2:
      if (self.getCoord(self.chemin[0])-self.getCoord(self.chemin[1])).lengthSquared() > (self.getCoord(self.chemin[0])-self.getCoord(self.chemin[2])).lengthSquared():
        self.chemin.remove(self.chemin[1])
        print "Troncage du chemin pour",self.chemin
    if len(self.chemin)>2:
      if (self.getCoord(chemin[-1])-self.getCoord(self.chemin[-2])).lengthSquared() > (self.getCoord(self.chemin[-1])-self.getCoord(self.chemin[-3])).lengthSquared():
        self.chemin.remove(self.chemin[-2])
        print "Troncage du chemin pour",self.chemin
  
  def afficheChemin(self):
    """Affiche le chemin à l'écran"""
    if self.chemin==None:
      return
      
    if general.DEBUG_AI_SUIT_CHEMIN:
      prev=None
      for element in self.chemin:
        if isinstance(element, int):
          element = general.planete.geoide.sommets[element]
        if prev!=None:
          general.planete.geoide.racine.attachNewNode(self.comportement.ai.sprite.dessineLigne((0.0,1.0,0.0), prev * 1.2, element * 1.2))
        prev = element
        
  def getCoord(self, point):
    """
    Retourne les coordonnées du point
    (Traduit les indices de sommets en coordonnées de sommet)
    """
    if isinstance(point, int):
      return general.planete.geoide.sommets[point]
    return point
    
  def ping(self, temps):
    """Boucle de calcul"""
    
    if self.chemin == None:
      #On a pas de chemin à suivre
      self.supprime()
      return
      
    #Si le chemin est une socket, alors on est en train d'attendre de recevoir un résultat de l'IA de navigation
    if not isinstance(self.chemin, list):
      if self.chemin.poll():
        recep = self.chemin.recv()
        recep=recep[1:-1].split(",")
        self.chemin=[self.comportement.ai.sprite.position]
        for elem in recep:
          self.chemin.append(int(elem))
        self.chemin.append(self.cible)
        #self.nettoieChemin()
      return
      
    if not self.chemin:
      #On est arrivé au bout du chemin
      self.supprime()
      return
      
    if self.courant == None:
      #On change de point de contrôle
      if general.DEBUG_AI_SUIT_CHEMIN:
        print "va vers checkpoint suivant..."
      general.TODO("Tester si le passage est toujours valide (changements géographiques,...) jusqu'au prochain point, recalculer si besoin est")

      if isinstance(self.chemin[0], int):
        if not self.chemin[0] in general.planete.aiNavigation.graph[general.planete.trouveSommet(self.comportement.sprite.position)]:
          print "bout de chemin desormais impraticable"
          chemin = self.comportement.calculChemin(sprite.position, self.chemin[-1])
          self.comportement.suitChemin(chemin, self.chemin[-1], self.priorite)
          self.chemin = None
          return

      #Comme on a pas de cible au chemin pour le moment
      #On prend le point suivant sur le chemin
      cible = self.getCoord(self.chemin.pop(0))
      
      if general.configuration.getConfiguration("debug", "ai", "DEBUG_AI_GRAPHE_DEPLACEMENT_PROMENADE", "t", bool):
        general.planete.geoide.racine.attachNewNode(self.comportement.ai.sprite.dessineLigne((1.0,0.0,0.0), self.comportement.ai.sprite.position * 1.2, cible * 1.2))
        mdl = loader.loadModel("./data/modeles/sphere.egg")
        mdl.setScale(0.1)
        mdl.setPos(cible * 1.2)
        mdl.setColor(1.0,0.0,0.0)
        mdl.reparentTo(general.planete.geoide.racine)
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
    """Déplace l'IA cers le point cible en ligne droite"""
    AIComportementUnitaire.__init__(self, comportement, priorite)
    self.cible = cible
    
  def ping(self, temps):
    """Boucle de calcul"""
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
    """
    Appel la fonction, lui donnant le dictionnaire de paramètres
    Le paramètre "temps" sera automatiquement ajouté et/ou mit à jour au temps de ping du comportement
    La fonction peut retourner :
    - -1 : Pas besoin de rappeler la fonction, on a fini
    - 0 : La fonction n'a rien fait, on la rappel au ping suivant
    - 1 : La fonction a fait un truc mais demande à être rappelée au ping suivant
    """
    AIComportementUnitaire.__init__(self, comportement, priorite)
    self.fonction = fonction
    self.dico = dico
    
  def ping(self, temps):
    """Boucle de calcul"""
    if self.fini:
      return
      
    #Met à jour l'info de temps dans le dico
    if "temps" in self.dico.keys():
      self.dico["temps"]=temps
      
    ret = self.fonction(**self.dico)
    if ret<0:
      self.fini=True
    
class Routine(AIComportementUnitaire):
  elements = None
  courant = None
  comportementBC = None
  
  def __init__(self, comportement, priorite):
    """Exécute des tâches selon une checkliste"""
    AIComportementUnitaire.__init__(self, comportement, priorite)
    self.elements = []
    self.comportementBC = comportement
    
  def ajouteCheck(self, element, cyclique, priorite):
    """Ajoute une nouvelle tâche, si cyclique==True, alors elle sera replacée à la fin de la liste lors de son exécution"""
    if self.elements == None:
      self.elements = []
      self.fini = False
      self.courant = None
      self.comportement = self.comportementBC
    self.elements.append((element, cyclique, priorite))
    
  def ping(self, temps):
    """La boucle de calcul"""
    if self.elements == None:
      #on a rien à faire
      self.supprime()
      if self.courant!=None:
        self.courant.fini = True
        self.courant = None
      return
    if not self.elements:
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
    """Tranforme la tache en quelque chose d'utilisable"""
    if True:#isinstance(tache, list):
      fonction, dico = tache
      return AppelFonction(fonction, dico, self.comportement, priorite)
    return VaVers(self.comportement.ai.sprite.position, self.comportement, priorite)
      
  def supprime(self):
    AIComportementUnitaire.supprime(self)
    self.elements = None
    self.courant = None
    
class AIComportement:
  ai = None #L'IA qui gère le sprite
  leader = None #Le chef du sprite (s'il en a un)
  recrues = None #Les sprites qui ont cette IA pour chef (s'il y en a)
  steeringForce = None #La force produite par l'IA (la direction et la vitesse à laquelle on y va)
  comportements = None #La liste de tous les bouts d'IA qu'il faut prendre en compte pour le calcul
  ennui = None #Vaut True si l'IA s'ennuie (elle n'a rien à faire) (hook vers le plugin)
  horizonAStar = None #Cette valeur augmente à chaque fois qu'un chemin n'a pas été trouvé et que l'horizon de calcul de AStar a été atteint
  
  def __init__(self, AI):
    """Le centre de la partie steering de l'IA"""
    self.ai = proxy(AI)
    self.recrues = []
    self.steeringForce = Vec3(0.0, 0.0, 0.0)
    self.comportements = []
    self.ennui = False
    self.horizonAStar=1
    
  def stop(self):
    for comportement in self.comportements:
      comportement.stop()
    self.comportements = []
    
  def sauvegarde(self):
    out = ""
    out += "aicomportement-steeringforce:"+self.ai.sprite.id+":"+str(self.steeringForce[0])+":"+str(self.steeringForce[1])+":"+str(self.steeringForce[2])+":\r\n"
    if self.recrues:
      out += "aicomportement-recrues:"
      for element in self.recrues:
        out += element.id+":"
      out += "\r\n"
    if self.leader!=None:
      out += "aicomportement-leader:"+self.leader.id+":\r\n"
    for comportement in self.comportements:
      out+=comportement.sauvegarde()
    return out
    
  def ping(self, temps):
    """Boucle de calcul"""
    force = Vec3(0.0,0.0,0.0)
    facteurs = 0.0
    
    finis = [] #La liste des comportements qui ont finis (à retirer)
    
    #On ping chaque comportement et on regarde là où il tente d'emmener l'IA
    for comportement in self.comportements:
      comportement.ping(temps)
      if not comportement.fini:
        force = force+comportement.force*comportement.priorite
        facteurs+=comportement.priorite
      else:
        finis.append(comportement)
        
    #On retire les comportements qui ont fini
    for comportement in finis:
      while self.comportements.count(comportement)>0:
        self.comportements.remove(comportement)
      
    if general.DEBUG_AI_PING_PILE_COMPORTEMENT:
      print self.ai.sprite.id,"somme forces",force
      print self.ai.sprite.id,"somme facteurs", facteurs
      
    #On calcul la force résultante
    if facteurs!=0:
      delta = 1.0/facteurs
    else:
      delta = 0.0
    force = force*delta
    self.steeringForce = force
    if general.DEBUG_AI_PING_PILE_COMPORTEMENT:
      print self.ai.sprite.id,"steering force", facteurs
      
    #On met à jour les hook de l'IA
    if not self.comportements:
      self.ennui = True
      if self.ai.bulbe != None:
        if self.ai.bulbe.ennui():
          print self.ai.sprite.id,"s'ennuie"
    else:
      self.ennui = False
        
  def clear(self):
    self.ai = None
    
  def chercheSpriteProche(self, stock, ressources, joueur, strict):
    """
    Recherche le sprite le plus proche qui correspond aux critères de recherche
    depot : si True, alors cherche un endroit où vider ses poches
    ressources : une liste des ressources que l'on tente de récupérer (ou déposer si depot=True) ex : ["nourriture", "bibine"] ou -1 si on ne cherche pas de ressources
    joueur : cible les sprite d'un seul joueur:
      - instance de joueur -> uniquement les sprites de ce joueur
      - nom d'un joueur -> uniquement les sprites de ce joueur
      - None -> uniquement les sprites qui n'appartiennent à personne
      - -1 -> tous les sprites
    strict : si True, alors le sprite retourné possédera tous les types de ressource demandé, sinon le plus proche qui en a au moins une
    DANGER : retourne une Socket
    """
    if True: #Passer à False pour faciliter le debug (danger, fait toutes les recherches en bloquant)
      parent_conn, child_conn = Pipe()
      p = Process(target=self._chercheSpriteProche_thread, args=(child_conn, stock, ressources, joueur, strict))
      p.start()
      return parent_conn
    else:
      return self._chercheSpriteProche_thread(None, stock, ressources, joueur, strict)

  def _chercheSpriteProche_thread(self, conn, stock, ressources, joueur, strict):
    """A ne pas appeler directement, utiliser chercheSpriteProche"""
    proche = None
    distanceA = None
    
    #Regarde si les ressources correspondent à la requète
    def testeRessources(trouver, sprite, stock, strict=False):
      contenu=sprite.contenu
      for element in trouver:
        if element in contenu.keys():
          if (stock and contenu[element]<sprite.taillePoches[element]) or (not stock and contenu[element]>0):
            if not strict:
              return True #Pas strict et on en a un
          else:
            if strict:
              return False #Strict et il en manque au moin 1
        else:
          if strict:
            return False #Strict et il en manque au moin 1
      return True #Strict et on a tout trouvé
      
    def testeSprite(sprite, stock, joueur, ressources, strict):
      if stock==-1 or stock==sprite.stock:
        if joueur==-1 or sprite.joueur==joueur or sprite.joueur.nom==joueur:
          if ressources==-1 or testeRessources(ressources, sprite, stock, strict):
            return general.planete.aiNavigation.aStar(general.planete.geoide.trouveSommet(self.ai.sprite.position), general.planete.geoide.trouveSommet(sprite.position), horizonAStar=self.horizonAStar)

      
    #On cherche dans tous les sprites le sprite le plus proche (en longueur de chemin et pas à vol d'oiseau) qui correspond à la requète
    for sprite in general.planete.spritesJoueur:
      chemin = testeSprite(sprite, stock, joueur, ressources, strict)
      if isinstance(chemin,list):
        distA=len(chemin)
      else:
        if chemin:
          #On a atteint l'horizon de recherche de chemin et rien trouvé, on l'étend
          self.horizonAStar+=1
        chemin=None
      if chemin!=None:
        if distanceA==None or distanceA>distA:
          proche = sprite
          distanceA = distA       
    for sprite in general.planete.spritesNonJoueur:
      chemin = testeSprite(sprite, stock, joueur, ressources, strict)
      if isinstance(chemin,list):
        distA=len(chemin)
      else:
        if chemin:
          #On a atteint l'horizon de recherche de chemin et rien trouvé, on l'étend
          self.horizonAStar+=1
        chemin=None
      if chemin!=None:
        if distanceA==None or distanceA>distA:
          proche = sprite
          distanceA = distA       
    if proche!=None:
      self.horizonAStar=1
      if conn!=None:
        conn.send(proche.id+"||"+str(chemin))
      else:
        return proche.id+"||"+str(chemin)
    else:
      if conn!=None:
        conn.send(None)
      else:
        return None
    
  def calculChemin(self, debut, fin, priorite):
    """
    Calcule le chemin allant de debut à fin (retourne une chaine de caractère)
    DANGER : retourne une Socket
    """
    if True:
      parent_conn, child_conn = Pipe()
      p = Process(target=self._calculChemin_thread, args=(child_conn, debut, fin, priorite))
      p.start()
      self.suitChemin(parent_conn, fin, priorite)
    else:
      self.suitChemin(self._calculChemin_thread(None, debut, fin, priorite), fin, priorite)
    
  def _calculChemin_thread(self, conn, debut, fin, priorite):
    """A ne pas appeler directement, utiliser calculChemin"""
    try:
      #Prépare les coordonnées
      if isinstance(debut, int):
        idP=debut
      else:
        idP = general.planete.geoide.trouveSommet(debut, tiensCompteDeLAngle=True)
      if isinstance(fin, int):
        idC=fin
      else:
        idC = general.planete.geoide.trouveSommet(fin, tiensCompteDeLAngle=True)
      #Fait le calcul de navigation
      chemin = general.planete.aiNavigation.aStar(idP, idC, horizonAStar=self.horizonAStar)
      
      print "De",idP,"à",idC,":",
      if isinstance(chemin, list):
        print chemin
      else:
        if chemin:
          #On a atteint l'horizon de recherche, on le repousse un peu pour la prochaine recherche
          self.horizonAStar+=1
          chemin = self._calculChemin_thread(None, debut, fin, priorite)
          self.horizonAStar=1
        else:
          print "impossible"
          chemin = None
      #Retourne le chemin
      if conn!=None:
        conn.send(str(chemin))
      else:
        return chemin
    except Exception as inst:
      self.afficheErreur(unicode(inst))


  def afficheErreur(self, texteErreur):
    """
    Affiche une erreur de façon formatée toute belle avec toute la pile d'exécution et des cookies !
   
    Paramètre :
    - texteErreur : Le message d'erreur qui sera affiché
    """
    import sys

    print
    print "ERREUR ---"
    pile = []
    deb = 1 #On commence à 1 car le point 0 c'est afficheErreur et on saît très bien qu'on y est

    #Bouclage sur le contenu de la pile
    cont = True
    while cont:
      try:
        #On attrape la position dans le code où qu'on était il y a deb appels de fonctions
        frame = sys._getframe(deb)
        #On fait une joulie mise en forme des infos
        pile.append(str(frame.f_code.co_filename)+"::"+str(frame.f_code.co_name)+" @"+str(frame.f_lineno))
        #On passe à l'appel suivant
        deb+=1
      except ValueError:
        #ValueError est levé quand _getframe a atteint le bout du bout, donc on a fini de boucler
        cont=False

    #Les appels de fonctions sont pas dans le bon ordre, donc on inverse tout le tableau
    pile.reverse()

    #Un peu de mise en page
    indentation = 0

    #On affiche avec une joulie indentation d'un espace par appel chaque fonction
    for element in pile:
      print str(" "*indentation)+str(element)
      indentation += 1

    #On affiche le message qu'on a eut en cadal
    print sys.exc_info()#[2].print_exc()
    print ">>> "+str(general.i18n.utf8ise(texteErreur).encode("utf-8"))
    print "--- ERREUR"
    print
      
  def piller(self, sprite, priorite):
    """Récupère les ressources contenues dans sprite"""
    print self.ai.sprite.id, "va chopper des ressources à",sprite.id
    self.routine([self.ai.sprite.piller, {"sprite":sprite, "temps":0.0}], False, priorite)
    
  def videPoches(self, sprite, priorite):
    """Récupère les ressources contenues dans sprite"""
    print self.ai.sprite.id, "va se vider les poches à",sprite.id
    self.routine([self.ai.sprite.videPoches, {"sprite":sprite, "temps":0.0}], False, priorite)

  def suitChemin(self, chemin, fin, priorite):
    """Suit le chemin"""
    self.comportements.append(SuitChemin(chemin, fin, self, priorite))
    
  def vaVers(self, cible, priorite):
    """Va vers la cible en ligne droite"""
    self.comportements.append(VaVers(cible, self, priorite))

  def fuit(self, cible, distancePanique, distanceOK, priorite):
    """
    Fuit la cible si la distance entre self et cible est < à distancePanique
    redevient normal si cette distance est supérieure à distanceOK
    """
    self.comportements.append(Fuit(cible, distancePanique, distanceOK, self, priorite))

  def poursuit(self, cible, distanceMax, priorite):
    """Poursuit un sprite jusqu'à ce que la distance parcourue soit supérieure à distanceMax"""
    self.comportements.append(Poursuit(cible, distanceMax, self, priorite))

  def reconnaissance(self, rayonZone, rayonChangeDirection, priorite):
    """Se promène dans une zone de rayon rayonZone autour de sa position initiale variant sa direction selon rayonChangeDirection"""
    self.comportements.append(Reconnaissance(rayonZone, rayonChangeDirection, self, priorite))

  def routine(self, checklist, cyclique, priorite):
    """Effectue des taches (cycliques ou non) selon une liste"""
    routine = None
    for comportement in self.comportements:
      if isinstance(comportement, Routine):
        routine = comportement
    if routine == None:
      routine = Routine(self, 1.0)
      self.comportements.append(routine)
    routine.ajouteCheck(checklist, cyclique, priorite)
    
  def devientChef(self):
    """Devient le leader d'une armée"""
    self.leader = None
    
  def recrute(self, ai):
    """Une ai se met sous ses ordres"""
    if self.leader!=None:
      #Si on a un leader, alors l'ai va suivre ce leader aussi
      self.leader.recrute(ai)
    else:
      #Si on a pas de leader, on le devient
      ai.leader=proxy(self)
      #on dit à l'AI de poursuivre indéfiniment
      ai.comportement.poursuit(self, -1, 0.75)
      self.recrues.append(ai)
      
  def dissolution(self):
    """On dissous son armée (si on en a une)"""
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
    if self.recrues:
      leader = self.recrues[0]
      leader.leader=None
      for ai in self.recrues[1:]:
        leader.recrute(ai)
    self.dissolution()
