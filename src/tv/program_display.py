#!/usr/bin/env python
#-----------------------------------------------------------------------
# ProgramDisplay - Information and actions for TvPrograms.
#-----------------------------------------------------------------------
# $Id$
#
# Todo: 
# Notes: 
#
#-----------------------------------------------------------------------
# $Log$
# Revision 1.11  2003/09/06 17:31:17  rshortt
# Removed 'Description: ' and added a close button.
#
# Revision 1.10  2003/09/05 02:48:12  rshortt
# Removing src/tv and src/www from PYTHONPATH in the freevo script.  Therefore any module that was imported from src/tv/ or src/www that didn't have a leading 'tv.' or 'www.' needed it added.  Also moved tv/tv.py to tv/tvmenu.py to avoid namespace conflicts.
#
# Revision 1.9  2003/09/01 19:46:02  dischi
# add menuw to eventhandler, it may be needed
#
# Revision 1.8  2003/08/23 12:51:43  dischi
# removed some old CVS log messages
#
#
#-----------------------------------------------------------------------
#
# Freevo - A Home Theater PC framework
#
# Copyright (C) 2002 Krister Lagerstrom, et al.
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
# ----------------------------------------------------------------------

import time

import config, tv.edit_favorite, tv.tv_util
import tv.record_client as record_client
import tv.view_favorites, tv.program_search
import event as em

from gui.GUIObject import *
from gui.Border    import *
from gui.Label     import *
from gui.ListBox   import *
from gui.AlertBox  import *

DEBUG = 1


class ProgramDisplay(PopupBox):
    """
    prog      the program to record
    context   guide or recording
    left      x coordinate. Integer
    top       y coordinate. Integer
    width     Integer
    height    Integer
    """
    
    def __init__(self, parent=None, prog=None, context=None, left=None, 
                 top=None, width=600, height=250, vertical_expansion=1):

        self.left = left
        self.top = top
        self.prog = prog
        self.font = None

        if context:
            self.context = context
        else:
            self.context = 'guide'

        PopupBox.__init__(self, text=self.prog.title, left=left, top=top, width=width, 
                          height=height, vertical_expansion=vertical_expansion)

        self.v_spacing = 15
        self.h_margin = 20
        self.v_margin = 20

        self.internal_h_align = Align.LEFT

        if self.prog.sub_title:
            subtitle_txt = 'Subtitle:  %s' % self.prog.sub_title
            subtitle = Label(subtitle_txt, self, Align.LEFT)

        # desc = Label('Description:  %s' % self.prog.desc, self, Align.LEFT)
        desc = Label(self.prog.desc, self, Align.LEFT)

        chan = Label('Channel:  %s' % \
                      tv.tv_util.get_chan_displayname(self.prog.channel_id), 
                                                   self, Align.LEFT)

        start = Label('Start:  %s' % time.strftime('%A %b %d %I:%M %p', 
                                      time.localtime(self.prog.start)),
                                      self, Align.LEFT)

        stop = Label('Stop:  %s' % time.strftime('%A %b %d %I:%M %p', 
                                     time.localtime(self.prog.stop)), 
                                     self, Align.LEFT)
        items_height = 40

        if self.context == 'guide':
            # num_items = 3
            num_items = 2
        else:
            num_items = 2

        self.options = ListBox(width=(self.width-2*self.h_margin), 
                               height=items_height*num_items, 
                               show_v_scrollbar=0)
        self.options.items_height = items_height

        if self.context == 'guide':
            self.options.add_item(text='Record this episode', value=1)
            # self.options.add_item(text='Search for more of this program', value=2)
            # self.options.add_item(text='Add "%s" to favorites' % prog.title, value=3)
        else:
            self.options.add_item(text='Remove from scheduled recordings', value=4)

        self.options.add_item(text='Close', value=-1)

        self.options.set_h_align(Align.CENTER)
        self.options.toggle_selected_index(0)
        self.add_child(self.options)


    def eventhandler(self, event, menuw=None):
        if DEBUG: print 'ProgramDisplay: event = %s' % event

        trapped = em.MENU_EVENTS.values()

        #if event in trapped:
        #    return
        if event in (em.INPUT_UP, em.INPUT_DOWN, em.INPUT_LEFT, em.INPUT_RIGHT):
            if DEBUG: print 'ProgramDisplay: should scroll'
            return self.options.eventhandler(event)

        elif event == em.INPUT_ENTER:
            if self.options.get_selected_item().value == -1:
                self.destroy()
            elif self.options.get_selected_item().value == 1:
                (result, msg) = record_client.scheduleRecording(self.prog)
                if result:
                    AlertBox(parent=self, 
                             text='%s has been scheduled for recording' % \
                              self.prog.title, handler=self.destroy).show()
                else:
                    AlertBox(parent=self, 
                             text='Scheduling Failed: %s' % msg).show()
            elif self.options.get_selected_item().value == 2:
                tv.program_search.ProgramSearch(parent=self, 
                                             search=self.prog.title).show()
            elif self.options.get_selected_item().value == 3:
                tv.edit_favorite.EditFavorite(parent=self, 
                                           subject=self.prog).show()
            elif self.options.get_selected_item().value == 4:
                (result, msg) = record_client.removeScheduledRecording(self.prog)
                if result:
                    AlertBox(parent=self, 
                             text='%s has been removed' % \
                              self.prog.title, handler=self.destroy).show()
                else:
                    AlertBox(parent=self, 
                             text='Remove Failed: %s' % msg).show()

        elif event == em.INPUT_EXIT:
            self.destroy()
        else:
            return self.parent.eventhandler(event)



