#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Planet - A game
#Copyright (C) 2009 Clerc Mathias
#See the license file in the docs folder for more details

from standard import Bulbe as std
import general


class Bulbe(std):
  _classe_ = "vehicule"
  sprite = None
  
  attaquants = None
  
  def __init__(self, sprite):
    std.__init__(self, sprite)
    
  def ennui(self):
    return False
    