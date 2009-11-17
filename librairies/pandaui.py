#!/usr/bin/env python
# -*- coding: utf-8 -*-
import overlays
import string
import random
import math
import os

from pandac.PandaModules import *
import general

class GUI():
  """Le GUI gère des groupes de composants graphiques"""
  overlay = None #La racine de tous les éléments graphiques que l'on a
  composants = None #La liste des objets actuels
  survol = None #La liste des objets actifs sous le curseur
  defaultPolice = None #La police de caractère à utiliser par défaut
  guiPath = None
  
  def __init__(self, i18n, guiPath):
    """Le GUI gère des groupes de composants graphiques"""
    if general.DEBUG_PANDAUI_GUI:
      print "DEBUG_PANDAUI_GUI :: Création de GUI(",i18n,")"
    self.overlay = overlays.PixelNode('g2d')
    self.composants = {}
    self.survol = []
    self.i18n = i18n
    self.defaultPolice = "FFF Tusj.ttf"#'GRENADIE.TTF' #Par défaut on choisit la police Grenadier
    self.guiPath = guiPath
    base.accept('aspectRatioChanged', self.fenetreChangeDimension)
    
  def ajouteComposant(self, composant, section="racine"):
    """Ajoute un composant au GUI, la section permet de définir un groupe dans lequel l'objet sera inséré"""
    if general.DEBUG_PANDAUI_GUI:
      print "DEBUG_PANDAUI_GUI :: Ajout du composant",composant,"dans la section",section
    if section==None:
      section="racine"
    section=section.lower().strip()
    if section.lower().strip() not in self.composants.keys():
      self.composants[section.lower().strip()] = []
    self.composants[section.lower().strip()].append(composant)
    
  def enleveComposant(self, composant, section=None):
    """Retire un composant d'une section, si la section n'est pas donnée, il sera retiré de toutes les sections où il se trouve"""
    if general.DEBUG_PANDAUI_GUI:
      print "DEBUG_PANDAUI_GUI :: Supression du composant",composant,"de la section",section
    if section==None:
      for section in self.composants.keys():
        self.enleveComposant(composant, section)
    elif section in self.composants.keys():
      section=section.lower().strip()
      while self.composants[section].count(composant)>0:
        self.composants[section].remove(composant)
    
  def testeSouris(self, x, y):
    """Gère le clic souris. X,Y sont les coordonnées (en pixels) du curseur au moment du clic avec 0,0 qui est le point supérieur gauche de l'écran"""
    if general.DEBUG_PANDAUI_CLIC:
      print "DEBUG_PANDAUI_CLIC (GUI) :: Test souris",x,",",y
    self.survol = []
    
    for section in self.composants:
      for composant in self.composants[section]:
        if composant.getPos() != None:
          if composant.getPos()[0] <= x and composant.getPos()[0] + composant.getSize()[0] >= x:
            if composant.getPos()[1] <= y and composant.getPos()[1] + composant.getSize()[1] >= y:
              if composant.actif:
                if general.DEBUG_PANDAUI_CLIC:
                  print "DEBUG_PANDAUI_CLIC :: Survol du composant",composant
                self.survol.append(composant)
        
  def clicGauche(self):
    """Gère le clic gauche, utilise la liste de survol calculée par testeSouris"""
    if general.DEBUG_PANDAUI_CLIC:
      print "DEBUG_PANDAUI_CLIC (GUI) :: Clic gauche"
    if len(self.survol)>0:
      if general.DEBUG_PANDAUI_CLIC:
        print "DEBUG_PANDAUI_CLIC (GUI) :: Clic gauche sur",self.survol[-1]
      self.survol[-1].clicGauche()
      self.survol = []
      return True
    return False
      
  def purge(self, section=None):
    """Supprime tous les objets d'une section. Si section==None, alors tous les objets sans exception seront effacés"""
    if general.DEBUG_PANDAUI_PURGE:
      print "DEBUG_PANDAUI_PURGE :: purge section",section
      
    if section==None:
      for section in self.composants.keys():
        self.purge(section)
    else:
      section=section.lower().strip()
      if section in self.composants.keys():
        while len(self.composants[section])>0:
          composant = self.composants[section][0]
          composant.efface()
          if self.composants[section].count(composant)>0:
            self.composants[section].remove(composant)
        del self.composants[section]
          
  def getTaille(self):
    """Retourne la résolution actuelle (taille de la zone d'affichage)"""
    if general.DEBUG_PANDAUI_GUI:
      print "DEBUG_PANDAUI_GUI :: Taille = ",base.win.getProperties().getXSize(), base.win.getProperties().getYSize()
    return base.win.getProperties().getXSize(), base.win.getProperties().getYSize()
    
  def fenetreChangeDimension(self):
    """Quand la taille de la fenêtre change, cette fonction lance la mise à jour du rendu des objets graphiques"""
    self.overlay.aspectRatioChanged()
    
  def setPolice(self, police):
    """Définit le nom de la police à utiliser (ne met pas à jour les composants déjà crées)"""
    self.defaultPolice = police
    
  def getPolice(self):
    """retourne le nom de la police de caractère utilisé"""
    return self.defaultPolice
          
  
