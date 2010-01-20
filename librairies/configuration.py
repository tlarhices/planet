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
  configuration = None #Le dictionnaire qui contient la configuration actuelle
  fichierConfig = None #Le fichier que l'on a chargé
  dicoDefinitionsSprite = None #Le dictionnaire qui contient toutes les définitions de sprite déjà chargées
  
  def __init__(self):
    self.configuration = {}
    self.dicoDefinitionsSprite = {}
    
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
      if ligne and ligne[0]!="#": #On saut les lignes vides ou commençant par #
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
    #Formatte les valeurs pour un sotckage vers le fichier
    def versStr(valeur):
      if isinstance(valeur, bool):
        return str(valeur)[0] #Transforme True en 'T' et False en 'F'
      return str(valeur)
      
    fichier = open(fichier, "w")
    for section in sorted(self.configuration.keys()): #Sauve les sections
      fichier.write("[["+str(section)+"]]\r\n")
      for soussection in sorted(self.configuration[section].keys()): #Sauve les sous-sections
        fichier.write(str(soussection)+":\r\n")
        for element in sorted(self.configuration[section][soussection].keys()): #Sauve les clefs
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
    """Charge un fichier de définition de sprite et range les valeurs au bon format dans un dictionnaire"""
    if fichier in self.dicoDefinitionsSprite.keys():
      return self.dicoDefinitionsSprite[fichier]
    
    sprite={}
    self.fichierConfig = fichier
    fich = open(fichier, "r")
    for ligne in fich:
      ligne = ligne.strip().lower() #On passe tout en minuscule
      if ligne[0]!="#":
        a,b = ligne.split("=")
        a = a.strip()
        b = b.strip()
        sprite[a]=b
      
    #Type les variables correctement
    def config(tab, clef, type, defaut):
      clef=clef.lower().strip()
      if not clef in tab.keys():
        return defaut
      else:
        return type(tab[clef])
        
    sprite["modele"] = config(sprite, "modele", str, "none")
    sprite["symbole"]  = config(sprite, "symbole", str, "none")
    sprite["icone"] = config(sprite, "icone", str, "icones/q.png")
    sprite["icone-actif"] = config(sprite, "icone-actif", str, "icones/q-over.png")
    sprite["icone-inactif"] = config(sprite, "icone-inactif", str, "icones/q.png")
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
    sprite["nourr"] = config(sprite, "nourr", float, 0.0)
    sprite["constr"] = config(sprite, "constr", float, 0.0)
    sprite["stock"] = config(sprite, "stock", str, "f")=="t"
    sprite["vitesseDePillage"] = config(sprite, "vitesseDePillage", float, 1.0)
    sprite["faciliteDePillage"] = config(sprite, "faciliteDePillage", float, 1.0)
    sprite["dureeDeVie"] = config(sprite, "dureeDeVie", float, -1.0)
    self.dicoDefinitionsSprite[fichier] = sprite
    return sprite
      
  def setConfiguration(self, section, soussection, champ, valeur):
    """Change une valeur de la configuration courante"""
    section=str(section).lower()
    soussection=str(soussection).lower()
    champ=str(champ).lower()
    
    if not section in self.configuration.keys():
      self.configuration[section]={}
    if not soussection in self.configuration[section].keys():
      self.configuration[section][soussection]={}
    self.configuration[section][soussection][champ]=valeur
    
  def versType(self, valeur, defaut, type):
    """
    Effectue un transtypage sécurisé
    Effectue type(valeur), si une erreur survient un message est affiché et type(defaut) est renvoyé
    Effectue un transtypage intelligent des booléens
    Si type(defaut) retourne une erreur, le programme se bloque
    """
    try:
      if type==bool:
        if isinstance(valeur, bool):
          return valeur
        elif isinstance(valeur, (int, float)):
          return valeur!=0
        return valeur.lower().strip()=="t"
      return type(valeur)
    except Exception, ex:
      print "configuration::transtypage::Erreur ::",valeur,"n'est pas typpable en",str(type)
      if defaut==valeur:
        raise ex
      return self.versType(defaut, defaut, type)
    
    
  def getConfiguration(self, section, soussection, champ, defaut, type=None):
    """Retourne une valeur de configuration"""
    
    if type==None:
      frame = sys._getframe(1)
      texte=str(frame.f_code.co_filename)+"::"+"??"+"::"+str(frame.f_code.co_name)+u" > Avertissement :: getConfiguration sans type est déprécié, pensez à mettre à jour"
      print texte
      type=str
    
    section=str(section).lower()
    soussection=str(soussection).lower()
    champ=str(champ).lower()
    
    if section not in self.configuration.keys():
      print self.configuration.keys()
      print "getConfiguration::section pas dans le fichier de configuration ::",section
      #raw_input("pause_configuration")
      self.configuration[section]={}
      self.configuration[section][soussection]={}
      self.configuration[section][soussection][champ]=self.versType(defaut, defaut, type)
      return self.versType(defaut, defaut, type)
    if soussection not in self.configuration[section].keys():
      print self.configuration.keys()
      print "getConfiguration::sous-section pas dans le fichier de configuration ::",section, soussection
      #raw_input("pause_configuration")
      self.configuration[section][soussection]={}
      self.configuration[section][soussection][champ]=self.versType(defaut, defaut, type)
      return self.versType(defaut, defaut, type)
    if champ not in self.configuration[section][soussection].keys():
      print "getConfiguration::champ pas dans le fichier de configuration ::",section, soussection, champ
      #raw_input("pause_configuration")
      self.configuration[section][soussection][champ]=self.versType(defaut, defaut, type)
      return self.versType(defaut, defaut, type)
      
    return self.versType(self.configuration[section][soussection][champ], defaut, type)
    
  def chargeMenu(self, menu):
    """Charge un fichier de menu et retourne le contenu du fichier parsé"""
    if not os.path.exists(os.path.join(".","data","menus",menu+".menu")):
      print "ChargeMenu, Erreur : fichier de menu inexistant", menu
      return None
    fichier = open(os.path.join(".","data","menus",menu+".menu"))
    sections = []
    dansSection=False
    for ligne in fichier:
      ligne = ligne.strip().split("#")[0].strip().decode("utf-8")
      if ligne:
        if ligne[0]!="#":
          if ligne.startswith("[") and ligne.endswith("]"):
            sections.append([ligne[1:-1],[],{}])
            dansSection = True
          elif ligne.endswith(":") and ligne.find("=")==-1:
            sections[-1][1].append([ligne[:-1],{}])
            dansSection = False
          elif ligne.find("=")!=-1:
            #clef
            a,b = ligne.split("=")
            a = str(a.strip()).lower()
            b = b.strip()
            if not dansSection:
              sections[-1][1][-1][1][a]=b
            else:
              sections[-1][2][a]=b
          else:
            print "ChargeMenu, Erreur : ligne inconnue :", ligne
            
    for nomSection, contenuSection, dicoSection in sections:
      if not 'nom' in dicoSection.keys():
        print "manque nom !"
      if not 'infobulle' in dicoSection.keys():
        print "manque infobulle !"
      if not 'icone' in dicoSection.keys():
        print "manque icone !"
      else:
        dicoSection["iconeactif"] = "icones/"+dicoSection["icone"]+"-over.png"
        dicoSection["iconeinactif"] = "icones/"+dicoSection["icone"]+".png"
        
      for nomElement, contenuElement in contenuSection:
        if not 'nom' in contenuElement.keys():
          print "manque nom !"
        if not 'chemin' in contenuElement.keys():
          print "manque chemin !"
        else:
          sect, soussect, var = contenuElement["chemin"].split("/")
          contenuElement["valeur"] = self.getConfiguration(sect, soussect, var, "Erreur !", str)
        if not 'infobulle' in contenuElement.keys():
          print "manque infobulle !"
        if not 'icone' in contenuElement.keys():
          print "manque icone !"
        else:
          contenuElement["iconeactif"] = "icones/"+contenuElement["icone"]+"-over.png"
          contenuElement["iconeinactif"] = "icones/"+contenuElement["icone"]+".png"
        if not 'type' in contenuElement.keys():
          print "manque type !"
          contenuElement["type"] = "None"
        elif contenuElement["type"] not in ["bool", "int", "liste", "float", "str"]:
          print "type inconnu !", contenuElement["type"]
          contenuElement["type"] = "None"
        else:
          if contenuElement["type"]=="liste":
            if not 'valeurs' in contenuElement.keys():
              print "manque valeurs pour type liste !"
              contenuElement["type"] = "None"
            else:
              contenuElement["valeurs"] = contenuElement["valeurs"].split("|")
          elif contenuElement["type"]=="bool":
            if contenuElement["valeur"].lower()=="t":
              contenuElement["valeur"] = True
            else:
              contenuElement["valeur"] = False
          elif contenuElement["type"]=="float":
            if (not 'valeurmin' in contenuElement.keys()) and (not 'valeurmax' in contenuElement.keys()):
              print "manque bornes pour type float !"
              contenuElement["type"] = "None"
            else:
              contenuElement["valeur"] = float(contenuElement["valeur"])
          elif contenuElement["type"]=="int":
            if (not 'valeurmin' in contenuElement.keys()) and (not 'valeurmax' in contenuElement.keys()):
              print "manque bornes pour type int !"
              contenuElement["type"] = "None"
            else:
              contenuElement["valeur"] = int(float(contenuElement["valeur"]))
    return sections
    
