from treegui.theme import *

class RTheme(Theme):

    RAW_DIR = "rtheme"
    
    DEFAULT = StretchBorder("rtheme/frame.png",4)
    
    CHECKON = IconLike("rtheme/twotone/checkmark.png")
    CHECKOFF = IconLike("rtheme/twotone/blank.png")
    
    RADIOON = IconLike("rtheme/twotone/radio-on.png")
    RADIOOFF = IconLike("rtheme/twotone/radio-off.png") 
    
    BAR_TOP = StretchBorder("rtheme/progress-top.png",4)
    
    SCROLL_Y = StretchBorder("rtheme/scrolly.png",2)
    SCROLL_X = StretchBorder("rtheme/scrollx.png",2)
    SCROLLER = StretchBorder("rtheme/progress-top.png",2)
    
    
    BUTTON = StretchBorder("rtheme/button-up.png",4)
    BUTTON_OVER = StretchBorder("rtheme/button-over.png",4)
    BUTTON_DOWN = StretchBorder("rtheme/button-donw.png",4)


    BLACK_FIX_SMALL_FONT = Font(
        "BLACK_FIX_SMALL_FONT",
        "rtheme/fonts/ProFontWindows.ttf",
        8,
        (0,0,0,1))
    
    BLACK_SCIFI_SMALL_FONT = Font(
        "BLACK_SCIFI_SMALL_FONT",
        "rtheme/fonts/kimberle.ttf",
        8,
        (0,0,0,1))


    BLACK_FIX_FONT = Font(
        "BLACK_FIX_FONT",
        "rtheme/fonts/ProFontWindows.ttf",
        10,
        (0,0,0,1))
    
    BLACK_SCIFI_FONT = Font(
        "BLACK_SCIFI_FONT",
        "rtheme/fonts/kimberle.ttf",
        10,
        (0,0,0,1))
    
    BLACK_FIX_BIG_FONT = Font(
        "BLACK_FIX_BIG_FONT",
        "rtheme/fonts/ProFontWindows.ttf",
        14,
        (0,0,0,1))
    
    BLACK_SCIFI_BIG_FONT = Font(
        "BLACK_SCIFI_BIG_FONT",
        "rtheme/fonts/kimberle.ttf",
        14,
        (0,0,0,1))

    DEFAULT_FONT = BLACK_FIX_FONT
    