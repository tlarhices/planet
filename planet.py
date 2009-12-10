#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import sys
import shutil
import getopt
import os
sys.path.append(os.path.join(".", "librairies"))

import general

from planete import *
from configuration import *
from joueur import *
from gui import *

try:
    import psyco
    psyco.full()
    #psyco.profile()
except ImportError:
    print 
    print "Vous devriez installer Psyco (pour python) pour aller plus vite"
    print 

class Start:
  
  #Paramètres de génération de la planète
  planete=None #L'instance de la classe planète
  tmp=None
  delta=None #Le taux de perturbation de la surface de la planète
  
  #Autres
  preImage = None #L'heure à laquelle la précédente image a été rendue
  
  joueur = None
  
  ### Initialisation ---------------------------------------------------
  def __init__(self):
    
    #render.setShaderAuto()
    
    #Configuration de DEBUG
    general.DEBUG_GENERE_PLANETE = general.configuration.getConfiguration("debug", "planete", "debug_genere_planete","0")=="1"
    general.DEBUG_CHARGE_PLANETE = general.configuration.getConfiguration("debug", "planete", "debug_charge_planete","0")=="1"
    general.DEBUG_CHARGE_PLANETE_VERBOSE = general.configuration.getConfiguration("debug", "planete", "debug_charge_planete_verbose","0")=="1"
    general.DEBUG_AI_GRAPHE_DEPLACEMENT_CONSTRUCTION = general.configuration.getConfiguration("debug", "ai", "debug_ai_graphe_deplacement_construction","0")=="1"
    general.DEBUG_AI_GRAPHE_DEPLACEMENT_PROMENADE = general.configuration.getConfiguration("debug", "ai", "debug_ai_graphe_deplacement_promenade","0")=="1"
    
    if base.camLens != None:
      general.gui = Interface(self)
    else:
      class DUMMY:
        def afficheTexte(self, texte, type="normal", forceRefresh=False):
          print "[",type,"]",texte
        def ajouteJoueur(self, joueur):
          pass
        def lanceInterface(self):
          pass
      general.gui = DUMMY()
    
    if general.configuration.getConfiguration("debug", "panda", "DEBUG_PANDA_VIA_PSTATS","0")=="1":
      #Profile du code via PStat
      PStatClient.connect()

    if general.configuration.getConfiguration("affichage", "general", "afficheFPS","0")=="1":
      base.setFrameRateMeter(True)
    #Place une sphère à la place de la planète pendant la construction
    self.tmp = Planete()
    self.tmp.seuilSauvegardeAuto = -1
    self.tmp.fabriqueNouvellePlanete(tesselation=3, delta=0.2)
    self.tmp.fabriqueModel()
    
    general.gui.io.positionneCamera(render)
    #On affiche le menu principal
    general.gui.lanceInterface()
    
  def start(self):
    """Lance le rendu et la boucle de jeu"""

    if self.planete == None:
      print "Vous devez créer une planète avant !"
      return
      
    #On ajoute les joueurs
    j1 = JoueurLocal("Joueur 1", (1.0, 0.0, 0.0, 1.0), self.planete)
    self.joueur = j1
    j2 = JoueurIA("Joueur 2", (1.0, 0.0, 0.0, 1.0), self.planete)
    self.planete.ajouteJoueur(j1)
    self.planete.ajouteJoueur(j2)
    j1.ajouteSprite("test", random.choice(self.planete.sommets), "test")
    j1.ajouteSprite("test", random.choice(self.planete.sommets), "test")
    j1.ajouteSprite("test", random.choice(self.planete.sommets), "test")
    j1.ajouteSprite("test", random.choice(self.planete.sommets), "test")
    j1.ajouteSprite("test", random.choice(self.planete.sommets), "test")
    j1.ajouteSprite("test", random.choice(self.planete.sommets), "test")
    j2.ajouteSprite("test", random.choice(self.planete.sommets), "test")

    #On construit le modèle 3D de la planète
    self.planete.fabriqueModel()
    self.tmp.detruit()
    self.tmp = None
    general.gui.io.positionneCamera()
    

  def afficheStat(self):
    general.afficheStatChrono()

  def ping(self, task):
    """Fonction exécutée à chaque image"""
    
    #Calculs du temps écoulé depuis l'image précédente
    if self.preImage != None:
      deltaT = task.time - self.preImage
    else:
      deltaT = task.time
    self.preImage = task.time
    
    #On ping la planète
    if self.planete != None:
      self.planete.ping(deltaT)
    if self.tmp != None:
      self.tmp.ping(deltaT)
    
    #On indique que l'on veut toujours cette fonction pour la prochaine image
    return Task.cont
  ### Fin initialisation -----------------------------------------------
      
  ### Gestion de la planète --------------------------------------------
  def fabriquePlanete(self):
    """Construit une nouvelle planète via les gentils algos"""
    self.detruit()
    self.planete = Planete()
    general.configuration.effacePlanete()
    tesselation = int(general.configuration.getConfiguration("planete", "generation", "tesselation", "4"))
    delta = float(general.configuration.getConfiguration("planete", "generation", "delta", "0.2"))
    self.planete.fabriqueNouvellePlanete(tesselation=tesselation, delta=delta)
    #self.camera.reparentTo(self.planete.racine)
    
  def chargePlanete(self, fichierPlanete):
    """Construit une nouvelle planète via les gentils algos"""
    self.detruit()
    self.planete = Planete()
    general.configuration.effacePlanete()
    self.planete.charge(fichier=fichierPlanete)
    #self.camera.reparentTo(self.planete.racine)
    
  def detruit(self):
    """Supprime le modèle et retire les structures de données"""
    if self.planete != None:
      self.planete.detruit()
      self.planete = None
  ### Fin gestion de la planète ----------------------------------------
      
  ### Autres -----------------------------------------------------------
  def modifieAltitude(self, direction):
    """Change l'altitude d'un point, si direction>0 alors l'altitude sera accrue sinon diminuée"""
    
    general.gui.io.testeSouris()
    
    if self.planete!=None:
      planete = self.planete
    elif self.tmp!=None:
      planete = self.tmp
    else:
      return
    
    if planete.survol == None:
      return
    
    ndelta = planete.delta * direction * 0.01
    planete.elevePoint(planete.survol, ndelta)
    
  def screenShot(self):
    base.screenshot("test")
  ### Fin autres -------------------------------------------------------


    
