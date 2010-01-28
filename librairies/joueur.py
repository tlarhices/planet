#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general
import math
import os
from sprite import *

class Joueur:
  """Contient tout les éléments associés à un joueur"""
  nom = None #Le nom unique du joueur
  couleur = None #La couleur du joueur
  sprites = None #La liste des sprites que ce joueur possède
  ressources = None #Les ressources que le joueur possède
  gui = None
  type = None
  
  def __init__(self, nom, couleur):
    """
    Gère un nouveau joueur
    nom : nom unique du joueur
    couleur : couleur du joueur
    """
    self.nom = nom
    self.couleur = couleur
    
    #Le joueur n'a pas de sprites
    self.sprites = []
    
    self.ressources = {"bouffe":10}

  def pingJoueur(self, temps):
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
    fichier = os.path.join(".","data","sprites",type+".spr")
    if not os.path.exists(fichier):
      print "Sprite inconnu",type, "->", fichier
    id = "{S:"+self.nom+"}"+id+"-"+str(len(self.sprites)+1)
    sprite = Sprite(id=id, position=position, fichierDefinition=fichier, joueur=self)
    noms = open(os.path.join(".","data","noms","noms")).readlines()
    prenoms = open(os.path.join(".","data","noms","prenoms")).readlines()
    sprite.nom = random.choice(noms).strip()+" "+random.choice(prenoms).strip()
    general.planete.spritesJoueur.append(sprite)
    self.sprites.append(sprite)
    
  def spriteMort(self, sprite):
    if sprite.typeMort=="obscurite":
      general.interface.alerte(message="%(a)s est mort par %(b)s", parametres={"a":sprite.id, "b":sprite.typeMort}, type="obscurite", coord=sprite.position)
    else:
      general.interface.alerte(message="%(a)s est mort par %(b)s", parametres={"a":sprite.id, "b":sprite.typeMort}, type="mort", coord=sprite.position)
    self.sprites.remove(sprite)
    
  def detruit(self):
    """Supprime le joueur et tout ce qui lui est associé"""
    for sprite in self.sprites:
      sprite.tue("destruction du joueur")
      
  def sauvegarde(self):
    out = "joueur:"+str(self.type)+":"+self.nom+":"+str(self.couleur)+":"+str(general.interface.joueur==self)+":\r\n"
    for ressource in self.ressources.keys():
      out += "joueur-ressource:"+self.nom+":"+ressource+":"+str(self.ressources[ressource])+":\r\n"
    return out
      
class JoueurLocal(Joueur):
  """Le joueur devant le clavier"""
  premierPing=None
  
  def __init__(self, nom, couleur):
    Joueur.__init__(self, nom, couleur)
    self.type="local"
    #Définit globalement qui est le joueur local
    general.joueurLocal = proxy(self)
    self.premierPing = True
    
  def pingJoueur(self, temps):
    Joueur.pingJoueur(self, temps)
    #On ne fait que ce qui suit au premier ping
    if self.premierPing:
      #Vire le menu "chargement" et affiche le menu en jeu
      general.interface.ajouteJoueur(self)
      #Met à jour la position de la caméra
      general.io.positionneCamera()
      self.premierPing = False

class JoueurDistant(Joueur):
  """Un joueur qui provient du réseau, peut-être humain ou une IA qui est sur une autre machine"""
  def __init__(self, nom, couleur):
    Joueur.__init__(self, nom, couleur)
    self.type="distant"

class JoueurIA(Joueur):
  """Une IA contrôlée sur cette machine"""
  def __init__(self, nom, couleur):
    Joueur.__init__(self, nom, couleur)
    self.type="ia"
