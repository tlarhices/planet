#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general
import math
from sprite import *

class Joueur:
  """Contient tout les éléments associés à un joueur"""
  
  planetePrincipale = None #L'instance de la planète mère
  nom = None #Le nom unique du joueur
  couleur = None #La couleur du joueur
  sprites = None #La liste des sprites que ce joueur possède
  ressources = None #Les ressources que le joueur possède
  gui = None
  type = None
  
  def __init__(self, nom, couleur, besoinGUI, planetePrincipale):
    """
    Gère un nouveau joueur
    nom : nom unique du joueur
    couleur : couleur du joueur
    planetePrincipale : l'instance de la planète
    """
    
    self.nom = nom
    self.couleur = couleur
    
    #On garde un pointeur sur la vraie planète
    self.planetePrincipale = planetePrincipale
    
    #On fabrique une planète vide
    #self.planete = Planete()
    #self.planete.fabriqueNouvellePlanete(tesselation = self.planetePrincipale.tesselation, delta=0.0)
    
    #Le joueur n'a pas de sprites
    self.sprites = []
    
    self.ressources = {"bouffe":10}
    
    if besoinGUI:
      general.gui.ajouteJoueur(self)

  def ping(self, temps):
    #Calcul la zone en vue du joueur
    #Synchronise la planète courante avec la la vraie planète
    #Le ping des sprite est géré par la planète
    pass
    
  def ajouteSprite(self, id, position, type):
    """
    Ajoute un nouveau sprite
    id : l'identifiant du sprite
    position : sa position sur le terrain
    type : le type de sprite à créer
    """
    modele=general.configuration.getConfiguration("sprites-"+type.strip().lower(), "modele",None)
    symbole=general.configuration.getConfiguration("sprites-"+type.strip().lower(), "symbole",None)
    icone=general.configuration.getConfiguration("sprites-"+type.strip().lower(), "icone-inactif",None)
    vie=float(general.configuration.getConfiguration("sprites-"+type.strip().lower(), "vie","100.0"))
    distanceSymbole=float(general.configuration.getConfiguration("sprites-"+type.strip().lower(), "distanceSymbole","3.0"))
    terminalVelocity=float(general.configuration.getConfiguration("sprites-"+type.strip().lower(), "terminalVelocity","0.03"))
    distanceProche=float(general.configuration.getConfiguration("sprites-"+type.strip().lower(), "distanceProche","0.002"))
    seuilToucheSol=float(general.configuration.getConfiguration("sprites-"+type.strip().lower(), "seuilToucheSol","0.01"))
    constanteGravitationelle=float(general.configuration.getConfiguration("sprites-"+type.strip().lower(), "constanteGravitationelle","0.01"))
    vitesse=float(general.configuration.getConfiguration("sprites-"+type.strip().lower(), "vitesse","0.01"))
    nocturne=general.configuration.getConfiguration("sprites-"+type.strip().lower(), "nocturne","0")=="1"
    
    if modele==None or symbole==None:
      print "Joueur::ajouteSprite - type inconnu", type
      raw_input()
      return
    
    id = "["+self.nom+"]"+id+"-"+str(len(self.sprites)+1)
    sprite = Sprite(id=id, position=position, modele=modele, symbole=symbole, icone=icone, distanceSymbole=distanceSymbole, vie=vie, terminalVelocity=terminalVelocity, distanceProche=distanceProche, seuilToucheSol=seuilToucheSol, constanteGravitationelle=constanteGravitationelle, nocturne=nocturne, vitesse=vitesse, planete=self.planetePrincipale, joueur=self)
    self.planetePrincipale.sprites.append(sprite)
    self.sprites.append(sprite)
    sprite.fabriqueModel()
    
  def spriteMort(self, sprite):
    #general.gui.afficheTexte("Joueur "+self.nom+" dit : :'( :'( pauvre "+sprite.id, "chat")
    general.gui.menuCourant.alerte("mort", sprite.id+" est mort par "+sprite.typeMort, sprite.position)
    if sprite.typeMort=="obscurite":
      general.gui.menuCourant.alerte("obscurite", sprite.id+" est mort par "+sprite.typeMort, sprite.position)
    self.sprites.remove(sprite)
    
  def detruit(self):
    """Supprime le joueur et tout ce qui lui est associé"""
    for sprite in self.sprites:
      sprite.tue("destruction du joueur")
      
  def sauvegarde(self):
    out = "j:"+str(self.type)+":"+self.nom+":"+str(self.couleur)+":"+str(general.gui.joueur==self)+":\r\n"
    for ressource in self.ressources.keys():
      out += "jr:"+self.nom+":"+ressource+":"+str(self.ressources[ressource])+":\r\n"
    return out
      
class JoueurLocal(Joueur):
  """Le joueur devant le clavier"""
  def __init__(self, nom, couleur, planetePrincipale):
    Joueur.__init__(self, nom, couleur, True, planetePrincipale)
    self.type="local"

class JoueurDistant(Joueur):
  """Un joueur qui provient du réseau, peut-être humain ou une IA qui est sur une autre machine"""
  def __init__(self, nom, couleur, planetePrincipale):
    Joueur.__init__(self, nom, couleur, False, planetePrincipale)
    self.type="distant"

class JoueurIA(Joueur):
  """Une IA contrôlée sur cette machine"""
  def __init__(self, nom, couleur, planetePrincipale):
    Joueur.__init__(self, nom, couleur, False, planetePrincipale)
    self.type="ia"
