from treegui.theme import *

class Theme(Theme):

    RAW_DIR = "theme"
    
    DEFAULT = StretchBorder("frame.png",4)
    VIDE = StretchBorder("frame-vide.png",4)
    
    CHECKON = IconLike("icones/checkmark.png")
    CHECKOFF = IconLike("icones/blank.png")
    
    RADIOON = IconLike("icones/radio-on.png")
    RADIOOFF = IconLike("icones/radio-off.png") 
    
    BAR_TOP = StretchBorder("progress-top.png",4)
    
    SCROLL_Y = StretchBorder("scrolly.png",2)
    SCROLL_X = StretchBorder("scrollx.png",2)
    SCROLLER = StretchBorder("progress-top.png",2)
    
    
    BUTTON = StretchBorder("button-up.png",4)
    BUTTON_OVER = StretchBorder("button-over.png",4)
    BUTTON_DOWN = StretchBorder("button-donw.png",4)


    BLACK_FIX_FONT = Font(
        "BLACK_FIX_FONT",
        "fonts/ProFontWindows.ttf",
        10,
        (0,0,0,1))

    DEFAULT_FONT = BLACK_FIX_FONT
    