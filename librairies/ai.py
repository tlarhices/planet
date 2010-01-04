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

class AIPlugin:
  plugins=None
  
  def __init__(self):
    self.plugins={}
    
  def scan(self):
    for fichier in os.listdir(os.path.join(".","librairies","ai")):
      if fichier.endswith(".py"):
        try:
          _temp = __import__(fichier[:-3], globals(), locals(), ['Bulbe'], -1)
          bulbe = _temp.Bulbe(None)
          print "AIPlugin :: trouvé plugin `",bulbe._classe_,"` dans le fichier",os.path.join(".","librairies","ai",fichier)
          self.plugins[bulbe._classe_]=_temp.Bulbe
        except AttributeError:
          print "Avertissement :: ",os.path.join(".","librairies","ai",fichier),"n'est pas un plugin d'IA valide"
          
  def getIA(self, type):
    if not type in self.plugins.keys():
      print "Erreur AIPlugin :: Plugin d'IA '"+str(type)+"' inexistant ou invalide"
      if len(self.plugins)>0:
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
    self.angleSolMax = float(general.configuration.getConfiguration("ai","navigation", "angleSolMax","70.0"))
    
  def detruit(self):
    self.graph = None
    
  # Création d'infos ---------------------------------------------------    
  def anglePassage(self, idxSommet1, idxSommet2, estSommets):
    """Retourne l'angle necessaire pour passer du sommet idxSommet1 au sommet idxSommet2"""
    general.TODO("Vérifier que l'angle soit calculer comme il devrait être")
    
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
    if angleSolMax==None:
      angleSolMax = self.angleSolMax
      
    connu = False
      
    if idxSommet1 in self.graph.keys():
      if idxSommet2 in self.graph[idxSommet1].keys():
        angle = self.graph[idxSommet1][idxSommet2]
        
        connu = True
        
        if angle >= angleSolMax or angle <= -angleSolMax:
          return False
        
        #On ne peut pas passer sous l'eau
        if general.planete.geoide.sommets[idxSommet2].length() <= general.planete.geoide.niveauEau or general.planete.geoide.sommets[idxSommet1].length() <= general.planete.geoide.niveauEau:
          return False
          
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
          general.planete.afficheTexte("Création du graphe de déplacement... %i/%i" %(cpt,totclef))
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
  def aStar(self, deb, fin, angleSolMax=None):
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
      for y in self.noeudsVoisins(x, angleSolMax):
        if not y in fait:
          #Si on ne l'a pas déjà parcourut
          tmpG = g[x] + self.angle(x, y)
          
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
            h[y] = (general.planete.geoide.sommets[y] - general.planete.geoide.sommets[fin]).lengthSquared()
            f[y] = g[y] + h[y]
            
    general.interface.afficheTexte("Impossible de trouver une trajectoire pour aller de "+str(deb)+" à "+str(fin), "avertissement")
    general.stopChrono("AINavigation::aStar")
    #On a rien trouvé
    return None
    
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
  sprite = None
  comportement = None
  bulbe = None
  
  def __init__(self, sprite):
    self.sprite = sprite
    self.comportement = AIComportement(self)
    
  def choisitComportement(self, type):
    self.bulbe = general.aiPlugin.getIA(type)
    if self.bulbe == None:
      print "AI :: Impossible de charger comportement"
    else:
      self.bulbe=self.bulbe(self.sprite)
    
  def ping(self, temps):
    self.comportement.ping(temps)
    acceleration = self.comportement.steeringForce / self.sprite.masse
    self.sprite.inertieSteering = acceleration
    self.sprite.direction = Vec3(self.comportement.steeringForce)
    self.sprite.direction.normalize()
    
    if self.bulbe != None:
      self.bulbe.ping(temps)
    
  def clear(self):
    self.sprite = None
    self.comportement.clear()
    self.comportement = None
    
  def sauvegarde(self):
    out = ""
    if self.comportement != None:
      out+=self.comportement.sauvegarde()
    if self.bulbe != None:
      out+=self.bulbe.sauvegarde()
    return out
    
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
    
  def sauvegarde(self):
    out = ""
    general.TODO("Sauvegarde des comportements unitaires de type :"+str(self.__class__))
    return out
    
  def ping(self, temps):
    self.supprime()
    
  def supprime(self):
    self.comportement = None
    self.fini = True
    
    

