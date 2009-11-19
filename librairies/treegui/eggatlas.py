"""

    this contains atlas tools 
    
"""

from pandac.PandaModules import *
import math
import os
import sha
from imagetable import ImageTable

def getAllType(eggNode,eggType):
    """ find all type in egg """
    try:
        child = eggNode.getFirstChild()
    except: 
        return
    
    while child:
        if child.__class__ == eggType: 
            yield child
            
        for subch in getAllType(child,eggType):
            yield subch
            
        child = eggNode.getNextChild()


def getAllEggGroup(eggNode):
    """ find all egg groups in egg """
    for c in getAllType(eggNode,EggGroup):
        yield c

class Image:
    """ mini data strucutre for egg atlas """
    name = ""
    x,y = 0,0
    w,h = 0,0
    extend = 0
    
    
    def __str__(self):
        return (
            "%s @(%i,%i) %ix%i >%i %i" %
            (self.name,self.x,self.y,self.w,self.h,self.extend[0],self.extend[1]))


class EggAtlas():
    """
        Egg atlas reads *.atlas.egg files
        and helps with the data that is stored in them
    """
    
    def __init__(self,filename):
        """ create atlas """
        self.images = {}
        self.chars  = {}
        self.readEgg(filename)
        
    def readEgg(self,filename):
        """ reads the egg file and stores the info"""
        egg = EggData()
        egg.read("./"+filename)
        for char in getAllEggGroup(egg):
            name = str(char.getName())
            
            image = Image()
            image.name = name
            self.images[name] = image 
            
            pos = char.getComponentVec3(0)
            
            for p in getAllType(char,EggPolygon):     
                     
                if p.getNumVertices() > 2:
                    v = p.getVertex(2)
                    vpos = v.getPos3()-pos
                    image.x = pos.getX()
                    image.y = pos.getZ()
                    image.w = vpos.getX()
                    image.h = vpos.getZ()
                    
                for l in getAllType(char,EggPoint):
                    extend = l.getVertex(0).getPos3()-pos
                    image.extend = math.ceil(extend.getX()),math.ceil(extend.getZ())
                    
            #print image

    def getRect(self,name):
        """ 
            return 4 values that correspond to the named rectangle 
        """ 
        try:       
            image = self.images[name]
            return image.x,image.y,image.w,image.h
        except KeyError:
            print "can't find",name,"in:",self.images.keys()
            return None
    
    def getChar(self,name):
        """
            return 4 values that correspond to the named rectangle
            and the extend the for the char
        """
        image = self.images[name]
        return image.x,image.y,image.w,image.h,image.extend
    

def walkdir(dir):
    """ walks a dir and returns file names """
    for path, dirs, files in os.walk(dir):
        for file in files:
            yield  path+"/"+file


def getAllType(eggNode,eggType):
    """ find all type in egg """
    try:
        child = eggNode.getFirstChild()
    except: 
        return
    
    while child:
        if child.__class__ == eggType: 
            yield child
            
        for subch in getAllType(child,eggType):
            yield subch
            
        child = eggNode.getNextChild()


def getAllEggGroup(eggNode):
    """ find all egg groups in egg """
    for c in getAllType(eggNode,EggGroup):
        yield c

def takeFile(file):
    """ return only filename from random path """
    i = max(file.rfind("/"))
    if i != -1:        
        return file[i+1:]
    return file

class EggAtlasMaker():
    """ 
        Egg Atlas is a *.atlas.egg file desing to be 
        using with many 2d billboard or ui components
            
    """
    
    def __init__(self,name,size=2048):
        """ 
            name - that atlas will come with
            size - the texture size x size the atlas will use
        """
        self.name = name
        self.comment = None
        self.extents = {}
        self.size = float(size)
        self.it = ImageTable(int(self.size),int(self.size))
        self.files = []

#    def doFont(self,f):
#        """ records the image extents in font """
#        
#        letters = {}
#        
#        print "font",f
#        
#        eggFont = EggData()
#        eggFont.read(f)
#        for char in getAllEggGroup(eggFont):
#            for p in getAllType(char,EggPolygon):
#                   
#                name = str(p.getTexture().getName())
#                texture = str(p.getTexture().getFilename())
#                
#                print name,texture
#                
#                if p.getNumVertices() > 0:
#                    uv1 = p.getVertex(0).getUv()
#                    uv2 = p.getVertex(2).getUv()
#                    print "  uv", uv1,uv2
#                           
#                    for l in getAllType(char,EggPoint):
#                        v1 = p.getVertex(0).getPos3()
#                        v2 = p.getVertex(2).getPos3()
#                        print " pos",v1,v2
#                        
#                        extendVec = l.getVertex(0).getPos3()
#                        print "  >", extendVec
#                        print "  =", extendVec
#                    
#                letters[name] = (uv1,uv2,extendVec)
#        self.fonts[texture] = letters
#        

    def doFonts(self,fonts):
        for font in fonts:
            print "doing font:",font
            self.doFont(font)

    def doFont(self,fontdef):
        
        color = Vec4(0,0,0,1)
        color.setX(fontdef.color[0])
        color.setZ(fontdef.color[1])
        color.setY(fontdef.color[2])
            
        size = fontdef.size
        
        name = fontdef.name
        
        PADDING = 0
        
        open(fontdef.filename)
        
        font = PNMTextMaker(fontdef.filename,0)
        font.setPixelsPerUnit(size)
        font.setPointSize(size)
        font.setAlign(font.ALeft)
        font.setNativeAntialias(False)
        font.setScaleFactor(16)
        
        tmp = ConfigVariableFilename("model-cache-dir").getStringValue()
         
        for i in range(32,128):
            char = chr(i)
            charName = name+str(i)
            #print i,charName,"'%s'"%char
            glyph = font.getGlyph(i)
            w,h = glyph.getWidth(),glyph.getBottom()-glyph.getTop()
            image = PNMImage(w+PADDING*2,h+PADDING*2)
            image.addAlpha()
            image.alphaFill()
            #print "  ",w,h
            