class Texte():
  """Affiche une ligne de texte sur un rectangle de fond"""
  gui = None
  section = None
  text = None
  box = None
  actif = None
  callback = None
  
  def __init__(self, gui, texte, wordwrap=-1, section="__", couleurTexte=(0,0,0,1), couleurFond=(.8, .8, .8, .8), pad = 5, police = None, texture=None):
    """
    Affiche une ligne de texte sur un rectangle de fond
    gui : l'instance de gui dans laquelle on va s'insérer
    texte : Le texte à afficher
    wordwrap : largeur horizontale du composant (par défaut -1)
    Si le texte déborde, il sera mit sur plusieures lignes.
    Si wordwrap vaut None, la taille horizontale du composant n'est pas fixée
    Si wordwrap vaut -1, la taille horizontale du composant est celle de l'écran (gui.getTaille()[1])
    Section : Le nom du groupe auquel ce composant appartient (par défaut "__")
    couleurTexte : La couleur du texte (par défaut noir)
    couleurFond : La couleur du rectangle de fond (par défaut gris 20% à 80% d'opacité)
    pad : La largeur de la bordure ajoutée par le fond autour du texte (par défaut 5)
    police : Le nom de la police de caractère à utiliser pour le texte (par défaut utilise la police de GUI)
    """
    self.gui=gui
    if police == None:
      police = gui.getPolice()
      
    self.section = section
    self.actif = True #L'objet bloque les clics
    self.pad = pad
    
    #Crée le fond
    if texture==None:
      self.box = overlays.Overlay(color=couleurFond)
    else:
      if self.gui.guiPath == None:
        tex = loader.loadTexture(os.path.join(".", "UI", "ui", "images", texture))
      else:
        tex = loader.loadTexture(os.path.join(self.gui.guiPath, "images", texture))
      tex.setMagfilter(Texture.FTNearest)
      self.box = overlays.OverlaySlice9(texture=tex, color1=Vec4(0,0.25,0.25,0.5), color2=Vec4(0,0.25,0.25,0.5))
      self.box.setTexture(tex)
    #self.box.setTexcoords(0, 0, 54, 53)

    self.box.reparentTo(gui.overlay)
    self.box.setPos(0, 0)
    
    #Crée le texte
    myFont = overlays.TextOverlay.loadFont(police, size=20)
    if wordwrap==-1:
      wordwrap=base.win.getProperties().getXSize()-pad*2
    #Panda encode en iso8859
    self.text = overlays.TextOverlay(msg=gui.i18n.getText(texte).encode("iso8859"), font=myFont, color=couleurTexte, wordwrap=wordwrap)
    self.text.reparentTo(gui.overlay)
    
    #On place le coin supérieur gauche de la boite au point 0,0
    self.box.setPos(0, 0)
    
    #On place le texte à la distance 'pad' des bords de la boite
    x, y = self.box.getPos()
    self.text.setPos(x+pad, y+pad)
    
    #On étire la boite pour quelle dépasse d'une distance 'pad' de l'autre coté du texte
    w, h = self.text.getSize()
    self.box.setSize(w+pad*2, h+pad*2)
    
    #On ajoute le composant au GUI
    gui.ajouteComposant(self, section=section)
    
  def setTexte(self, texte):
    """Change le texte sans recalculer la géométrie (la boite ne change pas de taille)"""
    self.text.setText(self.gui.i18n.getText(texte).encode("iso8859"))
    
  def setCouleur(couleurTexte, couleurFond):
    """Change la couleur du composant, mettre une valeur à None gardera sa valeur actuelle"""
    if self.text != None:
      self.text.setColor(couleurTexte)
    if self.box != None:
      self.box.setColor(couleurFond)
    
  def setPos(self, x, y, peutSortir=False):
    """
    Place les composants aux coordonnées x,y
    Si peutSortir==True, alors l'objet est autorisé à sortir de l'écran, sinon il se cognera aux bords
    """
    if not peutSortir:
      if self.box != None:
        if x + self.box.getSize()[0] > self.gui.getTaille()[0]:
          x = x - (self.gui.getTaille()[0] - self.box.getSize()[0])
        if y + self.box.getSize()[1] > self.gui.getTaille()[1]:
          y = y - (self.gui.getTaille()[1] - self.box.getSize()[1])
      elif self.text != None:
        if x + self.text.getSize()[0] > self.gui.getTaille()[0]:
          x = x - (self.gui.getTaille()[0] - self.text.getSize()[0])
        if y + self.text.getSize()[1] > self.gui.getTaille()[1]:
          y = y - (self.gui.getTaille()[1] - self.text.getSize()[1])
      if x < 0:
        x=0
      if y < 0:
        y=0
    if self.box != None:
      self.box.setPos(x, y)
      self.text.setPos(x + self.pad, y + self.pad)
    else:
      self.text.setPos(x, y)
    
  def getPos(self):
    """Retourne la position du composant"""
    if self.box != None:
      return self.box.getPos()
    elif self.text != None:
      return self.text.getPos()
    else:
      return None
    
  def getSize(self):
    """Retourne la taille du composant"""
    if self.box != None:
      return self.box.getSize()
    elif self.text != None:
      return self.text.getSize()
    else:
      return None
      
  def getTaille(self):
    """Pour la compatibilité"""
    return self.getSize()
    
  def fadeIn(self, task=None):
    return task.done
    
  def fadeOut(self, task=None):
    return task.done
      
  def efface(self, task=None):
    """Supprime le composant"""
    if self.box != None:
      self.box.destroy()
      self.box = None
    if self.text != None:
      self.text.destroy()
      self.text = None
      
    self.gui.enleveComposant(self)
      
    #Si self.callback existe, alors on appel cette fonction lors de l'effacement du composant (utile pour les bulles de dialogue)
    if self.callback != None:
      self.callback()
      
    #Task existe si c'est une moulinette interne de panda qui appelle cette fonction
    if task!=None:
      return task.done
    
  def clicGauche(self):
    """Ne fait rien quand on clique dessus"""
    pass
    
  def setActif(self, actif):
    self.actif = actif
    
