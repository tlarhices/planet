"""

    Components are widgets that are 
    composed of other widgets
    
    includes forms, tabs, scroll bars ...
    

"""


from widgets import *
from core import *
       
       
        
class Pane(Holder,Widget):
    """ a bordered box to hold widgets """
    
    clips = True
    
    style = "pane"
    
    def __init__(self,*args,**kargs):
        """ creates a pane """
        Widget.__init__(self,*args,**kargs)
        

class ScrollBar(Pane):
    """
        Base class use ScrollBarX or ScrollBarY
    """
    clips = False
    clickExpand = 4
    def __init__(self,*args,**kargs):
        Pane.__init__(self,*args,**kargs)
        
        class Scroller(Widget):
             """ the thing that scrolls """
             control = True    
             clickExpand = 5
        self.scroller = self.add(
            Scroller(x=0,y=0,width=10,height=10))   
        self.scroller.onClick=self.scrollerStartDrag
        self.scroller.style = "SCROLLER"
        self.scroller.onDrag = self.scrollerDrag
        
    def scrollerStartDrag(self):
        gui.drag(self.scroller)
        
    def scrollerDrag(self):
        raise NotImplemted("ScrollBar is abstract")
    
    def _compute(self,v,a,b):
        range = float(abs(a-b))
        self.value = v/range*100
        
class ScrollBarX(ScrollBar):   
    """ scrolls in X dirction """
    style = "SCROLL_X"
    def __init__(self,*args,**kargs):
        width="100%"
        height=5
        ScrollBar.__init__(self,*args,**kargs)
        self.scroller.height = self.height
   
    def scrollerDrag(self):
        self.scroller.x = inBounds(self.scroller.x,0,self._width-self.scroller.width)
        self._compute(self.scroller.x,0,self._width-self.scroller.width)
        self.value = self.scroller.x
        self.scroller.y = 0
        
        
    
class ScrollBarY(ScrollBar):   
    """ scrolls in Y dirction """
    style = "SCROLL_Y"
    def __init__(self,*args,**kargs):
        width=5
        height="100%"
        ScrollBar.__init__(self,*args,**kargs)
        self.scroller.width = self.width
        
    def scrollerDrag(self):
        self.scroller.y = inBounds(self.scroller.y,0,self._height-self.scroller.height)
        self._compute(self.scroller.y,0,self._height-self.scroller.height)
        self.value = self.scroller.y
        self.scroller.x = 0


class ScrollPane(Pane):
    """ 
        a bordered box to hold widgets 
        auto computes its internal size
        adds scrolls bars
    """
    
    clips = True
    
    style = "pane"
    
    def __init__(self,*args,**kargs):
        Pane.__init__(self,*args,**kargs)
        self.inner = self.add(Pane())
        self.inner.width=100000
        self.inner.height=100000
        self.inner.style = None
        
        self.sx = self.add(ScrollBarX(x=3,y="bottom -3",height=10,width="100% -20"))
        self.sy = self.add(ScrollBarY(y=3,x="right  -3",width=10, height="100% -20"))
        
        self.sx._compute = self.xScroll
        self.sy._compute = self.yScroll
        
        self.add = self.inner.add
        self.clear = self.inner.clear
        
    def computeBounds(self):
        x,y = 0,0
        for child in self.inner.children:
            x = max(x,child._x + child._width)
            y = max(y,child._y + child._height)
        self.bounds = x,y
        
    def xScroll(self,v,a,b):
        self.computeBounds()
        range = float(abs(a-b))
        slideRange = max(0,self.bounds[0]-self._width+100)
        self.inner.x = -slideRange*v/range
    
    def yScroll(self,v,a,b):
        self.computeBounds()
        range = float(abs(a-b))
        slideRange = max(0,self.bounds[1]-self._height+100)
        self.inner.y = -slideRange*v/range
        
    
class ProgressBar(Pane):
    """ display a string of text in the ui """
    clips = False
    style = "bar_back"
    
    class ProgressBarTop(Widget):
        style = "bar_top"

    def __init__(self, percent,**placement):
        self.doPlacement(placement)    
        self.children = []
        self.filler = self.add(self.ProgressBarTop(
            x=0,y=0,width=self.width,height=self.height))
        
        self.setProgress(percent)
        
    def setProgress(self,percent):
        self.filler.width = self.width * percent / 100
        
    def getProgress(self):
        return self.filler.width * 100 / self.width
    
class Form(Pane):
    """
        A complete window with title bar, 
        resizing, min, max and close buttons     
    """
    
    style = "form"
    
    def __init__(self):
        """ create a form """
        Pane.__init__(self)
        
        