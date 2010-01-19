
from pandac.PandaModules import *
import eggatlas
import os

class Stretch:
    
    def __init__(self,name):
        self.name = name
        self.border = 0

    def draw(self,drawer,pos,size):
        x,y = pos[0],pos[1]
        xs,ys = size[0],size[1]
        u,v,us,vs = drawer.atlas.getRect(self.name) 
        drawer.rectStreatch((x,y,xs,ys),(u,v,us,vs))

class IconLike:
    
    def __init__(self,name):
        self.name = name
        self.border = 0

    def draw(self,drawer,pos,size):
        x,y = pos[0],pos[1]
        u,v,us,vs = drawer.atlas.getRect(self.name)
        drawer.rectStreatch((x,y,us,vs),(u,v,us,vs))

class Single:
    
    def __init__(self,name):
        self.name = name
        self.border = 0

    def draw(self,drawer,pos,size):
        x,y = pos[0],pos[1]
        u,v,us,vs = drawer.atlas.getRect(self.name)
        xs,ys = min(us,size[0]),min(vs,size[1])
        drawer.rectStreatch((x,y,xs,ys),(u,v,xs,ys))
        
class StretchBorder:
    
    def __init__(self,name,border):
        self.name = name
        self.border = border
    
    def draw(self,drawer,pos,size):
        u,v,us,vs = drawer.atlas.getRect(self.name) 
        b = self.border 
        
        u += b
        v += b
        us -= b*2
        vs -= b*2
        
        self.drawBlock(drawer,pos,size,u,v,us,vs) # center
        x,y = pos[0],pos[1]
        xs,ys = size[0],size[1]
        
        self.drawBlock(drawer,Vec2(x,y-b),Vec2(xs,b),u,v-b,us,b) # N
        self.drawBlock(drawer,Vec2(x,y+ys),Vec2(xs,b),u,v+vs,us,b) # S
        self.drawBlock(drawer,Vec2(x-b,y),Vec2(b,ys),u-b,v,b,vs) # W
        self.drawBlock(drawer,Vec2(x+xs,y),Vec2(b,ys),u+us,v,b,vs) # E

        self.drawBlock(drawer,Vec2(x-b,y-b),Vec2(b,b),u-b,v-b,b,b) # NW
        self.drawBlock(drawer,Vec2(x+xs,y+ys),Vec2(b,b),u+us,v+vs,b,b) # SE 
        self.drawBlock(drawer,Vec2(x-b,y+ys),Vec2(b,b),u-b,v+vs,b,b) # SW
        self.drawBlock(drawer,Vec2(x+xs,y-b),Vec2(b,b),u+us,v-b,b,b) # NW
        
    def drawBlock(self,drawer,pos,size,u,v,us,vs):
        x,y = pos[0],pos[1]
        xs,ys = size[0],size[1]
        #u,v,us,vs = self.xStart,self.yStart,self.xEnd,self.yEnd
        drawer.rectStreatch((x,y,xs,ys),(u,v,us,vs))
    
class Tiled:
    
    def __init__(self,xStart,yStart,xEnd,yEnd):
        self.xStart,self.yStart,self.xEnd,self.yEnd = xStart,yStart,xEnd,yEnd

    def draw(self,drawer,pos,size):
        x,y = pos[0],pos[1]
        xs,ys = size[0],size[1]
        z = 0
        u,v,us,vs = self.xStart,self.yStart,self.xEnd,self.yEnd
        xFit = xs/us
        yFit = ys/vs
        xPos = x
        while xFit > 0:
            yPos = y
            yFit = ys/vs           
            while yFit > 0:
                fixed_us,fixed_vs = us,vs
                if xFit < 1: fixed_us = xs%us 
                if yFit < 1: fixed_vs = ys%vs
                drawer.rect((xPos,yPos,fixed_us,fixed_vs),(u,v))
                yPos += vs
                yFit -= 1
            xPos += us
            xFit -= 1
        
