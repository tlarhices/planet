#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

import sys
import getopt
import os
sys.path.append(os.path.join(".", "librairies"))

import general

from planete import *
from configuration import *
from joueur import *
try:
    import psyco
    psyco.full()
    #psyco.profile()
except ImportError:
    print 
    print "Vous devriez installer Psyco (pour python) pour aller plus vite"
    print 

class Start:
  #Paramètres shader
  pushBias=0.1 #Calcul des ombres
  ambient=0.2 #Lumière ambiante
  
  #Paramètres éclairage
  soleil=None #Noeud du soleil (une caméra dans le cas de la projection d'ombre)
  distanceSoleil = None #Distance du soleil à la planète
  vitesseSoleil = None #Vitesse de rotation du soleil en pifometre/s
  
  #Paramètres de génération de la planète
  planete=None #L'instance de la classe planète
  delta=None #Le taux de perturbation de la surface de la planète
  
  #Gestion de la caméra
  camera = None
  cameraRayon = 6.0 #Distance de la caméra au centre de la planète
  cameraAngleX = 0.0 #Angle de rotation de la planète selon la verticale
  cameraAngleY = 0.0 #Angle de rotation de la planète selon l'horizontale
  cameraPasRotation = general.degVersRad(1.0) #Angle entre 2 positions de la caméra
  cameraPasZoom = 0.005 #Pas de zoom
  cameraAngleSurface = 50 #L'angle de la caméra à la surface
  
  #Gestion du clavier
  touches = None #Liste des touches pressées en ce moment 
  configClavier = None #Dictionnaire des affectations de commandes
                       #De la forme ["nom de touche"]="action"
                       #Par exemple ["escape"]="quitter"
  actions = None #Dictionnaire des actions accessibles via touches
                 #De la frome ["action"]=(fonction à exécuter,X)
                 #X peut être None
                 #X peut être un tuple (0, 1) ou (0, ) ou (a, b ,c)...
                 #X peut être une liste [a, g]...
                 #X peut être un dictionnaire {"nom parametre":valeur, ...}
                 
  #Autres
  preImage = None #L'heure à laquelle la précédente image a été rendue
  
  joueur = None
  
  ### Initialisation ---------------------------------------------------
  def __init__(self):
    
    render.setShaderAuto()
    
    #Configuration de DEBUG
    general.DEBUG_GENERE_PLANETE = general.configuration.getConfiguration("general", "debug_genere_planete","0")=="1"
    general.DEBUG_CHARGE_PLANETE = general.configuration.getConfiguration("general", "debug_charge_planete","0")=="1"
    general.DEBUG_CHARGE_PLANETE_VERBOSE = general.configuration.getConfiguration("general", "debug_charge_planete_verbose","0")=="1"
    general.DEBUG_AI_GRAPHE_DEPLACEMENT_CONSTRUCTION = general.configuration.getConfiguration("general", "debug_ai_graphe_deplacement_construction","0")=="1"
    general.DEBUG_AI_GRAPHE_DEPLACEMENT_PROMENADE = general.configuration.getConfiguration("general", "debug_ai_graphe_deplacement_promenade","0")=="1"
    general.WIREFRAME = general.configuration.getConfiguration("affichage", "wireframe","0")=="1"
    general.DEBUG_PANDAUI_GUI = general.configuration.getConfiguration("general", "DEBUG_PANDAUI_GUI","0")=="1"
    general.DEBUG_PANDAUI_CLIC = general.configuration.getConfiguration("general", "DEBUG_PANDAUI_CLIC","0")=="1"
    general.DEBUG_PANDAUI_PURGE = general.configuration.getConfiguration("general", "DEBUG_PANDAUI_PURGE","0")=="1"
    
    self.distanceSoleil = float(general.configuration.getConfiguration("generationPlanete", "distanceSoleil","10.0"))
    self.vitesseSoleil = float(general.configuration.getConfiguration("generationPlanete", "vitesseSoleil","1.0"))
    
    if general.configuration.getConfiguration("general", "DEBUG_PANDA_VIA_PSTATS","0")=="1":
      #Profile du code via PStat
      PStatClient.connect()

    if general.configuration.getConfiguration("affichage", "afficheFPS","0")=="1":
      base.setFrameRateMeter(True)
    
    #On donne des alias à certaines fonctions
    self.lierActionsFonctions()
    
    #On associe des touches à des actions
    self.touches = []
    self.configClavier = general.configuration.getConfigurationClavier()
    
    #On place la caméra dans un noeud facile à secouer
    self.camera = NodePath("cam")
    self.camera.reparentTo(render)
    base.camera.reparentTo(self.camera)
    
  def start(self):
    """Lance le rendu et la boucle de jeu"""

    if self.planete == None:
      print "Vous devez créer une planète avant !"
      return
      
    #Désactive la gestion par défaut de la souris
    base.disableMouse() 
    #Place la caméra à sa position
    self.camera.setPos(self.cameraRayon,0,0)
    self.positionneCamera()
    
    #Normalement panda envoie des evenements du type "arrow_left"
    #ou "alt_arrow_left", avec ça il envoie "alt" et "arow_left" tout seul
    base.mouseWatcherNode.setModifierButtons(ModifierButtons())
    base.buttonThrowers[0].node().setModifierButtons(ModifierButtons())
    #On redirige toutes les événements de touches vers 2 fonctions magiques
    base.accept('wheel_up', self.presseTouche, ['wheel_up'])
    base.accept('wheel_down', self.presseTouche, ['wheel_down'])
    base.buttonThrowers[0].node().setButtonDownEvent('presseTouche')
    base.buttonThrowers[0].node().setButtonUpEvent('relacheTouche')
    base.accept('presseTouche', self.presseTouche)
    base.accept('relacheTouche', self.relacheTouche)
    
    #Ajout du rayon magique de la souris
    base.cTrav = CollisionTraverser()
    self.myHandler = CollisionHandlerQueue()
    self.pickerNode=CollisionNode('mouseRay')
    self.pickerNP=camera.attachNewNode(self.pickerNode)
    self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
    self.pickerRay=CollisionRay()
    self.pickerNode.addSolid(self.pickerRay)
    base.cTrav.addCollider(self.pickerNP, self.myHandler)
    
    #On construit le modèle 3D de la planète
    self.planete.fabriqueModel()
    
    #Préparation des shaders
    print " - Ajout de la projection d'ombre..."
    eclairage = general.configuration.getConfiguration("affichage", "typeEclairage","shader")
    if eclairage == "flat":
      self.hackNoShadow()
    elif eclairage == "none":
      self.hackNoLight()
    else:
      if eclairage != "shader":
        print "Type d'éclairage inconnu", eclairage, "utilisation de 'shader' par defaut"
      if not self.fabriqueShader():
        self.exit("Impossible de continuer, on ne peut pas afficher les ombres")
    print " - Ajout de la projection d'ombre terminée"

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
    
    #On va faire exécuter self.ping a chaque image
    taskMgr.add(self.ping, "BouclePrincipale")

    #On lance la boucle magique de panda
    run()

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
    
    #Teste de la position de la souris
    if base.mouseWatcherNode.hasMouse():
      mpos=base.mouseWatcherNode.getMouse()
      x=mpos.getX()
      y=mpos.getY()
      seuil = 0.8
      #Regarde si la caméra est proche d'un bord et fait tourner la planète le cas échéant
      if x<-seuil:
        self.tourneCamera(self.cameraPasRotation*(x+seuil)/(1.0-seuil), 0.0)
      if x>seuil:
        self.tourneCamera(self.cameraPasRotation*(x-seuil)/(1.0-seuil), 0.0)
      if y<-seuil:
        self.tourneCamera(0.0, self.cameraPasRotation*(y+seuil)/(1.0-seuil))
      if y>seuil:
        self.tourneCamera(0.0, self.cameraPasRotation*(y-seuil)/(1.0-seuil))
      
    #Clavier
    self.gereTouche()
    
    #On ping la planète
    self.planete.ping(deltaT)
    
    #Fait tourner le soleil
    theta = task.time / math.pi * self.vitesseSoleil
    if self.soleil != None and self.soleil != 1:
      self.soleil.setPos(0.0, math.sin(theta)*self.distanceSoleil, math.cos(theta)*self.distanceSoleil)
      self.soleil.lookAt(0,0,0)
    
    #On indique que l'on veut toujours cette fonction pour la prochaine image
    return Task.cont
  ### Fin initialisation -----------------------------------------------
      
  ### Gestion de la planète --------------------------------------------
  def fabriquePlanete(self):
    """Construit une nouvelle planète via les gentils algos"""
    self.detruit()
    self.planete = Planete()
    self.actions["clear"] = (self.planete.afficheTexte,None)
    self.planete.fabriqueNouvellePlanete(tesselation=int(general.configuration.getConfiguration("generationPlanete", "tesselation", "4")), delta=float(general.configuration.getConfiguration("generationPlanete", "delta", "0.2")))
    self.camera.reparentTo(self.planete.racine)
    
  def detruit(self):
    """Supprime le modèle et retire les structures de données"""
    if self.planete != None:
      self.planete.detruit()
      self.planete = None
  ### Fin gestion de la planète ----------------------------------------
    
  ### Gestion de l'éclairage -------------------------------------------
  def fabriqueShader(self):
    """Ajoute le shader qui fait les projections d'ombres"""
    
    #Vérification de la carte graphique
    if (base.win.getGsg().getSupportsBasicShaders()==0):
      raw_input("Planete: Pas de shader dans la carte graphique.")
      return False
    if (base.win.getGsg().getSupportsDepthTexture()==0):
      raw_input("Planete: Pas de texture de profondeur.")
      return False
  
    #Crée une fenêtre de rendu hors écran
    winprops = WindowProperties.size(512,512)
    props = FrameBufferProperties()
    props.setRgbColor(1)
    props.setAlphaBits(1)
    props.setDepthBits(1)
    LBuffer = base.graphicsEngine.makeOutput(
             base.pipe, "offscreen buffer", -2,
             props, winprops,
             GraphicsPipe.BFRefuseWindow,
             base.win.getGsg(), base.win)

    if (LBuffer == None):
      raw_input("Planete: Pas de buffer hors écran.")
      return False

    #render.setShaderAuto()

    #Ajoute une texture de profondeur
    Ldepthmap = Texture()
    LBuffer.addRenderTexture(Ldepthmap, GraphicsOutput.RTMBindOrCopy, GraphicsOutput.RTPDepthStencil)
    if (base.win.getGsg().getSupportsShadowFilter()):
        Ldepthmap.setMinfilter(Texture.FTShadow)
        Ldepthmap.setMagfilter(Texture.FTShadow) 

    #Un buffer en couleur pour le debug
    Lcolormap = Texture()
    LBuffer.addRenderTexture(Lcolormap, GraphicsOutput.RTMBindOrCopy, GraphicsOutput.RTPColor)

    #On fabrique une caméra qui sera notre lampe
    self.soleil=base.makeCamera(LBuffer)
    self.soleil.node().setScene(render)

    #On prépare les variables du shader
    render.setShaderInput('light', self.soleil)
    render.setShaderInput('Ldepthmap', Ldepthmap)
    render.setShaderInput('ambient', self.ambient,0,0,1.0)
    render.setShaderInput('texDisable', 0,0,0,0)
    render.setShaderInput('scale', 1,1,1,1)
    render.setShaderInput('push',self.pushBias,self.pushBias,self.pushBias,0)

    #On place le shader sur le soleil
    lci = NodePath(PandaNode("Light Camera Initializer"))
    lci.setShader(Shader.load('data/shaders/caster.sha'))
    self.soleil.node().setInitialState(lci.getState())
  
    #On place un shader sur la caméra écran
    #Si la carte 3D a du hardware pour ça, on l'utilise
    mci = NodePath(PandaNode("Main Camera Initializer"))
    if (base.win.getGsg().getSupportsShadowFilter()):
        mci.setShader(Shader.load('data/shaders/shadow.sha'))
    else:
        mci.setShader(Shader.load('data/shaders/shadow-nosupport.sha'))
    base.cam.node().setInitialState(mci.getState())
    
    #On configure notre soleil
    self.soleil.setPos(0,-40,40)
    self.soleil.lookAt(0,0,0)
    self.soleil.node().getLens().setFov(30)
    self.soleil.node().getLens().setNearFar(20,60)
    #self.soleil.node().showFrustum()
  
    #base.bufferViewer.toggleEnable()
    return True
    
  def hackNoShadow(self):
    """Passe a travers les securités qui font qu'on peut pas lancer le jeu sans ombre"""
    print "DANGER :: HACK :: Ombres desactivées ! [planet.py]"
    light = PointLight('soleil')
    light.setColor(VBase4(0.9, 0.9, 0.9, 0.8))
    self.soleil = render.attachNewNode(light)
    self.soleil.setPos(0,0,0)
    self.soleil.setLightOff()
    #self.soleil.setColor(1.0, 0.7, 0.3)
    
    #teste si la carte graphique supporte les shaders
    if (base.win.getGsg().getSupportsBasicShaders() == 0):
      print ":("
    else:
      print ":)"
      
    #applique un bloom
    if general.configuration.getConfiguration("general", "utiliseBloom","0")=="1":
      from direct.filter.CommonFilters import CommonFilters
      self.filters = CommonFilters(base.win, base.cam)
      filterok = True
      filterok = filterok and self.filters.setBloom(blend=(0.3,0.4,0.3,0), mintrigger=0.6, maxtrigger=1.0, desat=0.6, intensity=3.0, size="small")
      #filterok = filterok and self.filters.setCartoonInk()
    
      if not filterok:
        print "Erreur d'initialisation des filtres"
      
    render.setLight(self.soleil)
    
    cardMaker = CardMaker('soleil')
    cardMaker.setFrame(-0.5, 0.5, -0.5, 0.5)
    bl = render.attachNewNode(cardMaker.generate())
    #Applique la tecture dessus
    tex = loader.loadTexture("data/textures/soleil.png")
    bl.setTexture(tex)
    #Active la transprence
    bl.setTransparency(TransparencyAttrib.MDual)
    #Fait une mise à l'échelle
    bl.setScale(0.8)
    #On fait en sorte que la carte soit toujours tournée vers la caméra, le haut vers le haut
    bl.setBillboardPointEye()

    #bl = loader.loadModel("./data/modeles/sphere.egg")
    bl.reparentTo(self.soleil)
    
    self.soleil.reparentTo(render)
    
    
  def hackNoLight(self):
    """Passe a travers les securités qui font qu'on peut pas lancer le jeu sans lumière"""
    print "DANGER :: HACK :: Eclairage desactivé ! [planet.py]"
    self.soleil = loader.loadModel("./data/modeles/sphere.egg")
    self.soleil.reparentTo(render)
  ### Fin Gestion de l'éclairage ---------------------------------------

  ### Gestion de la caméra ---------------------------------------------
  def positionneCamera(self):
    """Place la caméra dans l'univers"""
    #La position de la caméra est gérée en coordonnées sphériques
    if general.normaliseVecteurCarre(self.camera.getPos())!=self.cameraRayon*self.cameraRayon:
      coord = general.multiplieVecteur(general.normaliseVecteur(self.camera.getPos()), self.cameraRayon)
    
    self.camera.setPos(coord[0], coord[1], coord[2])
    #La caméra regarde toujours le centre de la planète
    self.camera.lookAt(Point3(0,0,0), self.planete.racine.getRelativeVector(self.camera, Vec3(0,0,1)))
    angle = self.cameraAngleSurface-self.cameraAngleSurface*(-0.5+(self.cameraRayon-1.0)/(2*float(general.configuration.getConfiguration("generationPlanete", "delta", "0.2"))))
    angle = max(0.0, angle)
    base.camera.setP(angle)

  def zoomPlus(self):
    """Approche la caméra de la planète"""
    self.cameraRayon -= self.cameraRayon*self.cameraPasZoom
    self.cameraRayon = max(self.cameraRayon, 1.0 + float(general.configuration.getConfiguration("generationPlanete", "delta", "0.2")) + 0.001)
    self.positionneCamera()

  def zoomMoins(self):
    """Éloigne la caméra de la planète"""
    self.cameraRayon += self.cameraRayon*self.cameraPasZoom
    #On empèche la caméra de passer derrière le soleil
    self.cameraRayon = min(self.cameraRayon, self.distanceSoleil-0.01)
    self.positionneCamera()
    
  def tourneCamera(self, anglex, angley):
    """Tourne la caméra autour de la planète"""
    self.camera.setPos(self.camera, anglex*self.cameraRayon, 0, angley*self.cameraRayon)
    self.positionneCamera()
  ### Fin Gestion de la caméra -----------------------------------------
    
  ### Gestion du clavier/souris ----------------------------------------
  def presseTouche(self, touche):
    """Une touche a été pressée, on l'ajoute a la liste des touches"""
    self.touches.append(touche)
    self.gereTouche()
    
  def relacheTouche(self, touche):
    """Une touche a été relâchée, on l'enlève de la liste des touches"""
    while self.touches.count(touche)>0:
      self.touches.remove(touche)
      
  def gereTouche(self):
    """Gère les touches clavier"""
    for touche in self.touches:
      #La touche est configurée
      if touche in self.configClavier.keys():
        action = self.configClavier[touche]
        if action not in self.actions.keys():
          #La touche a été configurée pour faire un truc mais on saît pas ce que c'est
          print "Type d'action inconnue : ", action
        else:
          #On lance la fonction
          self.appelFonction(*self.actions[action])
      
  def lierActionsFonctions(self):
    """On donne des noms gentils à des appels de fonction moins sympas"""
    self.actions = {}
    self.actions["quitter"] = (sys.exit,(0,))
    self.actions["tournecameraverslagauche"] = (self.tourneCamera,(self.cameraPasRotation,0.0))
    self.actions["tournecameraversladroite"] = (self.tourneCamera,(-self.cameraPasRotation,0.0))
    self.actions["tournecameraverslehaut"] = (self.tourneCamera,(0.0,-self.cameraPasRotation))
    self.actions["tournecameraverslebas"] = (self.tourneCamera,(0.0,self.cameraPasRotation))
    self.actions["zoomplus"] = (self.zoomPlus,None)
    self.actions["zoommoins"] = (self.zoomMoins,None)
    self.actions["modifiealtitude+"] = (self.modifieAltitude,(1.0,))
    self.actions["modifiealtitude-"] = (self.modifieAltitude,(-1.0,))
    self.actions["affichestat"] = (self.afficheStat,None)
    self.actions["screenshot"] = (self.screenShot,None)
    
  def appelFonction(self, fonction, parametres):
    """Appel la fonction fonction en lui passant les paramètres décris"""
    if parametres==None:
      fonction()
    elif isinstance(parametres, dict):
      fonction(**parametres)
    elif isinstance(parametres, list) or isinstance(parametres, tuple):
      fonction(*parametres)
    else:
      print "ERREUR : Start.appelFonction, parametres doit être None, un tuple, une liste ou un dictionnaire"
      fonction[parametre]
  ### Fin gestion du clavier/souris ------------------------------------
      
  ### Autres -----------------------------------------------------------
  def modifieAltitude(self, direction):
    """Change l'altitude d'un point, si direction>0 alors l'altitude sera accrue sinon diminuée"""
    
    self.testeSouris()
    
    if self.planete.survol == None:
      return
    
    ndelta = self.planete.delta * direction * 0.01
    self.planete.elevePoint(self.planete.survol, ndelta)
    
  select = None
    
  def testeSouris(self):
    """Teste ce qui se trouve sous le curseur de la souris"""
    if base.mouseWatcherNode.hasMouse():
      mpos=base.mouseWatcherNode.getMouse()
      x=mpos.getX()
      y=mpos.getY()
      
      #Test du survol de la souris  
      self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
      base.cTrav.traverse(render)
      if self.myHandler.getNumEntries() > 0:
        self.myHandler.sortEntries()
        objet = self.myHandler.getEntry(0).getIntoNodePath().findNetPythonTag('type')
        if objet.getPythonTag('type') == "sol":
          coord = self.myHandler.getEntry(0).getSurfacePoint(self.planete.racine)
          if self.select != None:
            self.select.marcheVers(coord)
            self.select = None
          else:
            idsommet = self.planete.trouveSommet(coord)
            self.planete.survol = idsommet
        elif objet.getPythonTag('type') == "sprite":
            self.planete.afficheTexte("Clic sur le sprite : "+str(objet.getPythonTag('id')+" cliquez sur le sol où vous voulez qu'il aille"))
            self.select = objet.getPythonTag('instance')
        elif objet.getPythonTag('type') == "eau":
            print "clic dans l'eau"
        else:
          print "Clic sur un objet au tag inconnu : ", objet.getPythonTag('type')
          
        #On demande aux facettes de se redessiner
        #for element in self.planete.sommetDansFace[idsommet]:
        #  element.sommetAChange(idsommet)
      else:
        self.planete.survol = None
        
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
  print "  -b / --bug :"
  print "     Affiche le détails des différents bugs ouverts en ce moment"
  print "     --bug est plus verbeux"
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
    opts, args = getopt.getopt(sys.argv[1:], "hbc:p", ["help", "config=", "profiler", "bug"])
