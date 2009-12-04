from treegui.theme import *

class Theme(Theme):

    RAW_DIR = "theme"
    
    DEFAULT = StretchBorder("theme/frame.png",4)
    
    CHECKON = IconLike("theme/icones/checkmark.png")
    CHECKOFF = IconLike("theme/icones/blank.png")
    
    RADIOON = IconLike("theme/icones/radio-on.png")
    RADIOOFF = IconLike("theme/icones/radio-off.png") 
    
    BAR_TOP = StretchBorder("theme/progress-top.png",4)
    
    SCROLL_Y = StretchBorder("theme/scrolly.png",2)
    SCROLL_X = StretchBorder("theme/scrollx.png",2)
    SCROLLER = StretchBorder("theme/progress-top.png",2)
    
    
    BUTTON = StretchBorder("theme/button-up.png",4)
    BUTTON_OVER = StretchBorder("theme/button-over.png",4)
    BUTTON_DOWN = StretchBorder("theme/button-donw.png",4)


    BLACK_FIX_SMALL_FONT = Font(
        "BLACK_FIX_SMALL_FONT",
        "theme/fonts/ProFontWindows.ttf",
        8,
        (0,0,0,1))
    
    BLACK_SCIFI_SMALL_FONT = Font(
        "BLACK_SCIFI_SMALL_FONT",
        "theme/fonts/kimberle.ttf",
        8,
        (0,0,0,1))


    BLACK_FIX_FONT = Font(
        "BLACK_FIX_FONT",
        "theme/fonts/ProFontWindows.ttf",
        10,
        (0,0,0,1))
    
    BLACK_SCIFI_FONT = Font(
        "BLACK_SCIFI_FONT",
        "theme/fonts/kimberle.ttf",
        10,
        (0,0,0,1))
    
    BLACK_FIX_BIG_FONT = Font(
        "BLACK_FIX_BIG_FONT",
        "theme/fonts/ProFontWindows.ttf",
        14,
        (0,0,0,1))
    
    BLACK_SCIFI_BIG_FONT = Font(
        "BLACK_SCIFI_BIG_FONT",
        "theme/fonts/kimberle.ttf",
        14,
        (0,0,0,1))

    DEFAULT_FONT = BLACK_FIX_FONT
    