class Bulle(Texte):
  """Affiche une ligne de texte sur un rectangle de fond pour les dialogues"""
  tache = None
  
  def __init__(self, gui, texte, timeout=None, callback=None, section="__", wordwrap=-1, couleurTexte=(0,0,0,1), couleurFond=(.8, .8, .8, .8), pad = 5, police = None, texture = None):
    """
    Affiche une ligne de texte sur un rectangle de fond pour les dialogues
    gui : l'instance de gui dans laquelle on va s'insérer
    texte : Le texte à afficher
    timeout : La durée àorès laquelle le texte disparaitra
    callback : La fonction qui sera appelée une fois le composant disparut
    Section : Le nom du groupe auquel ce composant appartient (par défaut "__")
    wordwrap : largeur horizontale du composant (par défaut -1)
    Si le texte déborde, il sera mit sur plusieures lignes.
    Si wordwrap vaut None, la taille horizontale du composant n'est pas fixée
    Si wordwrap vaut -1, la taille horizontale du composant est celle de l'écran (gui.getTaille()[1])
    couleurTexte : La couleur du texte (par défaut noir)
    couleurFond : La couleur du rectangle de fond (par défaut gris 20% à 80% d'opacité)
    pad : La largeur de la bordure ajoutée par le fond autour du texte (par défaut 5)
    police : Le nom de la police de caractère à utiliser pour le texte (par défaut utilise celle de GUI)
    """
    
    if texture == None:
      texture = "bulle.png"
    Texte.__init__(self, gui=gui, texte=texte, section=section, wordwrap=wordwrap, couleurTexte=couleurTexte, couleurFond=couleurFond, pad=pad, police=police, texture=texture)
    
    #On place le texte en bas de l'écran
    self.setPos(pad, base.win.getProperties().getYSize() - self.text.getSize()[1] - pad)
    
    #On indique que l'on veut supprimer le texte après un temps timeout
    if timeout!=None:
      self.tache = taskMgr.doMethodLater(timeout, self.efface, 'Efface bulle')
      
    #On garde en mémoire la fonction à appeler une fois le texte effacé
    self.callback = callback
    
  def clicGauche(self):
    """Ne fait rien quand on clique dessus"""
    self.efface()
    if self.tache!=None:
      taskMgr.remove(self.tache)
  
