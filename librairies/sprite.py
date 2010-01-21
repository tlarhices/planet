#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general
import math
import random
import os

from ai import AI

from pandac.PandaModules import *
from weakref import proxy

class Sprite:
  """Un objet du monde"""
  id = None #Un identifiant (si possible unique) qui représente le sprite
  position = None #La position dans l'espace de cet objet
  modele = None #Le modèle 3D de l'objet
  fichierModele = None #Le nom du fichier du modèle 3D (utilisé pour la sauvegarde)
  fichierSymbole = None #Symbole remplaçant le modèle quand on dézoome
  icone = None #Icone sur la minimap
  altCarre = None #L'altitude de cet objet
  rac = None #Ce qui fait que le sprite garde les pieds en bas
  racine = None #Ce qui fait que le sprite garde la tête en haut
  zoneSurbrillance = None #Le disque au pied des personnages qui indique s'il est sélectionné ou non
  barreDeVie = None #La barre de vie
  barreDeVieRacine = None #La barre de vie est proportionnée par rapport à cette racine
  majTempsOrientation = None #La boucle qui s'assure qu'un sprite est bien orienté (les pieds par terre)
  majTempsOrientationMax = None #Le temps minimal à attendre entre 2 recalculs de l'orientation du sprite
  distanceSymbole = None #Distance à partir de laquelle on tranforme l'objet en symbole  (ou fait disparaitre l'objet si symbole==None)
  symbole=None #L'icône qui remplace le modèle quand on dézoome
  
  vitesse = None #La vitesse maximale du sprite en unité/s
  
  joueur = None #Le joueur qui possède cet objet
  stock = None #Le sprite est un contenant à ressource
  contenu = None #Ce qui se trouve dans l'objet
  taillePoches = None #Les seuils maximaux de ce que peut promener un sprite
  vie = None #L'état dans lequel se trouve l'objet
  tempsDeVie = None #Temps depuis lequel ce sprite existe
  dureeDeVie = None #Temps maximal durant lequel ce sprite existera
  typeMort = None #La façon dont le sprite est mort
  
  bouge = None #Si True, alors l'objet peut bouger (personnage, véhicule, ...) sinon il est statique (arbre, bâtiment, ...)
  aquatique = None #Si True, alors l'objet peut aller dans l'eau, sinon il est détruit
  nocturne = None #S'il est nocturne, la nuit ne le tue pas

  zoneContact = None #Les coordonnées de la zone de contact
  
  inertie = None #L'inertie physique de l'objet
  terminalVelocity = None #L'inertie maximale que l'objet peut atteindre
  distanceProche = None #La distance à partir de laquelle un point (objet, checkpoint, ...) est considéré comme atteint
  pileTempsAppliqueGraviteObjetsFixes = None #Les objets fixes (arbre) n'ont la physique que moulinettée une fois de temps en temps pour les garder sur le sol sans bouffer trop de puissance
  seuilRecalculPhysique = None #La durée à attendre avant de recalculer la physique d'un objet physique
  angleSolMax = None #L'angle maximal que le sol peut faire pour que ce sprite puisse marcher dessus
  seuilToucheSol = None #Delta dans lequel on considère qu'on est sur le sol et pas au-dessus
  constanteGravitationelle = None #force de gravitation de la planète sur cet objet (prends en compte la résistance à l'air et tout ça)
  
  blipid = None #L'id du blip sur la carte
  
  ai = None #Le point sur le comportement qui contrôle ce sprite (ne pas partager sous risque d'avoir des IA qui font n'importe quoi)
  inertieSteering = None #Le vecteur inertiel calculé par le steering (IA)
  
  masse = None #La masse de l'objet (utilisé pour les calculs d'accélération)
  vitesseDePillage = None #La vitesse à laquelle un sprite chope des ressources
  faciliteDePillage = None #Facteur de facilité à choper des ressources sur ce sprite

  echelle = None #Facteur d'échelle de l'objet en ce moment
  echelleOriginelle = None #Facteur d'échelle de l'objet lors de sa création == self.echelle à la sortie de __init__
  
  def __init__(self, id, position, fichierDefinition, joueur):
    """
    Fabrique un nouvel objet
    position : là où l'objet se trouve
    modele : le nom du fichier 3D à charger
    planete : la planète de laquelle cet objet dépend
    """
    general.TODO("Ajouter des sprites qui ne vivent que durant un certain temps (utile pour faire des cadavres et autres trucs qui disparaissent après un moment)")
    general.TODO("Ajouter la gestion des boulots")
    general.TODO("Ajouter sprite.regardeVers")
    general.TODO("Ajouter la gestion des animations de sprite")
    general.TODO("Support des objets non ponctuels")
    general.TODO("Faire dépendre la vitesse du sprite selon l'angle du sol sur lequel il se déplace")
    general.TODO("Gestion des barres de vie")
    general.TODO("Gestion d'une icone pour indiquer les activité (glandage, construction, baston, ...)")
    if joueur !=None:
      self.joueur = proxy(joueur)
    else:
      self.joueur = None
    self.id = id
    
    self.miseAJourPosition(position)
    
    self.modele = None
    self.tempsDeVie = 0.0
    self.inertie = Vec3(0.0,0.0,0.0)
    self.inertieSteering = Vec3(0.0,0.0,0.0)
    self.rac = NodePath("racine-sprite")
    self.rac.reparentTo(general.planete.geoide.racine)
    self.racine = NodePath("racine-sprite")
    self.racine.reparentTo(self.rac)
    #Tourne le modèle pour que sa tête soit en "haut" (Y pointant vers l'extérieur de la planète)
    self.racine.setP(90)
    self.racine.setScale(0.01)
    #On met en temps débile pour forcer un calcul dès le premier ping
    self.pileTempsAppliqueGraviteObjetsFixes = 1000.0
    self.majTempsOrientation = 1000000000
    self.majTempsOrientationMax = 0.1
    
    self.contenu={}
    self.taillePoches={}

    self.fichierDefinition = fichierDefinition
    #Charge les propriétés de l'objet depuis le fichier de définition du sprite
    if fichierDefinition!=None:
      definition = general.configuration.parseSprite(fichierDefinition)
      self.definition = definition
      self.fichierModele = definition["modele"]
      self.fichierSymbole = definition["symbole"]
      self.icone = definition["icone"]
      self.vie=definition["vie"]
      self.nocturne = definition["nocturne"]
      self.terminalVelocity = definition["terminalvelocity"]
      self.angleSolMax = general.configuration.getConfiguration("ai", "navigation", "angleSolMax", "70.0", float)
      self.distanceProche = definition["distanceProche"]
      self.seuilToucheSol = definition["seuilToucheSol"]
      self.constanteGravitationelle = definition["constanteGravitationelle"]
      self.vitesse = definition["vitesse"]
      self.distanceSymbole = definition["distancesymbole"]
      self.bouge = definition["bouge"]
      self.aquatique = definition["aquatique"]
      self.seuilRecalculPhysique = definition["seuilrecalculphysique"]
      self.masse = definition["masse"]
      self.echelle = definition["echelle"]
      self.echelleOriginelle = definition["echelle"]
      self.contenu["nourriture"] = definition["nourr"]
      self.contenu["construction"] = definition["constr"]
      self.stock = definition["stock"]
      self.taillePoches["nourriture"] = 50.0
      self.taillePoches["construction"] = 30.0
      self.vitesseDePillage = definition["vitesseDePillage"]
      self.faciliteDePillage = definition["faciliteDePillage"]
      self.dureeDeVie = definition["dureeDeVie"]
      #Si un sprite ne bouge pas, alors il n'a pas besoin d'AI (mais un sprite immobile (tour de guet) peut en avoir besoin, dans ce cas faire bouge=True, vitesse = 0.0)
      if definition["ai"] != "none" and self.bouge:
        self.ai = AI(self)
        #Charge un comportement tout fait
        self.ai.choisitComportement(definition["ai"])
        
  def stop(self):
    """Stoppe toutes les activités du sprite"""
    if self.ai:
      self.ai.stop()
    
  def pointeRacineSol(self):
    """Tourne la racine des éléments graphiques pour maintenir les "pieds" du sprite par terre"""
    #Positionne le modèle et le fait pointer vers le centre de la planète (Z pointant sur la planète)
    self.rac.setPos(*self.position)
    self.rac.lookAt(general.planete.geoide.racine,0,0,0)
    
  def ping(self, temps):
    """
    Appelé à chaque image, met à jour l'état de l'objet
    temps : le nombre de secondes depuis la dernière mise à jour
    """
    if general.io.selection!=None:
      if self in general.io.selection:
        #Le sprite est selectionné, afficher sa barre de vie
        if self.zoneSurbrillance:
          self.zoneSurbrillance.show()
        if self.barreDeVie:
          self.barreDeVie.show()
          #Donne la taille de la barre de bie
          self.barreDeVie.setScale(float(self.vie)/100, 1.0, 1.0)
          if self.vie>50:
            self.barreDeVie.setColor(0.0,1.0,0.0,0.75)
          else:
            self.barreDeVie.setColor(1.0,0.0,0.0,0.75)
      else:
        if self.zoneSurbrillance:
          self.zoneSurbrillance.hide()
        if self.barreDeVie:
          self.barreDeVie.hide()
    else:
      if self.zoneSurbrillance:
        self.zoneSurbrillance.hide()
      if self.barreDeVie:
        self.barreDeVie.hide()
        
    #On se casse pas la tête si le sprite est mort
    if self.vie<=0:
      return False
      
    #On vieillit le sprite
    self.tempsDeVie += temps
    if self.dureeDeVie < self.tempsDeVie and self.dureeDeVie > 0:
      self.tue("vieillesse", silence=False)
      return
      
    #On charge le modèle 3D si le sprite n'en a pas
    if self.modele==None:
      self.fabriqueModel()
      #On détruit le sprite si on a pas réussit à charger un modèle
      if self.modele==None:
        self.tue("Impossible de charger le modele")
    
    #Fait tomber
    self.appliqueGravite(temps)
    
    #On mouline l'AI
    if self.ai != None:
      self.ai.ping(temps)
      
    #Deplace
    self.appliqueInertie(temps)
      
    #On met à jour l'orientation du sprite
    self.majTempsOrientation+=temps
    if self.majTempsOrientation>self.majTempsOrientationMax:
      #Recalcule la verticale du modèle
      self.MAJSymbole()
      self.blip()
      self.majTempsOrientation = 0.0
      
    return True
    
  def majEchelle(self):
    """Recalcul le facteur d'échelle du sprite suivant son contenu"""
    facteur = 0.0
    
    #On regarde le %age de ressources restantes dans les poches du sprite
    for clef in self.contenu.keys():
      if self.taillePoches[clef]!=0.0:
        facteur = facteur + (self.contenu[clef]/self.taillePoches[clef])
    
    if facteur == 0.0:
      self.tue("Ressources épuisées")
    
    #Racine vaut none si l'objet a été détruit
    if self.racine==None or self.vie<=0:
      return
      
    #On change l'échelle
    self.echelle = self.echelleOriginelle*facteur
    self.modele.setScale(self.echelle)
    
  def piller(self, sprite, temps):
    """Prends des ressources dans les poches de 'sprite' pour les mettre dans les siennes"""
    #On regarde si on a atteint la cible à pic poquetter
    if (self.position - sprite.position).length()<=self.distanceProche:
      miam = {}
      peutContinuer=False
      print "Pillage :"
      for type in sprite.contenu.keys():
        stop=False
        
        #Le temps passer * la vitesse de récupération * le facteur de facilité de récupérage donne le volume récupéré pour le moment
        miam[type] = self.vitesseDePillage*sprite.faciliteDePillage*temps
        if sprite.contenu[type]<miam[type]:
          miam[type] = sprite.contenu[type]
          stop=True
          
        if self.taillePoches[type]<miam[type]+self.contenu[type]:
          miam[type] = self.taillePoches[type]-self.contenu[type]
          stop=True
          
        #Si on a pas totalement pillé tous les types de ressource, on continue à piller
        if not stop:
          peutContinuer=True
          
        sprite.contenu[type]-=miam[type]
        self.contenu[type]+=miam[type]
      sprite.majEchelle()
      
      print "pillé :",miam
      print "poches :",self.contenu
      print "restantes :",sprite.contenu
      if peutContinuer:
        return 1
      else:
        return -1
    else:
      return 0
      
  def videPoches(self, sprite, temps):
    """Dépose ses ressources dans le sprite"""
    #On regarde si on a atteint la cible à pic poquetter
    if (self.position - sprite.position).length()<=self.distanceProche:
      depot = {}
      peutContinuer=False
      print "Dépot :"
      for type in self.contenu.keys():
        stop=False
        
        #Le temps passer * la vitesse de récupération * le facteur de facilité de récupérage donne le volume récupéré pour le moment
        depot[type] = self.vitesseDePillage*sprite.faciliteDePillage*temps
        if self.contenu[type]<depot[type]:
          depot[type] = self.contenu[type]
          stop=True
          
        if sprite.taillePoches[type]<depot[type]+sprite.contenu[type]:
          depot[type] = sprite.taillePoches[type]-sprite.contenu[type]
          stop=True
          
        #Si on a pas totalement remplit le stock ou vidé ses poches
        if not stop:
          peutContinuer=True
          
        self.contenu[type]-=depot[type]
        sprite.contenu[type]+=depot[type]
      
      print "déposée :",depot
      print "poches :",self.contenu
      print "contenues :",sprite.contenu
      
      if peutContinuer:
        return 1
      else:
        return -1
    else:
      return 0
            
  def blip(self):
    """Met à jour le point sur la carte"""
    if self.blipid!=None:
      try:
        #On a un point sur la carte, donc on le met à jour
        general.interface.menuCourant.miniMap.majBlip(self.blipid,self.position,self.icone,self.joueur.couleur)
      except AttributeError:
        self.blipid=None
    else:
      try:
        #On a pas de point sur la carte mais on a une icône, on fabrique un nouveau point
        if self.icone != None and self.icone != "none":
          self.blipid = general.interface.menuCourant.miniMap.ajoutePoint3D(self.position,self.icone,self.joueur.couleur)
      except AttributeError:
        pass
  
  def testeSol(self, temps):
    """Regarde l'angle entre la normale de la face et le sprite qui s'y tient"""
    general.TODO("Debugger le teste d'inclinaison de sol")
    return
    sp = Vec3(position)
    sp.normalize()
    fc = general.planete.geoide.trouveFace(self.position).calculNormale()
    angle = sp.angleDeg(fc)
    if angle > self.angleSolMax:
      self.inertie = Vec3(self.inertie[0]+fc.getX()*temps, self.inertie[1]+fc.getY()*temps, self.inertie[2]+fc.getZ()*temps)
    
  def appliqueGravite(self, temps):
    """Fait tomber les objets sur le sol"""
    general.TODO("Debugger la gestion de la gravité")
    return
    altitudeCible = general.planete.geoide.altitudeCarre(self.position)
    if abs(self.altCarre-altitudeCible)>0.001:
      if self.altCarre<altitudeCible or not self.bouge or True:
        print self.id, self.altCarre, altitudeCible,"(",abs(self.altCarre-altitudeCible),")","->",
        sp = Vec3(self.position)
        sp.normalize()
        self.miseAJourPosition(sp * math.sqrt(altitudeCible))
        print self.altCarre, altitudeCible
      else:
        print self.id, self.altCarre, altitudeCible,"(",abs(self.altCarre-altitudeCible),")","-> VV",
        sp = Vec3(self.position)
        sp.normalize()
        haut = sp * (-self.constanteGravitationelle)
        alt = math.sqrt(self.altCarre)
        altci = math.sqrt(altitudeCible)
        if haut.length()>alt-altci:
          haut = Vec3(0.0,0.0,0.0)
          
        self.inertie+=haut
        print self.position, haut
        
    return
    self.testeSol(temps) #On est sur le sol, on teste si on peut se tenir debout dessus
      
  def appliqueGraviteObjetsFixes(self, temps):
    """Place les objets qui ne bougent pas sur le sol"""
    self.pileTempsAppliqueGraviteObjetsFixes+=temps
    
    if self.pileTempsAppliqueGraviteObjetsFixes<self.seuilRecalculPhysique+random.random():
      return
      
    self.pileTempsAppliqueGraviteObjetsFixes = 0.0
    
    altitudeCible = general.planete.geoide.altitudeCarre(self.position)
    if self.altCarre < altitudeCible or self.altCarre > altitudeCible + self.seuilToucheSol:
      #On place l'objet sur le sol d'un seul coup
      sp = Vec3(self.position)
      sp.normalize()
      self.miseAJourPosition(sp * math.sqrt(altitudeCible))
      self.inertie = Vec3(0.0,0.0,0.0)
      
  def appliqueInertie(self, temps):
    """Déplace l'objet selon le vecteur inertiel"""
    if self.inertie.lengthSquared()>self.terminalVelocity*self.terminalVelocity:
      self.inertie.normalize()
      self.inertie = self.inertie * self.terminalVelocity
    self.regardeVers(self.position+(self.inertie*temps+self.inertieSteering)*2)
    self.miseAJourPosition(self.position+self.inertie*temps+self.inertieSteering)
    self.inertieSteering = Vec3(0.0,0.0,0.0)
    self.inertie=self.inertie*0.7
    
  def versCoord(self, cible):
    """Si cible est une coordonnée, retourne cette dernière, sinon extrait les coordonnées"""
    try:
      cible = list(cible)
    except TypeError:
      cible=[cible, ]
      
    if len(cible)==1:
      cible = general.planete.geoide.sommets[cible[0]]

    return cible
      
  def deplace(self, cible, temps):
    """
    Déplace un personnage entre 2 points
    """
    cible = self.versCoord(cible)
      
    sp = cible - self.position
    sp.normalize()
    
    vecteurDeplacement = sp * self.vitesse*temps
    
    self.position = (self.position[0] + vecteurDeplacement[0], self.position[1] + vecteurDeplacement[1], self.position[2] + vecteurDeplacement[2])
    self.miseAJourPosition(self.position)
      
  def miseAJourPosition(self, position):
    """Change la position de l'objet"""
    self.position = position
      
    self.altCarre = self.position.lengthSquared()
    if self.altCarre < general.planete.geoide.niveauEau*general.planete.geoide.niveauEau:
      if self.aquatique:
        #Nage
        pass
      else:
        #Se noie
        self.tue("noyade")
    if self.modele != None:
      self.pointeRacineSol()
    pass
      
  def tue(self, type, silence=False):
    """Gère la mort du sprite"""
    general.TODO("Gestion des types de destructions de sprite : fin de partie, joueur a perdu, noyade, incendie, ...")
    general.TODO("Ajouter les ruines et les cadavres")
    self.stop()
    if not silence:
      general.interface.afficheTexte("%(a)s est mort par %(b)s", parametres={"a": general.i18n.utf8ise(self.id), "b": general.i18n.utf8ise(type)}, type="mort")
    self.vie = 0
    self.typeMort = type
    if self.rac!=None:
      self.rac.detachNode()
      self.rac.removeNode()
      self.rac = None
    if self.racine!=None:
      self.racine.detachNode()
      self.racine.removeNode()
      self.racine = None
    if self.modele!=None:
      self.modele.detachNode()
      self.modele.removeNode()
      self.modele = None
    self.symbole = None
    if self.blipid!=None:
      if general.interface.menuCourant!=None:
        if general.interface.menuCourant.miniMap!=None:
          general.interface.menuCourant.miniMap.enlevePoint(self.blipid)
    if self.ai != None:
      self.ai.clear()
      self.ai = None
    while self in general.planete.spritesNonJoueur:
      general.planete.spritesNonJoueur.remove(self)
    while self in general.planete.spritesJoueur:
      general.planete.spritesJoueur.remove(self)
    while self in general.io.selection:
      general.io.selection.remove(self)
    
  def sauvegarde(self):
    """Retoune une chaine qui représente l'objet"""
    nom = "none"
    if self.joueur != None:
      nom = self.joueur.nom
    out = "sprite:"+self.id+":"+nom+":"+self.fichierModele+":"+self.fichierSymbole
    out += ":"+str(self.position)+":"+str(self.vitesse)+":"+str(self.vie)+":"+str(self.bouge)+":"+str(self.aquatique)+":"+str(self.dureeDeVie)+":"+str(self.tempsDeVie)+":"+str(self.fichierDefinition)+":\r\n"
    if self.ai != None:
      out += self.ai.sauvegarde()
    if self.contenu != None:
      for element in self.contenu.keys():
        out += "sprite-contenu:"+self.id+":"+element+":"+str(self.contenu[element])+":\r\n"
    return out
    
  def __repr__(self):
    """"""
    nom = "none"
    if self.joueur != None:
      nom = self.joueur.nom
    return "sprite:"+self.id+":"+nom+":"+self.fichierModele+":"+self.fichierSymbole+":"+str(self.position)+":"+str(self.vitesse)+":"+str(self.vie)+":"+str(self.bouge)+":"+str(self.aquatique)
    
  def _syncCheck(self):
    return self.sauvegarde()
    
  def regardeVers(self, cible):
    h,p,r = self.modele.getHpr()
    self.modele.lookAt(*self.versCoord(cible))
    h=self.modele.getH()
    self.modele.setHpr(h,p,r)
    
  def marcheVers(self, cible):
    """Calcule la trajectoire pour aller du point actuel à la cible"""
    
    #Si y a pas d'ai, on a pas besoin de perdre son temps avec ^^
    if self.ai==None:
      return
    self.ai.comportement.calculChemin(self.position, cible, 0.75)
    
  def suitChemin(self, chemin, fin):
    """Suit un chemin"""
    #Si y a pas d'ai, on a pas besoin de perdre son temps avec ^^
    if self.ai==None:
      return
    self.ai.comportement.suitChemin(chemin, fin, 0.75)
    
  def fabriqueModel(self):
    """Produit le modèle ou le sprite"""
    if self.vie <=0:
      return None
      
    self.modele = NodePath(FadeLODNode('lod'))
    
    if self.fichierModele == None or self.fichierModele=="none":
      self.modele = None
      return
    
    fichierCarte = self.fichierModele[:-4]+"-card.txt"
    if os.path.exists(fichierCarte):
      general.TODO("Charger les images "+self.fichierModele[:-4]+"-1.png... pour faire un lod")
      
    if self.fichierModele.endswith(".png"):
      tmp = self.fabriqueSprite(self.fichierModele)
    else:
      tmp = loader.loadModel(self.fichierModele)
    
    if self.joueur!=None:
      self.ajouteZoneSurbrillance().reparentTo(tmp)
    self.ajouteBarreVie().reparentTo(tmp)
    
    tmp.reparentTo(self.modele)
    self.modele.setScale(self.echelle)
    self.modele.node().addSwitch(self.distanceSymbole, 0) 
    
    symbole = self.fabriqueSymbole(self.fichierSymbole)
    symbole.reparentTo(self.modele)
    
    self.modele.node().addSwitch(9999999, self.distanceSymbole) 
    
    self.modele.setPythonTag("type","sprite")
    self.modele.setPythonTag("id",self.id)
    self.modele.setPythonTag("instance",self)
    self.modele.reparentTo(self.racine)
    #Tourne le modèle pour que sa tête soit en "haut" (Y pointant vers l'extérieur de la planète)
    self.racine.setP(90)
    self.racine.setScale(0.01)
    self.pointeRacineSol()
    return self.modele
    
  def ajouteBarreVie(self):
    cardMaker = CardMaker('barreDeVie')
    cardMaker.setFrame(-0.5, 0.5, 0.0, 0.1)
    cardMaker.setHasNormals(True)
  
    #Construit une carte (un plan)
    self.barreDeVieRacine = NodePath("barreDeVie")
    self.barreDeVie = self.barreDeVieRacine.attachNewNode(cardMaker.generate())
    self.barreDeVie.setTexture(loader.loadTexture("./theme/progress-top.png"))
    self.barreDeVie.hide()
    self.barreDeVie.setBillboardAxis()
    self.barreDeVie.setPos(0.0, 0.0, 1.0)
    self.barreDeVie.setTransparency(TransparencyAttrib.MDual)
    return self.barreDeVie
    
  def ajouteZoneSurbrillance(self):
    cardMaker = CardMaker('surbrillance')
    cardMaker.setFrame(-0.5, 0.5, -0.5, 0.5)
    cardMaker.setHasNormals(True)
  
    #Construit une carte (un plan)
    racine = NodePath("surbrillance")
    self.zoneSurbrillance = racine.attachNewNode(cardMaker.generate())
    self.zoneSurbrillance.setTexture(loader.loadTexture("./data/textures/soleil.png"))
    self.zoneSurbrillance.hide()
    if self.joueur!=None:
      self.zoneSurbrillance.setColor(*self.joueur.couleur)
    self.zoneSurbrillance.setP(-90)
    self.zoneSurbrillance.setTwoSided(True)
    self.zoneSurbrillance.setTransparency(TransparencyAttrib.MDual)
    return self.zoneSurbrillance

  def fabriqueSymbole(self, fichierSymbole):
    """Affiche une icône dont la taille ne change pas avec la distance à la caméra"""
    
    if fichierSymbole=="none":
      self.symbole=NodePath("pas de symbole")
      return self.symbole
    #On calcule la distance à la caméra pour avoir le facteur de corection d'échelle
    if base.camera != None:
      taille = base.camera.getPos(self.modele).length()
    else:
      taille = 1.0
    #On construit l'objet
    self.symbole = self.fabriqueSprite(fichierSprite = fichierSymbole, taille = taille)
    #On lui dit de ne pas être dérangé par les sources lumineuses
    self.symbole.setLightOff()
    
    #Permet de l'afficher devant toute géométrie
    #self.symbole.setBin('fixed', -1)
    #self.symbole.setDepthTest(False)
    #self.symbole.setDepthWrite(False)

    return self.symbole
    
  def MAJSymbole(self):
    """Change l'échelle du symbole pour le garder toujours à la même taille"""
    if self.symbole!=None and self.racine!=None and self.echelle!=0:
      #On calcule la distance à la caméra pour avoir le facteur de corection d'échelle
      taille = general.io.camera.getPos(self.racine).length()
      #On change l'échelle
      self.symbole.setScale(taille*0.005, taille*0.005, taille*0.005)
    
    
  def makeDot(self):
    """Dessine un carré 2D en utilisant directement la puissance de la carte graphique"""
    gvf = GeomVertexFormat.getV3cp()

    # Create the vetex data container.
    vertexData = GeomVertexData('SpriteVertices',gvf,Geom.UHStatic)

    # Create writers
    vtxWriter = GeomVertexWriter(vertexData,'vertex')
    clrWriter = GeomVertexWriter(vertexData,'color') 
    vtxWriter.addData3f(0.0,0.0,0.0)
    clrWriter.addData3f(1,1,1) 
       
    # Create a GeomPrimitive object and fill with the vertices.
    geom = Geom(vertexData)
    points = GeomPoints(Geom.UHStatic)
    points.setIndexType(Geom.NTUint32)
    points.addVertex(0)

    points.closePrimitive()
    geom.addPrimitive(points)
    geomNode = GeomNode('Sprites')
    geomNode.addGeom(geom)
    cloud = NodePath(geomNode)
    cloud.setRenderModePerspective(True)
    #cloud.setRenderModeThickness(1.0)
    TS = TextureStage.getDefault()
    cloud.setTexGen(TS, TexGenAttrib.MPointSprite)
    #cloud.setTexScale(TS,-1,1) 
    return cloud
    
  def fabriqueSprite(self, fichierSprite, taille=1.0, type="carte"):
    """Construit un nouveau sprite"""
    
    racine = NodePath("sprite")
    
    if type=="carte":
      #Fabrique un carré
      cardMaker = CardMaker('sprite')
      cardMaker.setFrame(-0.5, 0.5, 0.0, 1.0)
      cardMaker.setHasNormals(True)
    
      #Construit une carte (un plan)
      card1 = racine.attachNewNode(cardMaker.generate())
      #On fait tourner la carte pour quelle pointe toujours vers la caméra
      #Elle rotationne autour d'un axe uniquement (garde ses pieds vers le sol)
      card1.setBillboardAxis()
    elif type=="point":
      card1 = self.makeDot()
      card1.reparentTo(racine)
    else:
      print "SPRITE :: Erreur :: type de carte inconnu :", type
      return self.fabriqueSprite(fichierSprite=fichierSprite, taille=1.0, type="carte")
      
    tex = loader.loadTexture(fichierSprite)
    card1.setTexture(tex)
    #Active la transprence
    card1.setTransparency(TransparencyAttrib.MDual)
    #Fait une mise à l'échelle
    card1.setScale(taille, taille, taille)
    
    #Les lignes suivantes font dessiner le sprite au dessus de tout le reste
    #Utile pour débugger
    #card1.setBin('fixed', -1)
    #card1.setDepthTest(False)
    #card1.setDepthWrite(False)
    return racine
    
  def dessineLigne(self, couleur, depart, arrivee):
    """Dessine une ligne de depart vers arrivée et ne fait pas de doublons"""
    ls = LineSegs()
    ls.setColor(*couleur)
    ls.setThickness(1.0)
    ls.moveTo(*depart)
    ls.drawTo(*arrivee)
    return ls.create()