except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    aideCommande()
    sys.exit(2)

def getBug(besoinDetails=False):
  from urllib2 import urlopen
  print "Lecture depuis http://bitbucket.org..."
  data = urlopen("http://bitbucket.org/tlarhices/planet/issues/?status=new&status=open").read()

  bugs = []
  cpt=0
  for element in data.split('href="/tlarhices/planet/issue/'):
    if cpt%2==1:
      adresse = 'http://bitbucket.org/tlarhices/planet/issue/'+element.split("\">")[0]
      bugs.append(adresse)
    elif cpt!=0:
      milestone = element.split(";milestone=")[1].split("\" class=")[0].strip().upper()
      if milestone!="":
        print "!!!!!!!!!!!!!!!!!!!!!!!"
      else:
        print "#######################"
      print element.split("</a")[0].split(">")[-1].strip().replace("&#39;","'").capitalize()
      if milestone!="":
        print "!!! MILESTONE ",milestone,"!!!"
      print bugs[-1]
      print 
      if besoinDetails:
        details = urlopen(bugs[-1]).read()
        print details.split("issues-issue-description")[1].split("</div>")[0][2:].replace("<p>","").replace("</p>","").replace("<br />","").replace("<em>","").replace("</em>","").replace("<sup>","").replace("</sup>","").strip()
      if milestone!="":
        print "!!!!!!!!!!!!!!!!!!!!!!!"
      else:
        print "#######################"
      print
    cpt+=1
    
  print "Il y a %i bugs ouverts en ce moment" %len(bugs)
  