print """

Planet, Copyright (C) 2009 Clerc Mathias
Planet comes with ABSOLUTELY NO WARRANTY; for details
type see the license file in the docs folder.  This
is free software, and you are welcome to redistribute
it under certain conditions; see the license file in
the docs folder for details.

"""

def aideCommande():
  print "Manuel :"
  print " # Options en ligne de commande :"
  print "  -h / --help :"
  print "     Afficher cette aide"
  print "  -c fichier / --config=fichier :"
  print "     Utiliser 'fichier' comme fichier de config"
  print "  -p / --profiler :"
  print "     Active cProfile et lui fait produire le fichier profiler.log"
  print ""
  print " # Configuration clavier par défaut :"
  print "  -q/esc :"
  print "     Quitter"
  print "  -Touches flêchées / souris aux bors de l'écran :"
  print "     Déplacer la caméra"
  print "  -Touches +/- / molette haut/bas :"
  print "     Zommer/dézoomer"
  print "  -Clic gauche sur la planète :"
  print "     Surélever le sommet le plus proche du curseur"
  print "  -Clic droite sur la planète :"
  print "     Enfoncer le sommet le plus proche du curseur"

#Parasage des paramètres de la ligne de commande
try:
    opts, args = getopt.getopt(sys.argv[1:], "hc:p", ["help", "config=", "profiler"])
except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    aideCommande()
    sys.exit(2)

def deb():
  #Création de l'instance
  print "Initialisation..."  
  start = Start()
  #Construction de la planète
  print " - Création d'une nouvelle planète..."
  #start.fabriquePlanete()
  print " - Création d'une nouvelle planète terminée"
  #Lancement du jeu
  print "Initialisation terminée"
  print "Lancement..."
  #On va faire exécuter self.ping a chaque image
  taskMgr.add(start.ping, "BouclePrincipale")

  #On lance la boucle magique de panda
  run()

if __name__=="__main__":

  fichierConfig = None
  profile = False
  besoinDetails = False
  for o, a in opts:
    if o in ("-h", "--help"):
      aideCommande()
      sys.exit()
    elif o in ("-c", "--config"):
      fichierConfig = a
    elif o in ("-p", "--profiler"):
      try:
        import cProfile
        profile = True
      except:
        pass
    else:
      assert False, "Paramètre inconnu"
      

  general.configuration = Configuration()
  #Charge la configuration par défaut
  general.configuration.charge(os.path.join(".","configuration","defaut.cfg"))
  #Si on a une configuration utilisateur, on écrase celle par défaut
  general.configuration.charge(os.path.join(".","configuration","utilisateur.cfg"), erreurSiExistePas=False)

  from pandac.PandaModules import *

  #Change le titre de la fenêtre
  loadPrcFileData("",u"window-title Planète".encode("iso8859"))
  loadPrcFileData("","model-cache-dir ./data/cache/")
  #loadPrcFileData("","hardware-point-sprites 0")
  #Change la résolution de la fenêtre
  resolution = general.configuration.getConfiguration("affichage","general", "resolution","640 480")
  if resolution == "0 0":
    print "Avertissement :: resolution de 0, démarrage sans fenêtre"
    loadPrcFileData("",u"window-type none")
  else:
    loadPrcFileData("",u"win-size "+resolution)
  #Kicke la synchro avec VSynch pour pouvoir dépasser les 60 FPS
  loadPrcFileData("",u"sync-video #f")

  import direct.directbase.DirectStart
  from direct.task import Task

  base.camLens.setNear(0.001)

  if not profile:
    deb()
  else:
    cProfile.run('deb()', 'profiler.log')
