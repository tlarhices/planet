#!/usr/bin/env python
# -*- coding: utf-8 -*-

camera1 = None
camera2 = None
root1 = None
root2 = None
root1_model = None
root2_model = None
card1 = None
card2 = None
card3 = None

def setCamera():
    global camera1
    global camera2
    global root1
    global root2
    camera1=createCamera((0.0,0.5,0,1))
    camera1.reparentTo(root1)
    camera1.lookAt(root1)
    camera2=createCamera((0.5,1.0,0,1))
    camera2.reparentTo(root2)
    camera2.lookAt(root2)
    base.camNode.setActive(False) #disable default cam

def createCamera(dispRegion):
    camera=base.makeCamera(base.win,displayRegion=dispRegion)
    camera.node().getLens().setAspectRatio(3.0/4.0)
    camera.node().getLens().setFov(45)
    camera.setPos(0,-8,0)
    return camera

def map3dToRender2d(node, point, camera):
    p3 = camera.getRelativePoint(node, point)
    p2 = Point2()
    if not camera.node().getLens().project(p3, p2):
       return None
    return (p2[0]+1.0)/2.0, (-p2[1]+1.0)/2.0
    
def resnap():
  text1, text2, text3 = snap()
  
  if card1!=None:
    card1.setTexture(text1, 1)
  if card2!=None:
    card2.setTexture(text2, 1)
  if card3!=None:
    card3.setTexture(text3, 1)
  
def snap():
  tex1 = Snap("1")
  root1_model.setH(root1_model.getH()+90)
  tex2 = Snap("2")
  root1_model.setH(root1_model.getH()-90)
  h,p,r = camera1.getH(), camera1.getP(), camera1.getR()
  pos = camera1.getPos()
  d = (camera1.getPos()-root1_model.getPos()).length()
  camera1.setPos(0,0,d)
  camera1.lookAt(root1)
  tex3 = Snap("3")
  camera1.setH(h), camera1.setP(p), camera1.setR(r)
  camera1.setPos(pos)
  return tex1, tex2, tex3
    
def Snap(fich=None):
  base.graphicsEngine.renderFrame()
  base.graphicsEngine.renderFrame()
  bounds = root1_model.getTightBounds()
  pt1, pt2 = map3dToRender2d(root1, bounds[0], camera1), map3dToRender2d(root1, bounds[1], camera1)
  if pt1==None or pt2==None:
    print "Err, bndbox hors ecran"
  minx = min(pt1[0], pt2[0])
  miny = min(pt1[1], pt2[1])
  maxx = max(pt1[0], pt2[0])
  maxy = max(pt1[1], pt2[1])
  X = int(minx*base.win.getXSize()/2.0), int(maxx*base.win.getXSize()/2.0+0.5)
  Y = int(miny*base.win.getYSize()), int(maxy*base.win.getYSize()+0.5)
  TX = X[1]-X[0]
  TY = (Y[1]-Y[0])*1.1
  capture = PNMImage()
  camera1.node().getDisplayRegion(0).getScreenshot(capture)
  image = PNMImage(TX, TY)
  image.addAlpha()
  image.copySubImage(capture, 0, 0, X[0], Y[0], TX, TY)
  if fich!=None:
    image.write(Filename(str(fich)+".png"))
  texture = Texture()
  texture.load(image)
  return texture

def loadModel(modelName, root):
  mdl = loader.loadModel(modelName)
  mdl.reparentTo(root)
  
def createBillboard(root, bounds):
  global card1
  p1, p2 = bounds
  cardMaker = CardMaker('lod')
  cardMaker.setFrame(p1[0], p2[0], p1[2], p2[2])
  cardMaker.setHasNormals(True)
  card1 = root.attachNewNode(cardMaker.generate())
  card1.setBillboardAxis()
  card1.setTransparency(TransparencyAttrib.MDual)