class SpritePlan(Sprite):
  """Support d'objets non ponctuels"""
  point1 = None
  point2 = None
  
  def __init__(self, id, point1, point2, modele, symbole, joueur):
    self.point1, self.point2, position = self.preparePoints(point1, point2)
    
    Sprite.__init__(self, id, position, modele, symbole, joueur)

  def preparePoints(self, point1, point2):
    point1 = (min(point1[0], point2[0]), min(point1[1], point2[1]), min(point1[2], point2[2]))
    point2 = (max(point1[0], point2[0]), max(point1[1], point2[1]), max(point1[2], point2[2]))
    position = (point1[0]+point2[0])/2.0, (point1[1]+point2[1])/2.0, (point1[2]+point2[2])/2.0
    return point1, point2, position

  def miseAJourPosition(self, point1, point2):
    self.point1, self.point2, position = self.preparePoints(point1, point2)
    Sprite.miseAJourPosition(self, position)
    
  def testeSol(self):
    Sprite.testeSol(self)

class Nuage(Sprite):
  """Génère un nuage aléatoirement"""
  densite = None
  
  def __init__(self, densite, taille):
    Sprite.__init__(self, id="nuage", position=Vec3(0.01,0.01,0.01), fichierDefinition=None, joueur=None)
    self.densite = densite
    self.taille = taille
    self.vie=100
    
  def tue(self, type, silence=False):
    """Un nuage ne peut pas mourrir"""
    return
    #if type=="noyade":
    #  return
    #else:
    #  Sprite.tue(self, type)
    
  def ping(self, temps):
    """Les nuages ne sont pas affectés par la gravité"""
    self.deplace(temps)
    #self.blip()
    if self.vie<=0:
      return True
    return True
    
  def blip(self):
    """Les nuages n'apparaissent pas sur le radar"""
    pass
    
  def deplace(self, temps):
    """Promène le nuage sur l'écran"""
    if self.racine == None or self.modele==None:
      return
    #Modele est centré sur la planète, donc les rotations le promènent un peu tout autour
    f = random.random()*3 -1.0
    self.modele.setH(self.modele.getH()+random.random()*temps*f/30)
    self.modele.setP(self.modele.getP()+random.random()*temps*f/30)
    self.modele.setR(self.modele.getR()+random.random()*temps*f/30)
    #Faire tourner la racine change le profile du nuage présenté à la caméra et donc sa forme pour donner l'impression qu'il évolue
    f=2.5
    self.racine.setH(self.racine.getH()+random.random()*temps*f/30)
    self.racine.setP(self.racine.getP()+random.random()*temps*f/30)
    self.racine.setR(self.racine.getR()+random.random()*temps*f/30)
    self.position = self.n1.getPos(general.planete.geoide.racine)
    
  def fabriqueModel(self):
    """Construit le nuage"""
    #Choisit une position du nuage selon un sommet aléatoire
    centre = random.choice(general.planete.geoide.sommets)
    
    #Facteur d'étalement du nuage selon les 3 axes en espace monde
    dx, dy, dz = 1.2,1.2,1.2
    fact = Vec3(dx, dy, dz).length()
        
    distanceSoleil = general.planete.distanceSoleil
        
    #Place le "centre" du nuage
    self.modele = NodePath("nuage")#NodePath(FadeLODNode('nuage'))
    ct = Vec3(centre)
    ct.normalize()
    
    self.modele.setPos(ct * (general.planete.geoide.niveauCiel-0.01))
    self.racine = NodePath("nuage-elem")
    self.racine.reparentTo(self.rac)
    
    import os
    textures = os.listdir(os.path.join(".","data","textures","nuages"))
    
    #Ajoute les prouts nuageux un par un
    for i in range(0, self.densite):
      #Fabrique un nouveau prout
      nuage = NodePath(FadeLODNode('lod'))
      tex="./data/textures/nuages/"+random.choice(textures)
      self.fabriqueSprite(tex, taille=1, type="point").reparentTo(nuage)
      if i==0:
        nuage.node().addSwitch(99999, 0) 
        self.n1=nuage
      else:
        nuage.node().addSwitch(float(i)/float(self.densite)*distanceSoleil, 0) 
        
      #nuage.setBillboardPointWorld()
      
      #On le décale par rapport au "centre"
      if i!=0:
        r = (random.random()*dx, random.random()*dy, random.random()*dz)
      else:
        #mais on garde le tout premier "prout" au milieu
        r = (0.0, 0.0, 0.0)
        
      #On coince le nuage dans le ciel
      rn = Vec3(r)
      rn.normalize()
      v=rn * (general.planete.geoide.niveauCiel-0.01+(general.planete.geoide.niveauCiel-general.planete.geoide.delta-1.0)*random.random())
      r = v-centre
      nuage.setPos(*r)
      
      #On diminue la taille du prout s'il est loin du centre
      nuage.setScale(max(fact-r.length(), 0.001*fact)/fact)
      #On diminue l'opacité du prout s'il est loin du centre
      nuage.setAlphaScale(max(fact-r.length(), 0.001*fact)/fact)
      nuage.reparentTo(self.racine)
    self.racine.reparentTo(self.modele)
    #On redimentionne le bestiau
    self.modele.setScale(self.taille)
    #On optimise les envois à la carte graphique
    self.racine.flattenStrong()
    self.modele.reparentTo(general.planete.geoide.racine)
    #self.modele.setBin('fixed', -1)
    #self.modele.setDepthTest(False)
    #self.modele.setDepthWrite(False)
    self.modele.setLightOff()
    
    return self.modele
    
  def sauvegarde(self):
    """Les nuages ne sont là que pour faire joli"""
    return "\r\n"
    
  def __repr__(self):
    """"""
    return "nuage"
    
  def _syncCheck(self):
    return ""

