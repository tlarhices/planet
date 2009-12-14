#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import general

import os
import sys

class Configuration:
  """Gère le fichier de configuration"""
  configuration = None
  fichierConfig = None
  
  def __init__(self):
    self.configuration = {}
    
  def charge(self, fichier, erreurSiExistePas=True):
    """Charge un fichier de configuration"""
    section = None
    soussection = None
    
    if not os.path.exists(fichier):
      if erreurSiExistePas:
        print "CONFIGURATION :: ERREUR :"
        raw_input("Le fichier de configuration '"+fichier+"' n'existe pas.")
      return
    
    self.fichierConfig = fichier
    fichier = open(fichier, "r")
    for ligne in fichier:
      ligne = ligne.strip().lower() #On passe tout en minuscule
      if len(ligne)>0 and ligne[0]!="#": #On saut les lignes vides ou commençant par #
        if ligne.startswith("[[") and ligne.endswith("]]"): #Si la ligne est de la forme [[****]] alors c'est une section
          section = ligne[2:-2].strip()
          soussection = None
        elif ligne.endswith(":"): #Si la ligne se finit par : alors c'est une soussection
          soussection = ligne[:-1].strip()
        else: #Si la ligne ne se termine pas par : alors ce sont des infos
          if section == None:
            print "Configuration hors catégorie : ",ligne
          else:
            a,b = ligne.split("=")
            a = a.strip()
            b = b.strip()
            if not section in self.configuration.keys():
              self.configuration[section]={}
            if not soussection in self.configuration[section].keys():
              self.configuration[section][soussection]={}
            self.configuration[section][soussection][a]=b
    
  def sauve(self, fichier):
    """Sauvegarde un fichier de configuration (ne garde pas les commentaires)"""
    def versStr(valeur):
      if isinstance(valeur, bool):
        return str(valeur)[0]
      return str(valeur)
      
    fichier = open(fichier, "w")
    for section in self.configuration.keys():
      fichier.write("[["+str(section)+"]]\r\n")
      for soussection in self.configuration[section].keys():
        fichier.write(str(soussection)+":\r\n")
        for element in self.configuration[section][soussection].keys():
          fichier.write(str(element)+" = "+versStr(self.configuration[section][soussection][element])+"\r\n")
        fichier.write("\r\n")
    fichier.write("\r\n")
    
  def getConfigurationClavier(self):
    """Retourne la configuration du clavier"""
    out = {}
    if "commandes" not in self.configuration.keys():
      print "ERREUR:getConfigurationClavier :: pas de touches configurées"
      return {}
    for clef in self.configuration["commandes"]["clavier"]:
      out[clef]=self.configuration["commandes"]["clavier"][clef]
    for clef in self.configuration["commandes"]["souris"]:
      out[clef]=self.configuration["commandes"]["souris"][clef]
    return out
    
  def parseSprite(self, fichier):
    sprite={}
    self.fichierConfig = fichier
    fichier = open(fichier, "r")
    for ligne in fichier:
      ligne = ligne.strip().lower() #On passe tout en minuscule
      if ligne[0]!="#":
        a,b = ligne.split("=")
        a = a.strip()
        b = b.strip()
        sprite[a]=b
      
    def config(tab, clef, type, defaut):
      clef=clef.lower().strip()
      if not clef in tab.keys():
        return defaut
      else:
        return type(tab[clef])
        
    sprite["modele"] = config(sprite, "modele", str, "none")
    sprite["symbole"]  = config(sprite, "symbole", str, "none")
    sprite["icone"] = config(sprite, "icone", str, "theme/icones/q.png")
    sprite["icone-actif"] = config(sprite, "icone-actif", str, "theme/icones/q-over.png")
    sprite["icone-inactif"] = config(sprite, "icone-inactif", str, "theme/icones/q.png")
    sprite["vie"] = config(sprite, "vie", float, 100.0)
    sprite["nocturne"] = config(sprite, "nocturne", str, "f")=="t"
    sprite["terminalvelocity"] = config(sprite, "terminalvelocity", float, 0.03)
    sprite["distanceProche"] = config(sprite, "distanceProche", float, 0.002)
    sprite["seuilToucheSol"] = config(sprite, "seuilToucheSol", float, 0.01)
    sprite["constanteGravitationelle"] = config(sprite, "constanteGravitationelle", float, 0.01)
    sprite["vitesse"] = config(sprite, "vitesse", float, 0.01)
    sprite["distancesymbole"] = config(sprite, "distancesymbole", float, 3.0)
    sprite["bouge"] = config(sprite, "bouge", str, "t")=="t"
    sprite["aquatique"] = config(sprite, "aquatique", str, "f")=="t"
    sprite["constructible"] = config(sprite, "constructible", str, "f")=="t"
    sprite["ai"] = config(sprite, "ai", str, "standard")
    sprite["seuilrecalculphysique"] = config(sprite, "seuilrecalculphysique", float, 2.0)
    sprite["masse"] = config(sprite, "masse", float, 1.0)
    sprite["echelle"] = config(sprite, "echelle", float, 1.0)
    sprite["nourr"] = config(sprite, "nourr", int, 0)
    sprite["constr"] = config(sprite, "constr", int, 0)
      
    return sprite
    
  def effacePlanete(self):
    return
    for clef in self.configuration.keys()[:]:
      del self.configuration[clef]
      
  def setConfiguration(self, section, sousection, champ, valeur):
    section=str(section).lower()
    champ=str(champ).lower()
    
    if not section in self.configuration.keys():
      self.configuration[section]={}
    if not soussection in self.configuration[section].keys():
      self.configuration[section][soussection]={}
    self.configuration[section][soussection][champ]=valeur
    
    
  def getConfiguration(self, section, soussection, champ, defaut):
    """Retourne une valeur de configuration"""
    section=str(section).lower()
    soussection=str(soussection).lower()
    champ=str(champ).lower()
    
    if section not in self.configuration.keys():
      print self.configuration.keys()
      print "getConfiguration::section pas dans le fichier de configuration ::",section
      raw_input("pause_configuration")
      self.configuration[section]={}
      self.configuration[section][soussection]={}
      self.configuration[section][soussection][champ]=defaut
      return defaut
    if soussection not in self.configuration[section].keys():
      print self.configuration.keys()
      print "getConfiguration::sous-section pas dans le fichier de configuration ::",section, soussection
      raw_input("pause_configuration")
      self.configuration[section][soussection]={}
      self.configuration[section][soussection][champ]=defaut
      return defaut
    if champ not in self.configuration[section][soussection].keys():
      print "getConfiguration::champ pas dans le fichier de configuration ::",section, soussection, champ
      raw_input("pause_configuration")
      self.configuration[section][soussection][champ]=defaut
      return defaut
      
      
    return self.configuration[section][soussection][champ]
