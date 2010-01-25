from pandac.PandaModules import * 
from keys import Keys
from theme import Theme
from layout import Layout
from drawer import Drawer


class NotImplemted(Exception):
    """ feature is not implemetned yet """

def inBounds(v,a,b):
    if v < a: v = a
    if v > b: v = b
    return v

def task(fun,p=-100):
    """ easy wrapper to create a task quickly """
    def fn(task):
        fun()
        return task.cont
    taskMgr.add(fn,str(fun),p)
    

class Holder:
    """ 
        ui component that itself should be inviable but 
        holds other other widgets.
        
        The gui system itself is instance of the holder 
    
    """
    
    def add(self, child):
        """ adds a ui component to the children list """
        child.onAdd()
        if child.parent:
            child.parent.remove(child)
        self.children.insert(0,child)
        child.parent = self
        if child.id:
            gui.idToFrame[child.id] = child
        return child
    
    def toFront(self,thing):
        """ move the current thing to from """
        self.children.remove(thing)
        self.children.insert(0,thing)
        
    def remove(self, child):
        """ removes a ui component"""
        child.parent = None
        child.onRemove()
        self.children.remove(child)
        return child

    def clear(self):
        """ removes all ui components """
        for child in list(self.children):            
            self.remove(child)
            
    def sendToFront(self,child):
        """ move the current ui component before all others """
        self.children.remove(child)
        self.children.append(child)
    
    def sendToBack(self,child):
        """ sends the current ui component to the background"""
        self.children.remove(child)
        self.children = [child] + self.children

    def mouseEvent(self,key,x,y):
        """ sends a low level mouse event down to the children """
        for child in self.children:
            ex = child.clickExpand
            if (child.visable and 
                child._x-ex < x < child._x+ex + child._width and
                child._y-ex < y < child._y+ex + child._height):
                # the mouse click originated inside the region
                if child.mouseEvent(key,x-child._x,y-child._y):
                    # one of the children was hit
                    return True
                else:
                    gui.innerX,gui.innerY = x-child._x,y-child._y
                    # none of the children got clicked
                    # will use event our self
                    if key == "mouse1" and child.onClick:
                        child.onClick()
                        return True
                    if key == "mouse3" and child.onContext:
                        child.onContext()
                        return True
                    if key == "hover":
                        if child.onHover:
                            child.onHover()
                        if gui.hoveringOver != child:
                            if child.onIn:
                                child.onIn()
                            if gui.hoveringOver and gui.hoveringOver.onOut:
                                gui.hoveringOver.onOut()
                            gui.hoveringOver = child
                        return True
                   


        # disable all focus
        if key != "hover":
            gui.keys.focus = None
        return False

class Gui(Holder):
    """ 
        core of the treegui system 
        handles most of the events 
        prods other ui system such as
        layout and drawing into doing
        stuff
    """

    def __init__(self,keys=None,theme=None):
        """ initilizes the gui """
        
        import __builtin__
        __builtin__.gui = self
       
        self.node = aspect2d
        
        self.id = "root"
                
        self.dragWidget = None
        self.dragPos = Vec2(0,0)
        self.dragFun = None
        self.dragSnap = False
        self.lastDragMoue = Vec2(0,0)           
        self.hoveringOver = None
        
        self.parent = False
        self.children = []
        self.idToFrame = {}
        
        self.pos = Vec2(0,0)
        self.windowsize = 800,600
        self.size = Vec2(*self.windowsize)
        
        self.mouse = Vec2(0,0) 
        self.node.setBin("fixed",2)
        self.node.setDepthWrite(False)
        self.node.setDepthTest(False)

        if not keys:
            self.keys = Keys()
        else:
            self.keys = keys
            
        if not theme:
            self.theme = Theme()
        else:
            self.theme = theme
        self.layout = Layout()
        self.drawer = Drawer()
        
        task(self._doMouse,-10)
        
        self._reSize()
        
        task(self._doDrag,10)        
        task(self._reSize,20)        
        task(self._layout,30)
        task(self._draw,40)
    
    def byId(self,name):
        if name in self.idToFrame:
            return self.idToFrame[name]
      
    def _layout(self):
        """ prods layout to do its thing """
        # compute children's real positions
        self.layout.do()
        
    def _draw(self):
        """ prods drawer to do its thing """
        self.drawer.draw(self.children)
    
    def _reSize(self):
        """ resize the window via panda3d internal events"""
        self.windowsize = base.win.getXSize(),base.win.getYSize()
        self.size = Vec2(*self.windowsize)
        self.aspect  = float(self.windowsize[0]) / float(self.windowsize[1])         
        self.node.setScale(2./base.win.getXSize(), 1, -2./base.win.getYSize())
        self.node.setPos(-1, 0, 1)
        self.node.reparentTo(render2d)    
        self._x = 0
        self._y = 0
        self._width = self.size[0]
        self._height = self.size[1]
        
    
    def baseMouseEvent(self,key):
        """ acts like user clicked mouse with key """
        md = base.win.getPointer( 0 )
        self.mouseX = md.getX()
        self.mouseY = md.getY()
        m = self.mouseEvent(key,self.mouseX,self.mouseY)        
        return m
          
    def _doMouse(self):
        """ treegui's low level mouse interface """ 
        used = self.baseMouseEvent("hover")
        if not used:
            if gui.hoveringOver and gui.hoveringOver.onOut:
                gui.hoveringOver.onOut()
            gui.hoveringOver = None
        
        
    def drag(self,widget,dragSnap=False):
        """ drags a widget """ 
        if not self.dragWidget :
            self.dragWidget = widget
            self.dragSnap = dragSnap
            self.dragPosX = widget._x-gui.mouseX
            self.dragPosY = widget._y-gui.mouseY
            widget.parent.toFront(widget)
    
    def _doDrag(self):
        """ task that does dragging at low level """
        if self.dragWidget:
            self.dragWidget.x = self.dragPosX+gui.mouseX           
            self.dragWidget.y = self.dragPosY+gui.mouseY

            if self.dragWidget.onDrag:
                self.dragWidget.onDrag()

            if self.dragSnap:
                def close(a,b):
                    return abs(a-b) < 15
        
                if close(self.dragWidget.x,0): 
                    self.dragWidget.x = "left"
                     
                elif close(
                    self.dragWidget.x + self.dragWidget._width,
                    self.dragWidget.parent._width): 
                        self.dragWidget.x = "right"
        
                if close(self.dragWidget.y,0): 
                    self.dragWidget.y = "top"
                    
                elif close(
                    self.dragWidget.y + self.dragWidget._height,
                    self.dragWidget.parent._height): 
                        self.dragWidget.y = "bottom"
                
    def focusOn(self,focus):
        if self.keys.focus:
            self.keys.focus.onUnFocus()
        focus.onFocus()
        self.keys.focus = focus
        return focus
    
    def focusNext(self,focus):

        i = focus.parent.children.index(focus)
        i -= 1   
        if i == -1 : i = len(focus.parent.children) - 1
        newFocus = focus.parent.children[i]
        
        while not newFocus.control and newFocus != focus:
            i = newFocus.parent.children.index(newFocus)
            i -= 1   
            if i == -1 : i = len(focus.parent.children) - 1
            newFocus = focus.parent.children[i]
            print "new",newFocus
    
        return self.focusOn(newFocus)        
                
    def toggle(self):
        if self.node.isHidden():
            self.node.show()
        else:
            self.node.hide()      