class Bouton(Texte):
  """Affiche un texte et un fond rectangulaire clicable (un bouton quoi)"""
  fonction = None #La fonction qui sera appelée lors du clic
  
  def __init__(self, gui, texte, fonction, wordwrap=-1, section="__", couleurTexte=(0,0,0,1), couleurFond=(.8, .8, .8, .8), pad = 5, police = None, texture = None):
    """
    Affiche un texte et un fond rectangulaire clicable (un bouton quoi)
    gui : l'instance de gui dans laquelle on va s'insérer
    texte : Le texte à afficher
    fonction : La fonction à exécuter lors du clic. Le bouton appelera fonction(texte) pour quelle sache quel bouton a appelé
    wordwrap : largeur horizontale du composant (par défaut -1)
    Si le texte déborde, il sera mit sur plusieures lignes.
    Si wordwrap vaut None, la taille horizontale du composant n'est pas fixée
    Si wordwrap vaut -1, la taille horizontale du composant est celle de l'écran (gui.getTaille()[1])
    Section : Le nom du groupe auquel ce composant appartient (par défaut "__")
    couleurTexte : La couleur du texte (par défaut noir)
    couleurFond : La couleur du rectangle de fond (par défaut gris 20% à 80% d'opacité)
    pad : La largeur de la bordure ajoutée par le fond autour du texte (par défaut 5)
    police : Le nom de la police de caractère à utiliser pour le texte (par défaut utilise celle de GUI)
    """
    if texture == None:
      texture = "bouton.png"

    self.fonction = fonction
    Texte.__init__(self, gui=gui, texte=texte, wordwrap=wordwrap, section=section, couleurTexte=couleurTexte, couleurFond=couleurFond, pad=pad, police=police, texture=texture)
    
  def clicGauche(self):
    """Fonction appelée lors du clic sur cet objet"""
    if general.DEBUG_PANDAUI_CLIC:
      print "DEBUG_PANDAUI_CLIC (Bouton) :: Clic gauche sur un bouton",self

    if self.fonction != None:
      if general.DEBUG_PANDAUI_CLIC:
        print "DEBUG_PANDAUI_CLIC (Bouton) :: Lancement de la fonction",self.fonction
      self.fonction(self.text.getText().decode("iso8859"))
    
class Titre(Texte):
  """Affiche un texte sur un fond rectangulaire centré sur l'écran"""
  def __init__(self, gui, texte, section="__", couleurTexte=(0,0,0,1), couleurFond=(.8, .8, .8, .8), pad = 5, police = None):
    """
    Affiche un texte sur un fond rectangulaire centré sur l'écran
    gui : l'instance de gui dans laquelle on va s'insérer
    texte : Le texte à afficher
    Section : Le nom du groupe auquel ce composant appartient (par défaut "__")
    couleurTexte : La couleur du texte (par défaut noir)
    couleurFond : La couleur du rectangle de fond (par défaut gris 20% à 80% d'opacité)
    pad : La largeur de la bordure ajoutée par le fond autour du texte (par défaut 5)
    police : Le nom de la police de caractère à utiliser pour le texte (par défaut utilise celle de GUI)
    """
    Texte.__init__(self, gui=gui, texte=texte, wordwrap=-1, section=section, couleurTexte=couleurTexte, couleurFond=couleurFond, pad=pad, police=police)
    self.setPos(self.getPos()[0], base.win.getProperties().getYSize()/2-self.getSize()[1]/2)
    #self.text.setPos(base.win.getProperties().getXSize()/2-self.text.getSize()[0]/2, self.text.getPos()[1])
    
