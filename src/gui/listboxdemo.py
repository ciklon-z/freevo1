#if 0 /*
# -----------------------------------------------------------------------
# listboxdemo.py - lets demonstrate the listbox
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.1  2003/02/23 18:24:04  rshortt
# New classes.  ListBox is a subclass of RegionScroller so that it can scroll though a list of ListItems which are drawn to a surface.  Also included is a listboxdemo to demonstrate and test everything.
#
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
import config

from GUIObject      import *
from PopupBox       import *
from ListBox        import *
from ListItem       import *
from Color          import *
from Button         import *
from Border         import *
from Label          import *
from types          import *

DEBUG = 1


class listboxdemo(PopupBox):
    """
    left      x coordinate. Integer
    top       y coordinate. Integer
    width     Integer
    height    Integer
    text      String to print.
    bg_color  Background color (Color)
    fg_color  Foreground color (Color)
    icon      icon
    border    Border
    bd_color  Border color (Color)
    bd_width  Border width Integer
    """

    def __init__(self, text, icon=None, left=None, top=None, width=None, 
                 height=None, bg_color=None, fg_color=None, border=None, 
                 bd_color=None, bd_width=None):

        PopupBox.__init__(self)

        self.text     = text
        self.icon     = icon
        self.border   = border
        self.label    = None
        self.h_margin = 10
        self.v_margin = 10
        self.bd_color = bd_color
        self.bd_width = bd_width
        self.width    = width
        self.height   = height
        self.left     = left
        self.top      = top
        self.bg_color = bg_color
        self.fg_color = fg_color

        # XXX: Place a call to the skin object here then set the defaults
        #      acodringly. self.skin is set in the superclass.

        if not self.width:    self.width  = 500
        if not self.height:   self.height = 350
        if not self.left:     self.left   = self.osd.width/2 - self.width/2
        if not self.top:      self.top    = self.osd.height/2 - self.height/2
        if not self.bg_color: self.bg_color = Color(self.osd.default_bg_color)
        if not self.fg_color: self.fg_color = Color(self.osd.default_fg_color)
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
        
        if icon:
            self.set_icon(icon)

        self.set_h_align(Align.CENTER)

        self.label.top = self.top + 25

        self.pb = ListBox(left=self.left+25, top=self.top+75, width=450, height=250)
        for i in range(20):
            iname = "Item %s" % i
            self.pb.add_item(text=iname, value=i)

        self.pb.toggle_selected_index(0)
        self.add_child(self.pb)


    def eventhandler(self, event):

        scrolldirs = [self.rc.UP, self.rc.DOWN, self.rc.LEFT, self.rc.RIGHT]
        if scrolldirs.count(event) > 0:
            return self.pb.eventhandler(event)
        elif event == self.rc.ENTER or event == self.rc.SELECT or event == self.rc.EXIT:
            self.parent.refresh()
            self.destroy()
        else:
            return self.parent.eventhandler(event)