#            print glyph.getLeft(),glyph.getRight()
#            print glyph.getTop(),glyph.getBottom()
#            print glyph.getAdvance()
            
            glyph.place(image,PADDING,glyph.getTop()+PADDING,color)
            #image.write(tmp+"/%i.png"%i)
            self.extents[charName] = (
                glyph.getAdvance(),
                glyph.getBottom()-2*glyph.getTop())
            
            self.it.add(charName,image)

    def doImage(self,f):
        """ process an iamge and put it into the atlas """ 
        print "Doing image:",f
        i = PNMImage(f)
        i.addAlpha()
        self.it.add(f,i)
        
        
    def doHash(self,folder):
        """ 
            walk the sub folders and files in this folder 
            and get hash of their names 
        """
        files = []
        for f in walkdir(folder):
            if ".font.egg" in f or ".png" in f or ".rgb" in f:        
                files.append("%s:%f"%(f,os.stat(f).st_mtime))
        text = "\n".join(sorted(files))
        return sha.new(text).hexdigest() 
    
    def doFolders(self,folder):
        """ 
            walk the sub folders and files in this foler 
            and insert them into the atlas 
        """
        for f in sorted(walkdir(folder)):
            
#            if "ttf" in f:        
#                self.doFont(f)
#                self.files.append(f)
                
            if ".png" in f or ".rgb" in f:
                self.doImage(f)
                self.files.append(f)


    def generate(self):
        """ generate the texture and .atlas.egg file """
        self.generateTexture()
        self.generateEggAtlas()

    def generateTexture(self):
        """ generate the acctuall texture """
        self.it.pack()
        self.it.generate(self.name+".atlas.png")

    def generateEggAtlas(self):
        """ generate the egg file that represents the atlas """
        self.egg = EggData()
        if self.comment:
            self.egg.addChild(EggComment("hash",self.comment))
            
        self.egg.addChild(EggComment(
            "file listing",
            "\n".join(sorted(self.files))))
            
        self.tex = EggTexture("atlas-tex", self.name+".atlas.png")
        self.tex.setMinfilter(EggTexture.FTLinearMipmapLinear )
        self.tex.setMagfilter(EggTexture.FTNearest )
        self.egg.addChild(self.tex)
        self.pool = EggVertexPool("atlas-vex")

        self._walkOverImages()

        self.egg.addChild(self.pool)
        self.egg.writeEgg(self.name+'.atlas.egg')

    def _walkOverImages(self):
        """ walk down the images recored and put them into the atlas """ 
        for fname,uv in sorted(self.it.imageStats.iteritems(),key=lambda v:v[0]):
            #print fname
            name = fname.replace("\\","/")
            group = EggGroup(name)
            
            group.addTranslate3d(Vec3D(uv.x,0,uv.y))
            
            group.setModelFlag(True)
            poly = EggPolygon()
            poly.addTexture(self.tex)
            
            def v(x,y):
                v = EggVertex()
                v.setUv(Point2D(x/float(self.size),(self.size-y)/float(self.size)))
                v.setPos(Point3D(x,0,y))        
                self.pool.addVertex(v)
                poly.addVertex(v)
                
            v(uv.x,uv.y)
            v(uv.x+uv.width,uv.y)
            v(uv.x+uv.width,uv.y+uv.height)
            v(uv.x,uv.y+uv.height)
            group.addChild(poly)    
            
            if fname in self.extents:
                extendX,extendY = self.extents[fname]
            else:
                extendX,extendY = uv.width,uv.height
                
            point = EggPoint() 
            x,y = uv.x+uv.width,uv.y+uv.height
            v = EggVertex()
            v.setPos(Point3D(uv.x+extendX,0,uv.y+extendY))        
            self.pool.addVertex(v)
            point.addVertex(v)
            group.addChild(point)
            
            self.egg.addChild(group)

    
#EggAtlas("../egg-atlas/2aw.atlas.egg")