class AnneauBoutons():
  """Construit des listes de boutons sous forme d'un anneau"""
  texts = None #Liste des boutons de l'anneau
  positions = None #Liste des positions par défaut des boutons de l'anneau
  section = None
  actif = None
  
  
  def __init__(self, gui, boutons, rayonBoutons, section="__"):
    """
    Construit des listes de boutons sous forme d'un anneau
    gui : l'instance de gui où l'on s'insère
    boutons : la liste des boutons à créer
    rayonBoutons : la taille d'un bouton
    section : le nom du groupe de composants de gui dans lequel on s'insère
    """
    pad = 5
    self.gui = gui
    self.texts=[]
    self.actif = True
    self.section = section
    self.positions = []
      
    #On calcule les infos sur l'anneau de base
    perimetre = (rayonBoutons * 2 + pad) * len(boutons)
    rayon = perimetre / (2 * 3.14)
    angle = 360.0 / len(boutons)
    currAngle = 0

    #On fabrique chaque bouton
    for texte, callback in boutons:
      bouton = Bouton(gui, texte, callback, wordwrap=None, section=section)
      position = rayon * math.sin(math.radians(currAngle)) - bouton.getTaille()[0]/2, rayon * math.cos(math.radians(currAngle)) - bouton.getTaille()[1]/2
      bouton.setPos(position[0], position[1])
      self.positions.append(position)
      self.texts.append(bouton)
      currAngle+=angle
      
  def efface(self, task=None):
    """Détruit tous les boutons de l'anneau"""
    for text in self.texts:
      text.efface()
    self.texts = []
    self.positions = []

    if self.callback!=None:
      self.callback()
      
    if task!=None:
      return task.done
      
  def deplace(self, x, y):
    """Déplace l'objet de x,y pixels"""
    for element in self.texts:
      element.setPos(element.getPos()[0]+x, element.getPos()[1]+y)
    
  def setPos(self, x, y):
    """Met le centre de l'anneau au point x,y"""
    for i in range(0, len(self.texts)):
      element = self.texts[i]
      position = self.positions[i]
      element.setPos(position[0]+x, position[1]+y)
      
  def setActif(self, actif):
    """Si l'objet est actif, alors tous ses composans le sont aussi"""
    self.actif = actif
    for composant in self.texts:
      composant.setActif(actif)
      
class ListeHorizontal():
  texts = None
  section = None
  actif = None
  
  def __init__(self, gui, titre, liste, timeout=None, callback=None, section="__"):
    pad = 5
    
    self.gui = gui
    self.texts=[]
    if titre!=None:
      self.texts.append(Texte(gui, titre, section = section))
    delta = 0
    for element in liste:
      bouton = Bouton(gui, element, callback, wordwrap=base.win.getProperties().getXSize()/len(liste)-pad*4, section=section)
      self.texts.append(bouton)
      
      
      if delta == 0:
        delta = pad + pad/2
      x = delta
      y = 0
      if titre!=None:
        y = self.texts[0].getSize()[1] + pad
      bouton.setPos(x, y)
        
      delta += bouton.getSize()[0]+pad
    if timeout!=None:
      taskMgr.doMethodLater(timeout, self.efface, 'Efface liste')
      
    self.callback = callback
    self.section = section
    self.actif = True
    
  def efface(self, task=None):
    for text in self.texts:
      text.efface()
    self.texts=[]

    if self.callback!=None:
      self.callback()
      
    if task!=None:
      return task.done
      
  def setPos(self, x, y):
    for element in self.texts:
      element.setPos(element.getPos()[0]+x, element.getPos()[1]+y)
      
  def getSize(self):
    x1, y1 = self.texts[0].getPos()
    x2, y2 = self.texts[-1].getPos()[0] + self.texts[-1].getSize()[0], self.texts[-1].getPos()[1] + self.texts[-1].getSize()[1]
    return x2-x1, y2-y1
    
  def setActif(self, actif):
    self.actif = actif
    for composant in self.texts:
      composant.setActif(actif)
      
