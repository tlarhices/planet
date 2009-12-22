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
sys.path.append(os.path.join(".", "librairies","ai"))

import general

from planete import *
from configuration import *
from ai import *
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
  delta=None #Le taux de perturbation de la surface de la planète
  
  #Autres
  preImage = None #L'heure à laquelle la précédente image a été rendue
  
  joueur = None
  
  ### Initialisation ---------------------------------------------------
  def __init__(self):
    general.start = self
    
    if general.configuration.getConfiguration("affichage","general", "multitexturage","heightmap")=="shader":
      render.setShaderAuto()
      sa = ShaderAttrib.make( )
      sa = sa.setShader( loader.loadShader( 'data/shaders/terrainNormal.sha' ) )
      cam0 = base.cam.node( )
      cam0.setTagStateKey( 'Normal' )
      cam0.setTagState( 'True' , RenderState.make( sa ) )
    
    #Configuration de DEBUG
    general.DEBUG_GENERE_PLANETE = general.configuration.getConfiguration("debug", "planete", "debug_genere_planete","f")=="t"
    general.DEBUG_CHARGE_PLANETE = general.configuration.getConfiguration("debug", "planete", "debug_charge_planete","f")=="t"
    general.DEBUG_CHARGE_PLANETE_VERBOSE = general.configuration.getConfiguration("debug", "planete", "debug_charge_planete_verbose","f")=="t"
    general.DEBUG_AI_GRAPHE_DEPLACEMENT_CONSTRUCTION = general.configuration.getConfiguration("debug", "ai", "debug_ai_graphe_deplacement_construction","f")=="t"
    general.DEBUG_AI_GRAPHE_DEPLACEMENT_PROMENADE = general.configuration.getConfiguration("debug", "ai", "debug_ai_graphe_deplacement_promenade","f")=="t"
    general.DEBUG_AI_VA_VERS = general.configuration.getConfiguration("debug", "ai", "DEBUG_AI_VA_VERS","f")=="t"
    general.DEBUG_AI_SUIT_CHEMIN = general.configuration.getConfiguration("debug", "ai", "DEBUG_AI_SUIT_CHEMIN","f")=="t"
    general.DEBUG_AI_PING_PILE_COMPORTEMENT = general.configuration.getConfiguration("debug", "ai", "DEBUG_AI_PING_PILE_COMPORTEMENT","f")=="t"
    
    general.aiPlugin = AIPlugin()
    general.aiPlugin.scan()
    
    if base.camLens != None:
      general.interface = Interface()
    else:
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
        def afficheTexte(self, texte, type="normal", forceRefresh=False):
          print "[",type,"]",texte
        def ajouteJoueur(self, joueur):
          self.joueur = joueur
        def lanceInterface(self):
          self.start.fabriquePlanete()
          self.start.start()
          
      general.interface = DUMMY(self)
    
    if general.configuration.getConfiguration("debug", "panda", "DEBUG_PANDA_VIA_PSTATS","f")=="t":
      #Profile du code via PStat
      PStatClient.connect()

    if general.configuration.getConfiguration("affichage", "general", "afficheFPS","f")=="t":
      base.setFrameRateMeter(True)
    #Place une sphère à la place de la planète pendant la construction
    general.planete = Planete()
    general.planete.seuilSauvegardeAuto = -1
    general.planete.fabriqueNouvellePlanete(tesselation=3, delta=0.2)
    general.planete.fabriqueModel()
    
    general.io.positionneCamera(render)
    #On affiche le menu principal
    general.interface.lanceInterface()
    
  def start(self):
    """Lance le rendu et la boucle de jeu"""

    if general.planete == None:
      print "Vous devez créer une planète avant !"
      return
      
    #On ajoute les joueurs
    j1 = JoueurLocal("Joueur 1", (1.0, 0.0, 0.0, 1.0))
    self.joueur = j1
    j2 = JoueurIA("Joueur 2", (1.0, 0.0, 0.0, 1.0))
    general.planete.ajouteJoueur(j1)
    general.planete.ajouteJoueur(j2)
    for i in range(0, 10):
      OK=False
      while not OK:
        sommet = random.choice(general.planete.geoide.sommets)
        OK = sommet.length()>general.planete.geoide.niveauEau
      j1.ajouteSprite("test", sommet, "test")
    for i in range(0, 5):
      OK=False
      while not OK:
        sommet = random.choice(general.planete.geoide.sommets)
        OK = sommet.length()>general.planete.geoide.niveauEau
      j2.ajouteSprite("test", sommet, "test")

    #On construit le modèle 3D de la planète
    general.planete.fabriqueModel()
    general.planete.afficheTexte("Supression de la planète du menu")
    general.tmp.detruit()
    general.tmp = None
    general.io.positionneCamera()
    

  def afficheStat(self):
    general.afficheStatChrono()

  def ping(self, task):
    """Fonction exécutée à chaque image"""
    if general.configuration.getConfiguration("affichage","general", "multitexturage","heightmap")=="shader":
      render.setShaderInput( 'time', task.time )
    #Calculs du temps écoulé depuis l'image précédente
    if self.preImage != None:
      deltaT = task.time - self.preImage
    else:
      deltaT = task.time
    self.preImage = task.time
    
    #On indique que l'on veut toujours cette fonction pour la prochaine image
    return Task.cont
  ### Fin initialisation -----------------------------------------------
      
  ### Gestion de la planète --------------------------------------------
  def fabriquePlanete(self):
    """Construit une nouvelle planète via les gentils algos"""
    general.tmp=general.planete
    general.planete=None
    self.detruit()
    general.planete = Planete()
    tesselation = int(general.configuration.getConfiguration("planete", "generation", "tesselation", "4"))
    delta = float(general.configuration.getConfiguration("planete", "generation", "delta", "0.2"))
    general.planete.fabriqueNouvellePlanete(tesselation=tesselation, delta=delta)
    
  def chargePlanete(self, fichierPlanete):
    """Charge une planète depuis un fichier"""
    general.tmp=general.planete
    general.planete=None
    self.detruit()
    general.planete = Planete()
    general.planete.charge(fichier=fichierPlanete)
    
  def detruit(self):
    """Supprime le modèle et retire les structures de données"""
    if general.planete != None:
      general.planete.detruit()
      general.planete = None
  ### Fin gestion de la planète ----------------------------------------
      
  ### Autres -----------------------------------------------------------
  def modifieAltitude(self, direction):
    """Change l'altitude d'un point, si direction>0 alors l'altitude sera accrue sinon diminuée"""
    general.io.testeSouris()
    
    if general.planete.geoide.survol == None:
      return
    
    ndelta = general.planete.geoide.delta * direction * 0.01
    general.planete.geoide.elevePoint(general.planete.geoide.survol, ndelta)
    
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
  """while True:
    taskMgr.step()
    time.sleep(1.0 / 60.0)"""

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
  #On bloque les touches cholaxes de windows (shift pressé plus de 5s, plus de 5 fois rapidement, ...)
  loadPrcFileData("",u"disable-sticky-keys 1")
  #On dit à Panda d'utiliser le coeur le moins utilisé pour le moment
  loadPrcFileData("",u"client-cpu-affinity -1")
  import direct.directbase.DirectStart
  from direct.task import Task

  if base.camLens != None:
    base.camLens.setNear(0.001)

  if not profile:
    deb()
  else:
    print "Profiling..."
    cProfile.run('deb()', 'profiler.log')