def createCrossBillboard(root, bounds, texture1, texture2):
  global card1
  global card2
  p1, p2 = bounds
  cardMaker = CardMaker('lod')
  cardMaker.setFrame(p1[0], p2[0], p1[2], p2[2])
  cardMaker.setHasNormals(True)
  card1 = root.attachNewNode(cardMaker.generate())
  card1.setTwoSided(True)
  card1.setTransparency(TransparencyAttrib.MDual)
  card1.setTexture(texture1)
  card2 = root.attachNewNode(cardMaker.generate())
  card2.setTwoSided(True)
  card2.setTransparency(TransparencyAttrib.MDual)
  card2.setH(90)
  card2.setTexture(texture2)
  
def createCrossTopBillboard(root, bounds, texture1, texture2, textureTop):
  global card1
  global card2
  p1, p2 = bounds
  cardMaker = CardMaker('lod')
  cardMaker.setFrame(p1[0], p2[0], p1[2], p2[2])
  cardMaker.setHasNormals(True)
  card1 = root.attachNewNode(cardMaker.generate())
  card1.setTwoSided(True)
  card1.setTransparency(TransparencyAttrib.MDual)
  card1.setTexture(texture1)
  card2 = root.attachNewNode(cardMaker.generate())
  card2.setTwoSided(True)
  card2.setTransparency(TransparencyAttrib.MDual)
  card2.setH(90)
  card2.setTexture(texture2)
  print p1, p2
  cardMaker.setFrame(p1[0], p2[0], p1[1], p2[1])
  cardMaker.setHasNormals(True)
  card3 = root.attachNewNode(cardMaker.generate())
  card3.setTwoSided(True)
  card3.setTransparency(TransparencyAttrib.MDual)
  card3.setP(90)
  card3.setPos((p1[2]+p2[2])/2)
  card3.setTexture(textureTop)

def zoomIn():
  global camera1
  global camera2
  global root1
  camera1.setPos(camera1, (0,0.1,0))
  camera2.setPos(camera2, (0,0.1,0))
  print (root1.getPos()-camera1.getPos()).length()
  
def zoomOut():
  global camera1
  global camera2
  global root1
  camera1.setPos(camera1, (0,-0.1,0))
  camera2.setPos(camera2, (0,-0.1,0))
  print (root1.getPos()-camera1.getPos()).length()

def camUp():
  global camera1
  global camera2
  camera1.setPos(camera1, (0,0.0,-0.1))
  camera2.setPos(camera2, (0,0.0,-0.1))
  camera1.lookAt(root1)
  camera2.lookAt(root2)

def camDown():
  global camera1
  global camera2
  camera1.setPos(camera1, (0,0.0,0.1))
  camera2.setPos(camera2, (0,0.0,0.1))
  camera1.lookAt(root1)
  camera2.lookAt(root2)

def turnLeft():
  global root1_model
  global root2_model
  root1_model.setH(root1_model.getH()+1)
  root2_model.setH(root2_model.getH()+1)

def turnRight():
  global root1
  global root2
  root1_model.setH(root1_model.getH()-1)
  root2_model.setH(root2_model.getH()-1)

if __name__ == "__main__":
  from pandac.PandaModules import *
  #Change le titre de la fenêtre
  loadPrcFileData("",u"window-title Planète".encode("iso8859"))
  loadPrcFileData("",u"win-size 320 240")
  #Kicke la synchro avec VSynch pour pouvoir dépasser les 60 FPS
  loadPrcFileData("",u"sync-video #f")

  import direct.directbase.DirectStart
  
  root1=NodePath("root1")
  root2=NodePath("root2")
  root1_model=NodePath("root1_model")
  root2_model=NodePath("root2_model")
  root1_model.reparentTo(root1)
  root2_model.reparentTo(root2)
  
  setCamera()
  loadModel("cherry.egg", root1_model)
  tex1, tex2, tex3=snap()
  createCrossTopBillboard(root2_model, root1_model.getTightBounds(), tex1, tex2, tex3)

  base.accept("arrow_up-repeat", zoomIn)
  base.accept("arrow_down-repeat", zoomOut)
  base.accept("arrow_left-repeat", turnLeft)
  base.accept("arrow_right-repeat", turnRight)
  base.accept("w-repeat", camUp)
  base.accept("s-repeat", camDown)

  run()