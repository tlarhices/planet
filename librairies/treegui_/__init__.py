"""

    TreeGUI philosophy
    
    * mash all the ui textures you have into a single texture
    * draw the entire ui as a single vertex buffer
    
    This gives is speed.  The game already uses many vertex buffers
    the ui geometry is not that huge.  It does not need to burden the 
    graphics card with many vertex buffers.  
    
    Drawing everything in one vertex buffer is also much simpler towards 
    sorting (we just draw in right order) and clipping (we just use simple 
    geometry level clipping)
    
    The system does not use any of panda3d ui or text stuff to render or 
    process the gui objects on screen.  Panda3d architecture uses too many
    vertex buffers that are needed for the acctual game itself.  Panda3d
    directGui and PGUi has no notion of layout and theme.
    

"""