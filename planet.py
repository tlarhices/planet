#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import random
import sys
import shutil
import getopt
import os
from weakref import proxy

#Ajoute les dossiers de librairies au path
sys.path.append(os.path.join(".", "librairies"))
sys.path.append(os.path.join(".", "librairies","ai"))

import general

#Préparation du todo
general.chargeTODO()

from planete import Planete
from systemesolaire import SystemeSolaire
from configuration import Configuration
import ai
from joueur import JoueurLocal, JoueurIA
from gui import Interface
from cartographie import Cartographie
from i18n import i18n

try:
    import psyco
    psyco.full()
    #psyco.profile()
except ImportError:
    print 
    print "Vous devriez installer Psyco (pour python) pour aller plus vite."
    print 


#Fabrique les dossiers de donnée s'ils ne sont pas déjà là
if not os.path.exists(os.path.join(".", "sauvegardes")):
  os.makedirs(os.path.join(".", "sauvegardes"))
if not os.path.exists(os.path.join(".", "data", "planetes")):
  os.makedirs(os.path.join(".", "data", "planetes"))
      
class Start:
  """Gère le début de la partie"""
  ### Initialisation ---------------------------------------------------
  def __init__(self):
    general.start = self
    
    #Active le shader si besoin est
    if general.configuration.getConfiguration("affichage", "general", "multitexturage", "heightmap", str) == "shader":
      _lightvec = Vec4(1.0, 0.0, 1.0, 1.0)
      render.setShaderInput( 'lightvec', _lightvec )
      render.setShaderAuto()
      sa = ShaderAttrib.make( )
      sa = sa.setShader( loader.loadShader( 'data/shaders/terrainNormal.sha' ) )
      cam0 = base.cam.node( )
      cam0.setTagStateKey( 'Normal' )
      cam0.setTagState( 'True' , RenderState.make( sa ) )
    
    general.TODO("Passer les DEBUG_* en getConfiguration")
    #Configuration de DEBUG
    general.DEBUG_GENERE_PLANETE = general.configuration.getConfiguration("debug", "planete", "debug_genere_planete", "f", bool)
    general.DEBUG_CHARGE_PLANETE = general.configuration.getConfiguration("debug", "planete", "debug_charge_planete", "f", bool)
    general.DEBUG_CHARGE_PLANETE_VERBOSE = general.configuration.getConfiguration("debug", "planete", "debug_charge_planete_verbose", "f", bool)
    general.DEBUG_AI_GRAPHE_DEPLACEMENT_CONSTRUCTION = general.configuration.getConfiguration("debug", "ai", "debug_ai_graphe_deplacement_construction", "f", bool)
    general.DEBUG_AI_GRAPHE_DEPLACEMENT_PROMENADE = general.configuration.getConfiguration("debug", "ai", "debug_ai_graphe_deplacement_promenade", "f", bool)
    general.DEBUG_AI_VA_VERS = general.configuration.getConfiguration("debug", "ai", "DEBUG_AI_VA_VERS", "f", bool)
    general.DEBUG_AI_SUIT_CHEMIN = general.configuration.getConfiguration("debug", "ai", "DEBUG_AI_SUIT_CHEMIN", "f", bool)
    general.DEBUG_AI_PING_PILE_COMPORTEMENT = general.configuration.getConfiguration("debug", "ai", "DEBUG_AI_PING_PILE_COMPORTEMENT", "f", bool)
    
    #Gère le dessin des cartes
    general.cartographie = Cartographie()
    
    #Gère les types de comportements d'IA
    general.aiPlugin = ai.AIPlugin()
    general.aiPlugin.scan()
    
    
    if base.camLens != None:
      #Si on a une fenêtre ouverte, on charge l'interface graphique
      general.interface = Interface()
    else:
      #Sinon (étrange debug mode console uniquement) on la remplace par une fausse classe d'interface
      class DUMMYCAMERA:
        def getPos(self, dummy=None):
          return Vec3(0.0,0.0,0.0)
      class DUMMYIO:
        camera = None
        def __init__(self):
          self.camera=DUMMYCAMERA()
          
        def positionneCamera(self, dummy=None):
          pass
      class DUMMY:
        menuCourant = None
        joueur = None
        def __init__(self):
          general.io = DUMMYIO()
        def afficheTexte(self, texte, parametres, type="normal", forceRefresh=False):
          print "[",type,"]",texte
        def ajouteJoueur(self, joueur):
          pass
        def lanceInterface(self):
          self.start.fabriquePlanete()
          self.start.start()
          
      general.interface = DUMMY(self)
    
    #On lance PStats (debugger de panda3d) si la configuration dit qu'on en a envie
    if general.configuration.getConfiguration("debug", "panda", "DEBUG_PANDA_VIA_PSTATS","f", bool):
      #Profile du code via PStat
      PStatClient.connect()

    #On affiche le compteur d'images par seconde si besoin est
    if general.configuration.getConfiguration("affichage", "general", "afficheFPS","f", bool):
      base.setFrameRateMeter(True)
      
    #On ajoute le système solaire
    self.fabriqueSystemeSolaire()
    
    #On dit qu'on a pas de joueur
    general.joueurLocal = None
    
    #general.io est crée par l'interface
    #Place la caméra dans l'arbre de rendu
    general.io.positionneCamera(render)
    
    #On affiche le menu principal
    general.interface.lanceInterface()
    
  def fabriqueSystemeSolaire(self):
    """Construit le système solaire"""
    
    #On fabrique le système solaire
    general.planete = SystemeSolaire()
    #On place les planètes dans le système
    cptPlanetes = 0
    for fich in os.listdir(os.path.join(".", "data", "planetes")):
      if fich.endswith(".pln"):
        cptPlanetes+=1
        general.planete.ajoutePlanete(fich)
    #On met des planètes aléatoires qui font rien pour avoir au moins 7 planètes dans le menu
    while cptPlanetes<7:
      cptPlanetes+=1
      general.planete.ajoutePlanete("--n/a--")
    general.planete.fabriqueModel()
    
  def start(self):
    """Lance le rendu et la boucle de jeu"""

    #Les couleurs des joueurs par ordre d'arrivée sur la planète
    couleurs = [
      (0.0, 0.0, 1.0, 1.0),
      (1.0, 0.0, 0.0, 1.0),
      (0.0, 1.0, 0.0, 1.0),
      (0.0, 1.0, 1.0, 1.0),
      (1.0, 0.0, 1.0, 1.0),
      (1.0, 1.0, 0.0, 1.0),
      (1.0, 0.0, 0.0, 1.0),
      (1.0, 0.0, 0.0, 1.0),
      (1.0, 0.0, 0.0, 1.0),
      (1.0, 0.0, 0.0, 1.0),
      (1.0, 0.0, 0.0, 1.0),
      (1.0, 0.0, 0.0, 1.0)      
    ]
    
    #On ajoute les joueurs
    j = JoueurLocal("Joueur 1", couleurs[len(general.planete.joueurs)])
    general.planete.ajouteJoueur(j)
    while len(general.planete.joueurs)<int(general.configuration.getConfiguration("planete", "Regles", "nombreJoueurs", "2", int)):
      j = JoueurIA("Joueur "+str(len(general.planete.joueurs)+1), couleurs[len(general.planete.joueurs)])
      general.planete.ajouteJoueur(j)
    
    #Ajoute des gugusses aux joueurs
    for joueur in general.planete.joueurs:
      for i in range(0, int(general.configuration.getConfiguration("planete", "Regles", "nombreUnite", "2", int))):
        OK=False
        while not OK:
          sommet = random.choice(general.planete.geoide.sommets)
          OK = sommet.length()>general.planete.geoide.niveauEau
        joueur.ajouteSprite("test", sommet, "test")
      for i in range(0, int(general.configuration.getConfiguration("planete", "Regles", "nombreCollecteurRessource", "1", int))):
        OK=False
        while not OK:
          sommet = random.choice(general.planete.geoide.sommets)
          OK = sommet.length()>general.planete.geoide.niveauEau
        joueur.ajouteSprite("ressource", sommet, "ressource")

    #On construit le modèle 3D de la planète
    general.planete.fabriqueModel()
    
    #On retire le système solaire du fond de menu
    general.planete.afficheTexte("Supression du système solaire", {}, None)
    general.tmp.detruit()
    general.tmp = None
    
  def ping(self, task):
    """Fonction exécutée à chaque image"""
    #On met à jour l'heure actuelle pour les calculs dans les shaders
    render.setShaderInput( 'time', task.time )
    
    #On indique que l'on veut toujours cette fonction pour la prochaine image
    return Task.cont
  ### Fin initialisation -----------------------------------------------
      
  ### Gestion de la planète --------------------------------------------
  def fabriquePlanete(self):
    """Construit une nouvelle planète via les gentils algos"""
    #On place la planète courante comme fond de menu
    general.tmp=general.planete
    general.planete=None
    
    #On fabrique une nouvelle planete vide
    general.planete = Planete()
    
    #On fabrique la planète
    general.planete.fabriqueNouvellePlanete(
      tesselation = general.configuration.getConfiguration("planete", "generation", "tesselation", "4", int),
      delta = general.configuration.getConfiguration("planete", "generation", "delta", "0.2", float)
    )
    
  def chargePlanete(self, fichierPlanete):
    """Charge une planète depuis un fichier"""
    #On place la planète courante comme fond de menu
    general.tmp=general.planete
    general.planete=None
    
    #On fabrique une nouvelle planete vide
    general.planete = Planete()
    #On charge la planète
    general.planete.charge(fichier=fichierPlanete)
    
  def detruit(self):
    """Supprime le modèle et retire les structures de données"""
    if general.planete != None:
      general.planete.detruit()
      general.planete = None
  ### Fin gestion de la planète ----------------------------------------
      
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
  #Boucle qui fait presque tout comme "run()"
  """while True:
    taskMgr.step()
    #VSynch à 60FPS
    time.sleep(1.0 / 60.0)"""

