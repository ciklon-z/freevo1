#if 0 /*
# -----------------------------------------------------------------------
# OptionBox.py - A drop-down box.
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.1  2003/02/24 11:58:28  rshortt
# Adding OptionBox and optiondemo.  Also some minor cleaning in a few other
# objects.
#
#
# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2003 Krister Lagerstrom, et al.
# Please see the file freevo/Docs/CREDITS for a complete list of authors.
#   
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#                
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# ----------------------------------------------------------------------- */
#endif

import pygame
import config

from GUIObject import *
from ListBox   import *
from Color     import *
from Border    import *
from Label     import * 
from types     import * 
from osd import Font

DEBUG = 1


class OptionBox(GUIObject):
    """
    left      x coordinate. Integer
    top       y coordinate. Integer
    width     Integer
    height    Integer
    text      Letter to hold.
    bg_color  Background color (Color)
    fg_color  Foreground color (Color)
    selected_bg_color  Background color (Color)
    selected_fg_color  Foreground color (Color)
    border    Border
    bd_color  Border color (Color)
    bd_width  Border width Integer

    """

    
    def __init__(self, text=" ", left=None, top=None, width=None, height=None, 
                 bg_color=None, fg_color=None, selected_bg_color=None,
                 selected_fg_color=None, border=None, bd_color=None, 
                 bd_width=None):

        GUIObject.__init__(self)

        self.text           = text
        self.border         = border
        self.h_margin       = 6
        self.v_margin       = 2
        self.bd_color       = bd_color
        self.bd_width       = bd_width
        self.width          = width
        self.height         = height
        self.left           = left
        self.top            = top
        self.bg_color       = bg_color
        self.fg_color       = fg_color
        self.label          = None
        self.selected_bg_color = selected_bg_color
        self.selected_fg_color = selected_fg_color


        # XXX: Place a call to the skin object here then set the defaults
        #      acodringly. self.skin is set in the superclass.

        if not self.width:    self.width  = 75
        if not self.height:   self.height = 25
        if not self.left:     self.left   = -100
        if not self.top:      self.top    = -100
        if not self.bg_color: self.bg_color = Color(self.osd.default_bg_color)
        if not self.fg_color: self.fg_color = Color(self.osd.default_fg_color)
        if not self.selected_fg_color: self.selected_fg_color = self.fg_color
        if not self.selected_bg_color: self.selected_bg_color = Color((0,255,0,128))
        if not self.bd_color: self.bd_color = Color(self.osd.default_fg_color) 
        if not self.bd_width: self.bd_width = 2
        if not self.border:   self.border = Border(self, Border.BORDER_FLAT, 
                                                   self.bd_color, self.bd_width)


        if type(text) is StringType:
            if text: self.set_text(text)
        elif not text:
            self.text = None
        else:
            raise TypeError, text

        self.max_visible = 5
        self.list = ListBox(left=self.left, top=self.top+self.height, 
                            width=self.width, height=75)
        self.add_child(self.list)
        self.list.visible = 0


    def change_item(self, direction):
        self.list.scroll(direction)

        if self.list.get_selected_index() >= 0:
            self.set_text(self.list.get_selected_item().text)

        self._draw()
        

    def add_item(self, text, value=None):
        self.list.add_item(None, text, value)


    def toggle_selected_index(self, i):
        if self.list:
            self.list.toggle_selected_index(i)


    def toggle_box(self):
        if self.list.is_visible():
            self.list.visible = 0
            self.selected = 1
        else:
            self.list.visible = 1
            self.selected = 0

        self._draw()
 

    def _draw(self):
        """
        The actual internal draw function.

        """
        if not self.width or not self.height or not self.text:
            raise TypeError, 'Not all needed variables set.'

        if self.selected:
            c = self.selected_bg_color.get_color_sdl()
            a = self.selected_bg_color.get_alpha()
        else:
            c = self.bg_color.get_color_sdl()
            a = self.bg_color.get_alpha()

        box = pygame.Surface(self.get_size(), 0, 32)
        box.fill(c)
        box.set_alpha(a)

        # pygame.draw.polygon(self.surface, (64, 64, 64), [(50,5),(65,5),(58,20)])
        ar_1 = (self.width-18, 5)
        ar_2 = (self.width-8, 5)
        ar_3 = (self.width-13, 20)
        pygame.draw.polygon(box, (64, 64, 64), [ar_1, ar_2, ar_3])

        self.osd.screen.blit(box, self.get_position())

        if self.border: self.border._draw()
        if self.list: 
            self.list._draw()
        if self.label:  self.label._draw()

    
    def get_text(self):
        return self.text

        
    def set_text(self, text):

        if DEBUG: print "Text: ", text
        if type(text) is StringType:
            self.text = text
        else:
            raise TypeError, type(text)

        if not self.label:
            self.label = Label(text)
            self.label.set_parent(self)
            # These values can also be maipulated by the user through
            # get_font and set_font functions.
            self.label.set_font( config.OSD_DEFAULT_FONTNAME,
                                 config.OSD_DEFAULT_FONTSIZE )
            # XXX Set the background color to none so it is transparent.
            self.label.set_background_color(None)
            self.label.set_h_margin(self.h_margin)
            self.label.set_v_margin(self.v_margin)
            self.label.set_v_align(Align.MIDDLE)
            self.label.set_h_align(Align.LEFT)
        else:
            self.label.set_text(text)



    def get_font(self):
        """
        Does not return OSD.Font object, but the filename and size as list.
        """
        return (self.label.font.filename, self.label.font.ptsize)


    def set_font(self, file, size):
        """
        Set the font.

        Just hands the info down to the label. Might raise an exception.
        """
        if self.label:
            self.label.set_font(file, size)
        else:
            raise TypeError, file


    def set_border(self, bs):
        """
        bs  Border style to create.
        
        Set which style to draw border around object in. If bs is 'None'
        no border is drawn.
        
        Default is to have no border.
        """
        if isinstance(self.border, Border):
            self.border.set_style(bs)
        elif not bs:
            self.border = None
        else:
            self.border = Border(self, bs)
            

    def set_position(self, left, top):
        """
        Overrides the original in GUIBorder to update the border as well.
        """
        GUIObject.set_position(self, left, top)
        if isinstance(self.border, Border):
            if DEBUG: print "updating borders set_postion as well"
            self.border.set_position(left, top)
        if isinstance(self.label, Label):
            self.label.set_position(self.label.calc_position())
        if isinstance(self.list, ListBox):
            self.list.set_position(self.left, self.top+self.height)

        

    def _erase(self):
        """
        Erasing us from the canvas without deleting the object.
        """

        if DEBUG: print "  Inside PopupBox._erase..."
        # Only update the part of screen we're at.
        self.osd.screen.blit(self.bg_image, self.get_position(),
                        self.get_rect())
        
        if self.border:
            if DEBUG: print "    Has border, doing border erase."
            self.border._erase()

        if DEBUG: print "    ...", self


