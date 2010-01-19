import rectpack
from pandac.PandaModules import *

SIZE = 512

class ImageStats:
    
    name = ""
    image = None
    placed = False
    x = 0
    y = 0
    width = 0
    height = 0

class ImageTable:
    
    
    def __init__(self,x=SIZE,y=SIZE):
        self.imageStats = {}
        self.finalTexture = None
        self.finalSizeX = x
        self.finalSizeY = y
        
    def add(self,name,image):
        imageStats = ImageStats()
        imageStats.image = image
        imageStats.name = name
        self.imageStats[name] = imageStats
        
    def get(self,name):
        return self.imageStats[name].image
    
    def uv(self,name):
        stat = self.imageStats[name]
        if stat.placed:
            return (
                Vec2(stat.x,stat.y),
                Vec2(stat.x,stat.y) + 
                Vec2(stat.image.getXSize(),stat.image.getYSize()))                
        return (Vec2(0,0),Vec2(0,0))
        
    def remove(self,name):
        del self.imageStats[name]
        
    def pack(self):
        
        rp = rectpack.CygonRectanglePacker(
            self.finalSizeX,
            self.finalSizeY)
        
        statList = self.imageStats.values()
        statList.sort(key = 
            lambda stat: stat.image.getXSize() * stat.image.getYSize())
        
        for stat in statList:
            p = rp.TryPack(
                stat.image.getXSize(),
                stat.image.getYSize())
            if p:
                stat.x = p.x
                stat.y = p.y
                stat.width = stat.image.getXSize()
                stat.height = stat.image.getYSize()
                stat.placed = True
            else:
                print "error",(
                    stat.image.getXSize(),
                    stat.image.getYSize())
                
                
    def vertualHash(self):
        return hash(",".join(map(str,self.imageStats.keys())))
                
    def texture(self):
        self.pack()        
        bamCache = BamCache.getGlobalPtr()
        r = bamCache.lookup('~ImageTable/%i'%self.vertualHash(), 'txo')
        if r.hasData():
            print "Cache file already exists"
            tex = r.getData()
        else:
            print "Cache file does not exist"
            tex = self.generate()
            r.setData(tex, False)
            bamCache.store(r)
        return tex
                
    def generate(self,name="final.png"):
        
        self.finalImage = PNMImage(
            self.finalSizeX,
            self.finalSizeY)
        self.finalImage.addAlpha()
        
        for stat in self.imageStats.values():
            if stat.placed:
                self.finalImage.copySubImage(
                    stat.image,
                    stat.x,
                    stat.y)
                
        self.finalImage.write(name) 
        tex = Texture()
        tex.load(self.finalImage)
        
        return tex  

                
        