if __name__=="__main__":
  fichierConfig = None
  profile = False
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
  
  if fichierConfig == None:
    #Si on a une configuration utilisateur, on écrase celle par défaut
    general.configuration.charge(os.path.join(".","configuration","utilisateur.cfg"), erreurSiExistePas=False)
  else:
    #Si on a un fichier de config donné par ligne de commande, on l'utilise
    general.configuration.charge(fichierConfig, erreurSiExistePas=False)
    
  #On initialise l'internationalisation
  general.i18n = i18n(langue=general.configuration.getConfiguration("affichage","langue", "langue", "french", str))

  from pandac.PandaModules import *

  #Change le titre de la fenêtre
  loadPrcFileData("",u"window-title Planète".encode("iso8859"))
  #Change le dossier où sera stocké les données temporaires
  loadPrcFileData("","model-cache-dir ./data/cache/")
  #Debug si les nuages déconnent
  #loadPrcFileData("","hardware-point-sprites 0")
  
  #Change la résolution de la fenêtre
  resolution = general.configuration.getConfiguration("affichage", "general", "resolution", "640 480", str)
  if resolution == "0 0":
    print "Avertissement :: resolution de 0, démarrage sans fenêtre"
    loadPrcFileData("",u"window-type none")
  else:
    loadPrcFileData("",u"win-size "+resolution)
    
  #Kicke la synchro avec VSynch pour pouvoir dépasser les 60 FPS
  loadPrcFileData("",u"sync-video #f")
  
  #On bloque les touches cholaxes de windows (shift pressé plus de 5s, plus de 5 fois rapidement, ...)
  loadPrcFileData("",u"disable-sticky-keys 1")
  
  #On dit à Panda d'utiliser le coeur le moins utilisé pour le moment et pas le coeur 1
  loadPrcFileData("",u"client-cpu-affinity -1")
  
  import direct.directbase.DirectStart
  from direct.task import Task

  #Change le frontclip
  if base.camLens != None:
    base.camLens.setNear(0.001)

  if not profile:
    deb()
  else:
    print "Profiling..."
    cProfile.run('deb()', 'profiler.log')
