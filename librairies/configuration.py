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
    prefixe = fichier.split("/")[-1].split("\\")[-1][:-4]
    
    if not os.path.exists(fichier):
      print "CONFIGURATION :: ERREUR :"
      raw_input("Le fichier de configuration '"+fichier+"' n'existe pas.")
      return
    
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
            if not prefixe+"-"+section in self.configuration.keys():
              self.configuration[prefixe+"-"+section]={}
            self.configuration[prefixe+"-"+section][a]=b
    
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
    out = {}
    for clef in self.configuration["commandes-clavier"]:
      out[clef]=self.configuration["commandes-clavier"][clef]
    for clef in self.configuration["commandes-souris"]:
      out[clef]=self.configuration["commandes-souris"][clef]
    return out
    
  def getConfigurationSprite(self):
    liste=[]
    noms = []
    for section in self.configuration.keys():
      if section.startswith("sprites-"):
        if self.getConfiguration(section, "constructible", "0")=="1":
          nom = self.getConfiguration(section, "nom", section[7:])
          if nom not in noms:
            noms.append(nom)
          liste.append((nom,int(self.getConfiguration(section, "constr", "-1")),int(self.getConfiguration(section, "nourr", "-1")),self.getConfiguration(section, "icone-actif", "rtheme/twotone/q-over.png"), self.getConfiguration(section, "icone-inactif", "rtheme/twotone/q.png")))
    noms.sort()
    liste2 = []
    for nom in noms:
      for element in liste:
        if element[0]==nom:
          liste2.append(element)
    return liste2
    
  def effacePlanete(self):
    return
    for clef in self.configuration.keys()[:]:
      del self.configuration[clef]
    
  def getConfiguration(self, section, champ, defaut):
    """Retourne une valeur de configuration"""
    section=str(section).lower()
    champ=str(champ).lower()
    
    sect = section
    for sectionDico in self.configuration.keys():
      if "-".join(sectionDico.split("-")[1:])==section:
        sect=sectionDico
    section = sect
    if section not in self.configuration.keys():
      print self.configuration.keys()
      print "Section pas dans le fichier de configuration",section
      raw_input("---")
      return defaut
    if champ not in self.configuration[section].keys():
      print "Section::champ pas dans le fichier de configuration",section,champ
      raw_input("---")
      return defaut
      
      
    return self.configuration[section][champ]