class ScheduledRecordings(PopupBox):
    """
    left      x coordinate. Integer
    top       y coordinate. Integer
    width     Integer
    height    Integer
    text      String to print.
    handler   Function to call after pressing ENTER.
    bg_color  Background color (Color)
    fg_color  Foreground color (Color)
    icon      icon
    border    Border
    bd_color  Border color (Color)
    bd_width  Border width Integer
    """

        
    def __init__(self, parent='osd', text=None, handler=None, 
                 left=None, top=None, width=600, height=300, bg_color=None, 
                 fg_color=None, icon=None, border=None, bd_color=None, 
                 bd_width=None, vertical_expansion=1):

        if not text:
            text = 'Scheduled Recordings'
        
        PopupBox.__init__(self, parent, text, handler, left, top, width, height, 
                          bg_color, fg_color, icon, border, bd_color, bd_width,
                          vertical_expansion)


        (self.result, recordings) = record_client.getScheduledRecordings()
        if self.result:
            progs = recordings.getProgramList()
        else:
            errormsg = Label('Get recordings failed: %s' % recordings, 
                             self, Align.CENTER)
            return 

        self.internal_h_align = Align.CENTER

        items_height = 40
        self.num_shown_items = 7
        self.results = ListBox(width=(self.width-2*self.h_margin),
                               height=self.num_shown_items*items_height,
                               show_v_scrollbar=0)
        self.results.y_scroll_interval = self.results.items_height = items_height
        max_results = 10

        self.results.set_h_align(Align.CENTER)
        self.add_child(self.results)


        if self.result:
            i = 0
            self.results.items = []

            if len(progs) > self.num_shown_items:
                self.results.show_v_scrollbar = 1
            else:
                self.results.show_v_scrollbar = 0

            f = lambda a, b: cmp(a.start, b.start)
            progs = progs.values()
            progs.sort(f)
            for prog in progs:
                i += 1
                self.results.add_item(text='%s %s: %s' % \
                                        (time.strftime('%b %d %I:%M %p',
                                           time.localtime(prog.start)),
                                         tv.tv_util.get_chan_displayname(prog.channel_id),
                                         prog.title),
                                      value=prog)

            space_left = self.num_shown_items - i
            if space_left > 0:
                for i in range(space_left):
                    self.results.add_item(text=' ', value=0)

            self.results.toggle_selected_index(0)


    def eventhandler(self, event, menuw=None):
        if not self.result:
            self.destroy()
            return

        if event in (em.INPUT_UP, em.INPUT_DOWN, em.INPUT_LEFT, em.INPUT_RIGHT):
            return self.results.eventhandler(event)
        elif event == em.INPUT_ENTER:
            ProgramDisplay(prog=self.results.get_selected_item().value,
                           context='recording').show()
            return
        elif event == em.INPUT_EXIT:
            self.destroy()
        else:
            return self.parent.eventhandler(event)