class ListeBoutonsHorizontal(ListeHorizontal):
  def __init__(self, gui, titre, boutons, section="__"):
    liste=[]
    self.boutons = boutons
    self.titre = titre
    for element in boutons:
      liste.append(element[0])
    ListeHorizontal.__init__(self, gui, titre, liste, callback=self.executeFonction, section=section)

  def executeFonction(self, texte):
    if general.DEBUG_PANDAUI_CLIC:
      print "DEBUG_PANDAUI_CLIC (ListeBoutonsHorizontal) :: Lancement de la fonction de",texte
      
    for element in self.boutons:
      if element[0].strip().lower() == texte.strip().lower():
        if general.DEBUG_PANDAUI_CLIC:
          print "DEBUG_PANDAUI_CLIC (ListeBoutonsHorizontal) :: Lancement de la fonction",element[1],"pour",element[0]
        print element[1], element[0]
        
        element[1](self.titre, element[0])
    self.gui.purge(self.section)

class ListeVertical():
  texts = None
  section = None
  actif = None
  
  def __init__(self, gui, titre, liste, timeout=None, callback=None, section="__"):
    pad = 5
    
    self.gui = gui
    self.texts=[]
    delta = 0
    if titre!=None:
      self.texts.append(Texte(gui, titre, section=section))
      delta = self.texts[0].getTaille()[1]
    
    for element in liste:
      bouton = Bouton(gui, element, callback, section=section)
      self.texts.append(bouton)
      x = bouton.getPos()[0]
      y = delta + pad
      bouton.setPos(x, y)
      delta += bouton.getSize()[1]+pad
      
    if timeout!=None:
      taskMgr.doMethodLater(timeout, self.efface, 'Efface liste')
      
    self.callback = callback
    self.section = section
    self.actif = True
    
  def efface(self, task=None):
    for text in self.texts:
      text.efface()
    self.texts=[]

    if self.callback!=None:
      self.callback()
      
    if task!=None:
      return task.done
      
  def setPos(self, x, y):
    for element in self.texts:
      element.setPos(element.getPos()[0]+x, element.getPos()[1]+y)
      
  def getSize(self):
    x1, y1 = self.texts[0].getPos()
    x2, y2 = self.texts[-1].getPos()[0] + self.texts[-1].getSize()[0], self.texts[-1].getPos()[1] + self.texts[-1].getSize()[1]
    return x2-x1, y2-y1
    
  def setActif(self, actif):
    self.actif = actif
    for composant in self.texts:
      composant.setActif(actif)
      
class ListeBoutonsVertical(ListeVertical):
  def __init__(self, gui, titre, boutons, section="__"):
    liste=[]
    self.boutons = boutons
    self.titre = titre
    for element in boutons:
      liste.append(element[0])
    ListeVertical.__init__(self, gui, titre, liste, callback=self.executeFonction, section=section)

  def executeFonction(self, texte):
    if general.DEBUG_PANDAUI_CLIC:
      print "DEBUG_PANDAUI_CLIC (ListeBoutonsVertical) :: Lancement de la fonction de",texte

    for element in self.boutons:
      if element[0].strip().lower() == texte.strip().lower():
        if general.DEBUG_PANDAUI_CLIC:
          print "DEBUG_PANDAUI_CLIC (ListeBoutonsVertical) :: Lancement de la fonction",element[1],"pour",element[0]
        element[1](self.titre, element[0])
    self.gui.purge(self.section)
    
class UIOuiNon(ListeBoutonsHorizontal):
  def __init__(self, gui, titre, boutons, texteOui, callback, section="__"):
    self.texteOui = texteOui
    ListeBoutonsHorizontal.__init__(self, gui, titre, boutons, section=section)
    self.setPos(0, base.win.getProperties().getYSize()/2 - self.getSize()[1]/2)
    self.callback = callback

  def executeFonction(self, texte):
    if general.DEBUG_PANDAUI_CLIC:
      print "DEBUG_PANDAUI_CLIC (UIOuiNon) :: Lancement de la fonction de",texte
    if self.texteOui.strip().lower() == texte.strip().lower():
      if general.DEBUG_PANDAUI_CLIC:
        print "DEBUG_PANDAUI_CLIC (UIOuiNon) :: Lancement de la fonction",self.callback,"pour",True
      self.callback(True)
    if general.DEBUG_PANDAUI_CLIC:
      print "DEBUG_PANDAUI_CLIC (UIOuiNon) :: Lancement de la fonction",self.callback,"pour",False
    self.callback(False)
    self.gui.purge(self.section)