class SuitChemin(AIComportementUnitaire):
  chemin = None
  courant = None
  cible = None
  
  def __init__(self, chemin, cible, comportement, priorite):
    AIComportementUnitaire.__init__(self, comportement, priorite)
    self.chemin = chemin
    self.cible = cible
    if isinstance(self.chemin, list):
      self.nettoieChemin()
    
  def nettoieChemin(self):
    if self.chemin==None:
      return
      
    if len(self.chemin)>2:
      if (self.getCoord(self.chemin[0])-self.getCoord(self.chemin[1])).lengthSquared() > (self.getCoord(self.chemin[0])-self.getCoord(self.chemin[2])).lengthSquared():
        self.chemin.remove(self.chemin[1])
        print "Troncage du chemin pour",self.chemin
    if len(self.chemin)>2:
      if (self.getCoord(chemin[-1])-self.getCoord(self.chemin[-2])).lengthSquared() > (self.getCoord(self.chemin[-1])-self.getCoord(self.chemin[-3])).lengthSquared():
        self.chemin.remove(self.chemin[-2])
        print "Troncage du chemin pour",self.chemin
  
  def afficheChemin(self):
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
    if isinstance(point, int):
      return general.planete.geoide.sommets[point]
    return point
    
  def ping(self, temps):
    if self.chemin == None:
      #On a pas de chemin à suivre
      self.supprime()
      return
      
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
      
    if len(self.chemin) < 1:
      #On est arrivé au bout du chemin
      self.supprime()
      return
      
    if self.courant == None:
      if general.DEBUG_AI_SUIT_CHEMIN:
        print "va vers checkpoint suivant..."
      general.TODO("Tester si le passage est toujours valide (changements géographiques,...) jusqu'au prochain point, recalculer si besoin est")

      #Comme on a pas de cible au chemin pour le moment
      #On prend le point suivant sur le chemin
      cible = self.getCoord(self.chemin.pop(0))
      
      if general.configuration.getConfiguration("debug", "ai", "DEBUG_AI_GRAPHE_DEPLACEMENT_PROMENADE", "t")=="t":
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
  comportementBC = None
  
  def __init__(self, comportement, priorite):
    AIComportementUnitaire.__init__(self, comportement, priorite)
    self.elements = []
    self.comportementBC = comportement
    
  def ajouteCheck(self, element, cyclique, priorite):
    if self.elements == None:
      self.elements = []
      self.fini = False
      self.courant = None
      self.comportement = self.comportementBC
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
    
  def sauvegarde(self):
    out = ""
    out += "aicomportement-steeringforce:"+self.ai.sprite.id+":"+str(self.steeringForce[0])+":"+str(self.steeringForce[1])+":"+str(self.steeringForce[2])+":\r\n"
    if len(self.recrues)>0:
      out += "aicomportement-recrues:"
      for element in self.recrues:
        out += element.id+":"
      out += "\r\n"
    if self.leader!=None:
      out += "aicomportement-leader:"+self.leader.id+":\r\n"
    if len(self.checklist)>0:
      general.TODO("AIComportement::sauvegarde :: Sauvegarde de la checklist")
      out += "aicomportement-checklist:"+str(self.checklist)+":\r\n"
    for comportement in self.comportements:
      out+=comportement.sauvegarde()
    return out
    
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
      if self.ai.bulbe != None:
        if self.ai.bulbe.ennui():
          print self.ai.sprite.id,"s'ennuie"
    else:
      self.ennui = False
        
  def clear(self):
    self.ai = None
    
  def chercheSpriteProche(self, depot, ressources, joueur, strict):
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
    """
    parent_conn, child_conn = Pipe()
    p = Process(target=self._chercheSpriteProche_thread, args=(child_conn, depot, ressources, joueur, strict))
    p.start()
    return parent_conn

  def _chercheSpriteProche_thread(self, conn, depot, ressources, joueur, strict):
    try:
      proche = None
      distance = None
      distanceA = None
      
      def testeRessources(trouver, contenu, strict=False):
        for element in trouver:
          if element in contenu.keys():
            if not strict:
              return True #Pas strict et on en a un
          else:
            if strict:
              return False #Strict et il en manque au moin 1
        return True #Strict et on a tout trouvé
        
      
      for sprite in general.planete.sprites:
        if joueur==-1 or sprite.joueur==joueur or sprite.joueur.nom==joueur:
          if ressources==-1 or testeRessources(ressources, sprite.contenu, strict):
            dist = (self.ai.sprite.position - sprite.position).length()
            if distance==None or distance>dist:
              distA = general.planete.aiNavigation.aStar(general.planete.geoide.trouveSommet(self.ai.sprite.position), general.planete.geoide.trouveSommet(sprite.position))
              if distA!=None:
                distA=len(distA)
              if distA!=None and (distanceA==None or distanceA>distA):
                proche = sprite
                distanceA = distA
                distance = dist
      if proche!=None:
        conn.send(proche.id)
      else:
        conn.send(None)
    except Exception as inst:
      self.afficheErreur(str(inst))
    
  def calculChemin(self, debut, fin, priorite):
    parent_conn, child_conn = Pipe()
    p = Process(target=self._calculChemin_thread, args=(child_conn, debut, fin, priorite))
    p.start()
    self.suitChemin(parent_conn, fin, priorite)
    
  def _calculChemin_thread(self, conn, debut, fin, priorite):
    try:
      if isinstance(debut, int):
        idP=debut
      else:
        idP = general.planete.geoide.trouveSommet(debut, tiensCompteDeLAngle=True)
      if isinstance(fin, int):
        idC=fin
      else:
        idC = general.planete.geoide.trouveSommet(fin, tiensCompteDeLAngle=True)
      chemin = general.planete.aiNavigation.aStar(idP, idC)
      
      print "De",idP,"à",idC,":",
      if chemin!=None:
        print chemin
      else:
        print "impossible"
      conn.send(str(chemin))
    except Exception as inst:
      self.afficheErreur(str(inst))


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
    print ">>> "+str(texteErreur)
    print "--- ERREUR"
    print
      
  def piller(self, sprite, priorite):
    print self.ai.sprite.id, "va chopper des ressources à",sprite.id
    self.routine([self.ai.sprite.piller, {"sprite":sprite, "temps":0.0}], False, priorite)
    
  def suitChemin(self, chemin, fin, priorite):
    self.comportements.append(SuitChemin(chemin, fin, self, priorite))
    
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