class TileBorder(StretchBorder):
    
    def draw(self,drawer,pos,size):
        
        u,v,us,vs = drawer.atlas.getRect(self.name) 
        b = self.border 
        
        u += b
        v += b
        us -= b*2
        vs -= b*2
        
        self.drawBlock(drawer,pos,size,u,v,us,vs) # center
        x,y = pos[0],pos[1]
        xs,ys = size[0],size[1]
        
        self.drawBlock(drawer,Vec2(x,y-b),Vec2(xs,b),u,v-b,us,b) # N
        self.drawBlock(drawer,Vec2(x,y+ys),Vec2(xs,b),u,v+vs,us,b) # S
        self.drawBlock(drawer,Vec2(x-b,y),Vec2(b,ys),u-b,v,b,vs) # W
        self.drawBlock(drawer,Vec2(x+xs,y),Vec2(b,ys),u+us,v,b,vs) # E

        self.drawBlock(drawer,Vec2(x-b,y-b),Vec2(b,b),u-b,v-b,b,b) # NW
        self.drawBlock(drawer,Vec2(x+xs,y+ys),Vec2(b,b),u+us,v+vs,b,b) # SE 
        self.drawBlock(drawer,Vec2(x-b,y+ys),Vec2(b,b),u-b,v+vs,b,b) # SW
        self.drawBlock(drawer,Vec2(x+xs,y-b),Vec2(b,b),u+us,v-b,b,b) # NW
        

    def drawBlock(self,drawer,pos,size,u,v,us,vs):
        x,y = pos[0],pos[1]
        xs,ys = size[0],size[1]
        z = 0
        xFit = xs/us
        yFit = ys/vs
        xPos = x
        while xFit > 0:
            yPos = y
            yFit = ys/vs           
            while yFit > 0:
                fixed_us,fixed_vs = us,vs
                if xFit < 1: 
                        fixed_us = xs%us 
                if yFit < 1: 
                        fixed_vs = ys%vs
                drawer.rect((xPos,yPos,fixed_us,fixed_vs),(u,v))
                yPos += vs
                yFit -= 1
            xPos += us
            xFit -= 1

class TileBarX(TileBorder):
    def draw(self,drawer,pos,size):
        u,v,us,vs,b = self.xStart,self.yStart,self.xEnd,self.yEnd,self.border
        self.drawBlock(drawer,pos,size,u,v,us,vs) # center
        x,y = pos[0],pos[1]
        xs,ys = size[0],size[1]
        self.drawBlock(drawer,Vec2(x-b,y),Vec2(b,ys),u-b,v,b,vs) # W
        self.drawBlock(drawer,Vec2(x+xs,y),Vec2(b,ys),u+us+b,v,b,vs) # E


class TreeGUIFontInvalid(Exception):
    pass

class Font:
    
    def __init__(self, name, filename, size=12, color=(1,1,1)):
        
        self.name = name
        
        self.filename = filename
        self.size = size
        self.color = color        
        self.isFont = True

    def __str__(self):
        return "Font: %s: size:%i color:%s"%(self.filename,self.size,str(self.color)) 

class TreeGUIThemeClassMustDefine(Exception):
    pass

class Theme(object):
    
    STRICT = False
    
    RAW_DIR = None
    TEXTURE = None
    ATLAS   = None
    
    DEFAULT = None
    DEFAULT_FONT = None
    
    MIN_DEFINES = [
        "frame","label","button","button_over","button_down",
        "entry","textbox","pane","form"        
        ]

    LABEL = None 

    def __init__(self):
        
        self.name = self.__class__.__name__
        
        self.fonts = []
        
        if self.RAW_DIR:
            if self.needRegen():
                self.regen()


        if self.DEFAULT == None:
            raise TreeGUIThemeClassMustDefine(
                "DEFAULT in theme must not be None")
                
        if self.DEFAULT_FONT == None:                
            raise TreeGUIThemeClassMustDefine(
                "DEFAULT_FONT in theme must not be None")
                
        if self.STRICT:
            for define in self.MIN_DEFINES:
                if None == self.define(define):
                    raise TreeGUIThemeClassMustDefine(define.upper())
    
    def needRegen(self):
        """ need to regenerate? """
        eam = eggatlas.EggAtlasMaker(self.name)
        hash = eam.doHash(self.RAW_DIR)
        tmp = ConfigVariableFilename("model-cache-dir").getStringValue()
        self.ATLAS = tmp+"/"+self.name+".atlas.egg"
        self.TEXTURE = tmp+"/"+self.name+".atlas.png"
        if not os.path.exists(self.ATLAS): return True
        if not os.path.exists(self.TEXTURE): return True        
        return hash not in open(self.ATLAS).read()
        
    def regen(self):
        print """ regenerating the atlas ..."""
        tmp = ConfigVariableFilename("model-cache-dir").getStringValue()
        eam = eggatlas.EggAtlasMaker(tmp+self.name)
        hash = eam.doHash(self.RAW_DIR)
        eam.comment = hash
        eam.doFolders(self.RAW_DIR)
        
        fontNames = [e for e in dir(self) if "FONT" in e.upper()]
        self.fonts = set([self.defineFont(name) for name in fontNames])
        eam.doFonts(self.fonts,self.RAW_DIR) 
        eam.generate()
    
    def define(self,name):
        name = name.upper()
        try:
            return self.__getattribute__(name)
        except:  
            return self.__getattribute__("DEFAULT")
        
    def defineFont(self,name):
        name = name.upper()
        try:
            e =  self.__getattribute__(name)
            try: e.isFont
            except: raise TreeGUIFontInvalid(e)
            return e
        except:  
            e =  self.__getattribute__("DEFAULT_FONT")
            try: e.isFont
            except: raise TreeGUIFontInvalid(e)
            return e
        
    
    
