"""

    in tree gui layout are mostly spesified relative to other objects
    
    
    it uses a little langauge CSS like lanaguge to compute where the
    elements should be everyframe based on their values in plaement and
    resizing.
        
    
    widgets use CSS box like model:
        
        margin-------|
        |border-----||
        ||padding--|||
        |||        |||
        |||        |||
        |||        |||
        |||        |||
        |||--------|||
        ||----------||
        |------------|
  
        
    placement:
    
                                 above 
                                 -----
                                 at 
   
        
        before ->|<- at          center             till->|<- after 
   
                                
                                 till
                                 -----
                                 below
    
        example:
        
            placement = "100px,10px"
            placement = "center of bluebox,10px"            
            placement = "before redbox, bellow picker"
        
    sizing:
    
        grow left or right
        envelope its continaing objects
        
                        till
                        -----
        
        till ->|                      cover ->|
        
        
                        cover
                        -----    
        example:
        
            sizing = "100px,300px"
            sizing = "30%,envelope"
            sizing = "grow till redbox, cover blue_buttons"


"""

def tryfloat(f):
    f = f.replace("px","")
    try:
        return float(f)
    except:
        return 100.0


def tryInt(i):
    i = i.replace("px","")
    try:
        return int(i)
    except:
        return 0
    
class Layout:    

    def load(self,filename):
        file = open(filename)
        for line in file:
            line = line.strip()
            id,x,y,width,height,visable = line.split("|")
            if id in gui.idToFrame:
                widget = gui.idToFrame[id]
                widget.x = x
                widget.y = y
                widget.width = width
                widget.height = height
                widget.visable = visable == "True"
        
    def save(self,filename):
        file = open(filename,'w')
        for widget in gui.idToFrame.values():
            p = map(str,[
                widget.id,
                widget.x,
                widget.y,
                widget.width,
                widget.height,
                widget.visable])
            file.write("%s|%s|%s|%s|%s|%s\n"%tuple(p)) 

    def do(self):
        
        self.processed = {}
        self.processed["root"] = gui
        for child in gui.children:
            self.process(child)

        
    def processById(self,id):
        self.process(gui.idToFrame[id])
                            
    def process(self,widget):
        
        if widget.id and widget.id in self.processed:
            return widget
        else:
            self.processed[widget.id] = widget
            
                     
        if widget in self.processed:
            return widget
        else:
            self.processed[widget] = widget

        p = self.process


        
        # position pass one
        if type(widget.x) in [float,int,long]:
            x = int(widget.x)
        elif widget.x[-1] == "%":
            parentWidth = p(widget.parent)._width
            x = int(widget.x[0:-1])/100.*parentWidth
        elif widget.x == "left":
            x = 0
        else:
            x = tryfloat(widget.x)
               
        if type(widget.y) in [float,int,long]:
            y = int(widget.y)
        elif widget.y[-1] == "%":
            parentHeight = p(widget.parent)._height
            y = int(widget.y[0:-1])/100.*parentHeight
        elif widget.y == "top":
            y = 0
        else:
            y = tryfloat(widget.y)

        # size pass one
        if type(widget.width) in [float,int,long]:
            sx = widget.width
        elif widget.width[-1] == "%":
            parentWidth = p(widget.parent)._width
            sx = float(widget.width[0:-1])/100.*parentWidth - x
        elif "%" in widget.width :
            sayWidth,sayAdjustment = widget.width.split("%")
            sayWidth,sayAdjustment = tryfloat(sayWidth),tryfloat(sayAdjustment)
            parentWidth = p(widget.parent)._width
            sx = sayWidth/100.*parentWidth + sayAdjustment - x
        else:
            sx =  tryfloat(widget.width)
        
        if type(widget.height) in [float,int,long]:
            sy = widget.height
        elif widget.height[-1] == "%":
            parentHeight = p(widget.parent)._height
            sy = float(widget.height[0:-1])/100.*parentHeight - y
        elif "%" in widget.height :
            sayHeight,sayAdjustment = widget.height.split("%")
            sayHeight,sayAdjustment = tryfloat(sayHeight),tryfloat(sayAdjustment)
            parentHeight = p(widget.parent)._height
            sy = sayHeight/100.*parentHeight + sayAdjustment - y
        else:
            sy = tryfloat(widget.height)
        
       
        
        
        # position pass 2
        if widget.x == "center":
            x = p(widget.parent)._width/2 - sx/2
        elif widget.x == "right":
            x = p(widget.parent)._width - sx
        elif type(widget.x) == str:
            words = widget.x.split()
            if len(words) > 1 and words[-1] in gui.idToFrame:
                if words[-1] not in self.processed: self.processById(words[-1])
                otherFrame = gui.idToFrame[words[-1]]
                if words[0] == "left":
                    x = otherFrame._x - sx
                elif words[0] == "right":
                    x = otherFrame._x + otherFrame._width
                elif words[0] == "next":
                    x = otherFrame._x   
            if len(words) > 1 and tryInt(words[-1]):
                adjust = tryInt(words[-1])
                if words[0] == "left":
                    x = + adjust
                if words[0] == "center":
                    x = p(widget.parent)._width/2 - sx/2 + adjust
                elif words[0] == "right":
                    x = p(widget.parent)._width - sx  + adjust
                
            
        if widget.y == "center":
            y = p(widget.parent)._height/2-sy/2
        elif widget.y == "bottom":
            y = p(widget.parent)._height - sy
        elif type(widget.y) == str:
            words = widget.y.split()
            if len(words) > 1 and words[-1] in gui.idToFrame:
                if words[-1] not in self.processed: self.processById(words[-1])
                otherFrame = gui.idToFrame[words[-1]]
                if words[0] == "above":
                    y = otherFrame._y - sy
                elif words[0] == "bellow":
                    y = otherFrame._y + otherFrame._height
                elif words[0] == "next":
                    y = otherFrame._y
            if len(words) > 1 and tryInt(words[-1]):
                adjust = tryInt(words[-1])
                if words[0] == "top":
                    y =  + adjust
                if words[0] == "center":
                    y = p(widget.parent)._height/2-sy/2 + adjust
                elif words[0] == "bottom":
                    y = p(widget.parent)._height - sy + adjust
              
            
        widget._x = int(x)
        widget._y = int(y)

        widget._width = int(sx)
        widget._height = int(sy)

        if widget.children:
            for child in widget.children:
                self.process(child)
                
        return
            
        
        # size pass 2
        if type(widget.width) == str:
            words = widget.width.split()
            if words[0] == "grow" and words[-1] in self.idToFrame:
                if words[-1] not in self.processed: self.processById(words[-1])
                otherFrame = self.idToFrame[words[-1]]
                if x < otherFrame.getPos()[0]:
                    sx = otherFrame.getPos()[0] - x
                elif x < otherFrame.getPos()[0] + otherFrame.getSize()[0]:
                    sx = otherFrame.getPos()[0] + otherFrame.getSize()[0] - x
                elif x > otherFrame.getPos()[0] + otherFrame.getSize()[0]:
                    sx = x - (otherFrame.getPos()[0] + otherFrame.getSize()[0]) + sx
                    x = otherFrame.getPos()[0] + otherFrame.getSize()[0]
                    
        if type(cls._height) == str:
            words = cls._height.split()
            if words[0] == "grow" and words[-1] in self.idToFrame:
                if words[-1] not in self.processed: self.processById(words[-1])
                otherFrame = self.idToFrame[words[-1]]
                if y < otherFrame.getPos()[1]:
                    sy = otherFrame.getPos()[1] - y
                elif y < otherFrame.getPos()[1] + otherFrame.getSize()[0]:
                    sy = otherFrame.getPos()[1] + otherFrame.getSize()[0] - y
                elif y > otherFrame.getPos()[1] + otherFrame.getSize()[0]:
                    sy = y - (otherFrame.getPos()[1] + otherFrame.getSize()[0]) + sy
                    y = otherFrame.getPos()[1] + otherFrame.getSize()[0]
            
        frame.setPos(Vec2(x,y))
        frame.setSize(Vec2(sx,sy))
        
        
        
