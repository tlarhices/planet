"""

    The drawer tries to draw the ui in as little goems 
    and triangles as possible
    
    It tries to use only a single vertex buffer and only 
    a single texture
    
    It clips polygons in software rather then resorting to 
    scissor tests or clip planes which reduces trips to the card
    and speeds stuff up.

"""

from pandac.PandaModules import *
import os



from random import *
def randVec():
    """ reandom vector """
    return Vec3(random()-.5,random()-.5,random()-.5)


from eggatlas import EggAtlas

from theme import Stretch


drawer2D=False
try:
    draw=MeshDrawer2D()
    drawer2D=True
except:
    pass


class Drawer:

    def __init__(self):
        """ create the drawer """
        vfs = VirtualFileSystem.getGlobalPtr()
        
        self.atlas = EggAtlas(gui.theme.ATLAS)
        
        self.image = loader.loadTexture(gui.theme.TEXTURE)
        self.image.setCompression(Texture.CMOff)
        self.image.setMinfilter(Texture.FTNearest)
        self.image.setMagfilter(Texture.FTLinear)
        self.image.reload()

        self.drawer = self.makeThemeDrawer(gui.node)
        
        self.w = float(self.image.getXSize())
        self.h = float(self.image.getYSize())

        self.color = Vec4(1,1,1,1)

    def makeDrawer(self,node):
        """
            make generic 2d drawer 
        """
        if drawer2D:
            drawer = MeshDrawer2D()
        else:
            drawer = MeshDrawer()
            drawer.setPlateSize(32)
        drawer.setBudget(3000)

        drawerNode = drawer.getRoot()
        drawerNode.reparentTo(node)
        drawerNode.setDepthWrite(False)
        drawerNode.setTransparency(True)
        drawerNode.setTwoSided(True)
        drawerNode.setBin("fixed",0)
        drawerNode.setLightOff(True)
        drawerNode.node().setBounds(OmniBoundingVolume())
        drawerNode.node().setFinal(True) 
		
		# debug wire frame
        #cc = drawerNode.copyTo(node)
        #cc.setRenderModeWireframe()

        return drawer

    def makeThemeDrawer(self,node):
        """
            make the theme drawer
        """
        themeDrawer = self.makeDrawer(node)
        themeDrawer.getRoot().setTexture(self.image)
        return themeDrawer


    def draw(self,children):
        """ draws all of the children """
        self.clip = [(0,0,gui._width+100, gui._height+100)]

        if drawer2D:
            self.drawer.setClip(0,0,gui._width+100, gui._height+100)
            self.drawer.begin()
        else:
            self.drawer.begin(base.cam, render)
        z = 0
        for child in reversed(children):
            z += 1
            self.drawChild(0,0,z,child)
            
        self.drawer.end()
        
    def drawChild(self,x,y,z,thing):
        """ draws a single thing """
        self.z = z
        
        
        
        if not thing.visable:
            return 
        
        
        self.color = Vec4(*thing.color)
        
        realX = x+float(thing._x)
        realY = y+float(thing._y)
        
        if thing.style:
            style = gui.theme.define(thing.style)
            if style:
                style.draw(
                    self,
                    (realX,realY),
                    (float(thing._width),float(thing._height)))
        
        if thing.clips:
            # set clip stuff
            if drawer2D:
                self.pushClip(realX,realY,realX+thing._width,realY+thing._height)
            else:
                self.doClip(realX,realY,realX+thing._width,realY+thing._height)
            
        if thing.icon:
            rect = self.atlas.getRect(thing.icon)
            if rect: 
                self.color = thing.color
                u,v,us,vs = rect
                self.rectStreatch((realX,realY,us,vs),(u,v,us,vs))
            
        if thing.text:
            # draw text stuff
            if thing.editsText:
                self.drawEditText(
                    gui.theme.defineFont(thing.font),
                    thing.text,
                    realX,
                    realY,
                    thing.selection,
                    thing.caret)
            else:
                self.drawText(
                    gui.theme.defineFont(thing.font),
                    thing.text,
                    realX,
                    realY)
           
            
        if thing.children:
            for child in thing.children:
                z += 1
                self.drawChild(realX,realY,z,child)
                
        if thing.clips:
            if drawer2D:
                self.popClip()
            else:
                self.clip.pop()
    
     
    
    def drawText(self, font, text, x, y):
        """ 
            draws just text
        """
        self.color = Vec4(*font.color)
        
        name =  font.name
        ox = x
        baseLetter = self.atlas.getChar(name + str(ord("T")))
        omaxh = baseLetter[3] - baseLetter[4][1]

        for line in text.split("\n"):
            build = []
            maxh = omaxh  
                
            for c in line:
                code = ord(unicode(c))
                if code <= 32:
                    u,v,w,h,e = self.atlas.getChar(name + str(77))
                    x += e[0]
                    continue
                try:
                  u,v,w,h,e = self.atlas.getChar(name + str(code))
                except KeyError:
                  u,v,w,h,e = self.atlas.getChar(name + "empty")
                build.append((x,y+e[1],u,v,w,h))
                x += e[0]
                maxh = max(maxh,h-e[1])
                 
            for x,y,u,v,w,h in build:
                self.rectStreatch((x,y+maxh-h,w,h),(u,v,w,h))
                
            x = ox     
            y += maxh
    
    def drawEditText(self, font, text, x, y, selection=(0,0), caret=-1):
        """ 
            draws the text
            and selection
            and caret
        """
        self.color = Vec4(*font.color)
        name =  font.name
        
        char_count = 0 
        ox = x
        baseLetter = self.atlas.getChar(name + str(ord("T")))
        omaxh = baseLetter[3] - baseLetter[4][1]

        for line in text.split("\n"):
            build = []
            maxh = omaxh  
                
            for c in line:
                if char_count == caret:
                     u,v,w,h,e = self.atlas.getChar(name + str(ord('|')))
                     build.append((x-w/2,y+e[1],u,v,w,h))
                char_count += 1 
                
                code = ord(unicode(c))
                if code <= 32:
                    u,v,w,h,e = self.atlas.getChar(name + str(77))
                    x += e[0]
                    continue
                try:
                  u,v,w,h,e = self.atlas.getChar(name + str(code))
                except KeyError:
                  u,v,w,h,e = self.atlas.getChar(name + "empty")
                build.append((x,y+e[1],u,v,w,h))
                x += e[0]
                maxh = max(maxh,h-e[1])
            
            else:
                if char_count == caret:
                     u,v,w,h,e = self.atlas.getChar(name + str(ord('|')))
                     build.append((x-w/2,y+e[1],u,v,w,h))
                char_count += 1 
                 
            for x,y,u,v,w,h in build:
                self.rectStreatch((x,y+maxh-h,w,h),(u,v,w,h))
                
            x = ox     
            y += maxh    
        
    def rect(self,(x,y,xs,ys),(u,v)):
        """ draw a rectangle """
        us = xs
        vs = ys
        self.rectStreatch((x,y,xs,ys),(u,v,us,vs))
        
        
    def doClip(self, xs,ys,xe,ye):
        self.pushClip(xs,ys,xe,ye)


    def popClip(self):
        self.clip.pop()
        xs,ys,xe,ye = self.clip[-1]
        self.drawer.setClip(xs,ys,xe-xs,ye-ys)
            
    def pushClip(self,xs,ys,xe,ye):
        bxs,bys,bxe,bye = self.clip[-1]
        
        xs = max(bxs,xs)
        ys = max(bys,ys)
        xe = min(bxe,xe)
        ye = min(bye,ye)
        
        self.clip.append((xs,ys,xe,ye))   
        
        if drawer2D:
            self.drawer.setClip(xs,ys,xe-xs,ye-ys)

    def rectStreatch(self,(x,y,xs,ys),(u,v,us,vs)):
        """ draw a generic stretched rectangle """
        # do clipping now:
        
        if not drawer2D:
          clipXStart,clipYStart,clipXEnd,clipYEnd = self.clip[-1]
          
          if (x >= clipXStart and 
              y >= clipYStart and
              x+xs <= clipXEnd and
              y+ys <= clipYEnd):
              
                  pass
              
          elif ((x >= clipXStart or x+xs <= clipXEnd) and 
                (y >= clipYStart or y+ys <= clipYEnd)):
              
              if xs==0:
                xRatio = 1.0
              else:
                xRatio = us/xs
              if ys==0:
                yRatio = 1.0
              else:
                yRatio = vs/ys 
              
              if x > clipXEnd: return
              if y > clipYEnd: return
              if x+xs < clipXStart: return
              if y+ys < clipYStart: return
              
              
              if x < clipXStart: 
                  dt = clipXStart-x
                  x  += dt
                  xs -= dt               
                  u  += dt*xRatio
                  us -= dt*xRatio 
                                   
              if y < clipYStart: 
                  dt = clipYStart-y
                  y  += dt
                  ys -= dt
                  v  += dt*yRatio 
                  vs -= dt*yRatio
                  
              if x+xs > clipXEnd: 
                  dt = xs + x - clipXEnd
                  xs -= dt 
                  us -= dt*xRatio
                               
                 
              if y+ys > clipYEnd: 
                  dt = ys + y - clipYEnd
                  ys -= dt 
                  vs -= dt*yRatio         

          else:
              return
    
           
           # final draw thing
           
          z = 0
          color = self.color 
          v1 = Vec3(x,    z,y)
          v2 = Vec3(x+xs, z,y)
          v3 = Vec3(x+xs, z,y+ys)
          v4 = Vec3(x,    z,y+ys)
           
           
        color = self.color
        
        w = self.w
        h = self.h
        
        u,v,us,vs = u/w,1-v/h,(u+us)/w,1-(v+vs)/h
        if not drawer2D:
          self.drawer.tri( 
              v1, color, Vec2(u,v),
              v2, color, Vec2(us,v),
              v3, color, Vec2(us,vs))
          self.drawer.tri( 
              v3, color, Vec2(us,vs),
              v4, color, Vec2(u,vs),
              v1, color, Vec2(u,v))
        
        else:
          self.drawer.rectangle( 
              x,y,xs,ys,
              u,v,us-u,vs-v,
              #u/self.w,v/self.h,us/self.w,vs/self.h,
              color)