def deb():
  #Création de l'instance
  print "Initialisation..."  
  start = Start()
  #Construction de la planète
  print " - Création d'une nouvelle planète..."
  start.fabriquePlanete()
  print " - Création d'une nouvelle planète terminée"
  #Lancement du jeu
  print "Initialisation terminée"
  print "Lancement..."
  start.start()


fichierConfig = None
profile = False
besoinDetails = False
for o, a in opts:
  if o in ("-h", "--help"):
    aideCommande()
    sys.exit()
  elif o in ("-c", "--config"):
    fichierConfig = a
  elif o =="-b":
    getBug(False)
    raw_input()
  elif o =="--bug":
    getBug(True)
    raw_input()
  elif o in ("-p", "--profiler"):
    try:
      import cProfile
      profile = True
    except:
      pass
  else:
    assert False, "Paramètre inconnu"
    
if fichierConfig==None:
  fichierConfig="config.cfg"

#On charge le fichier de config
general.configuration = Configuration()
general.configuration.charge(fichierConfig)

from pandac.PandaModules import *

#Change le titre de la fenêtre
loadPrcFileData("",u"window-title Planète".encode("iso8859"))
#Change la résolution de la fenêtre
loadPrcFileData("",u"win-size "+general.configuration.getConfiguration("affichage", "resolution","640 480"))
#Kicke la synchro avec VSynch pour pouvoir dépasser les 60 FPS
loadPrcFileData("",u"sync-video #f")

import direct.directbase.DirectStart
from direct.task import Task

base.camLens.setNear(0.001)

if not profile:
  deb()
else:
  cProfile.run('deb()', 'profiler.log')
