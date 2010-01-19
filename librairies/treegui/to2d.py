from pandac.PandaModules import *

class To2D:    
    """ class that can take all the things 
        that where added to it and manipulate 
        them in 2d guish kinda way """
    
    def getGUIPos(self,node):        
        """ node -> pos on screen , -100,-100 it its not on screen"""
        pos2d = self.compute2dPosition(node,Vec3(0,0,0))
        if pos2d:
            return Point2((pos2d[0]+1)*gui.windowsize[0]/2, (-pos2d[1]+1)*gui.windowsize[1]/2)
        return Point2(-100,-100)
        
    def getThingClosestTo(self,cThings,pos,far=9999):
        try:
            cThings = cThings.values()
        except: pass
        things = []
        for thing in cThings:
            pos2d = self.compute2dPosition(thing.node,Vec3(0,0,0))
            if pos2d:
                pos2d = Vec2(
                    (pos2d[0]+1)*gui.windowsize[0]/2, 
                    (-pos2d[1]+1)*gui.windowsize[1]/2)
                distance = (pos2d-pos).length()
                #print pos2d,pos,distance,thing
                if distance < far:
                    far = distance
                    things = [thing]
        return things
                  
    def getThingInGUIRec(self,cThings,rec):
        """ is there a thing in any of the rectagle """
        try:
            cThings = cThings.values()
        except: pass
        sx,ex,sy,ey = rec      
        if sx > ex: sx,ex = ex,sx
        if sy > ey: sy,ey = ey,sy
        things = []
        for thing in cThings:
            pos2d = self.compute2dPosition(thing.node,Vec3(0,0,0))
            if pos2d:
                pos2d = Point2(
                    (pos2d[0]+1)*gui.windowsize[0]/2, 
                    (-pos2d[1]+1)*gui.windowsize[1]/2)
                x,y=pos2d[0],pos2d[1]
                if sx < x and x < ex and sy < y and y < ey :
                    things.append(thing)                    
        return things       
               
    def compute2dPosition(self,nodePath, point = Point3(0, 0, 0)):
        """ Computes a 3-d point, relative to the indicated node, into a
        2-d point as seen by the camera.  The range of the returned value
        is based on the len's current film size and film offset, which is
        (-1 .. 1) by default. """
        if base.win.hasSize():
            p3d = base.cam.getRelativePoint(nodePath, point)
            p2d = Point2()
            if base.cam.node().getLens().project(p3d, p2d):
                return p2d
        return None 