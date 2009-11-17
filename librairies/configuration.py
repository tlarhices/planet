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
    
  def charge(self, fichier):
    """Charge un fichier de configuration"""
    section = None
    self.fichierConfig = fichier
    fichier = open(fichier, "r")
    for ligne in fichier:
      ligne = ligne.strip().lower() #On passe tout en minuscule
      if len(ligne)>0 and ligne[0]!="#": #On saut les lignes vides ou commençant par #
        if ligne[-1] == ":": #Si la ligne se finit par : alors c'est une section
          section = ligne[:-1].strip()
        else: #Si la ligne ne se termine pas par : alors ce sont des infos
          if section == None:
            print "Configuration hors catégorie : ",ligne
          else:
            a,b = ligne.split("=")
            a = a.strip()
            b = b.strip()
            if not section in self.configuration.keys():
              self.configuration[section]={}
            self.configuration[section][a]=b
    
  def sauve(self, fichier):
    """Sauvegarde un fichier de configuration (ne garde pas les commentaires)"""
    fichier = open(fichier, "w")
    for section in self.configuration.keys():
      fichier.write(str(section)+":\r\n")
      for element in self.configuration[section].keys():
        fichier.write(str(element)+" = "+str(self.configuration[section][element])+"\r\n")
    fichier.write("\r\n")
    
  def getConfigurationClavier(self):
    """Retourne la configuration du clavier"""
    return self.configuration["clavier"]
    
  def getConfiguration(self, section, champ, defaut):
    """Retourne une valeur de configuration"""
    section=str(section).lower()
    champ=str(champ).lower()
    
    if section not in self.configuration.keys():
      print "Section pas dans le fichier de configuration",section
      return defaut
    if champ not in self.configuration[section].keys():
      print "Section::champ pas dans le fichier de configuration",section,champ
      return defaut
      
    return self.configuration[section][champ]