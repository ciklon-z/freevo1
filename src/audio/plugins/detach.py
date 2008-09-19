# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# Detach plugin for the audio player
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:
#
# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002 Krister Lagerstrom, et al.
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
# -----------------------------------------------------------------------


from kaa import Timer
from kaa import EventHandler

import config
import plugin
import menu
import rc
import audio.player
from event import *
from util.benchmark import benchmark
benchmarking = config.DEBUG_BENCHMARKING
benchmarkcall = config.DEBUG_BENCHMARKCALL
benchmarking = 0
benchmarkcall = False

class PluginInterface(plugin.MainMenuPlugin):
    """
    plugin to detach the audio player to e.g. view pictures while listening
    to music
    """

    @benchmark(benchmarking, benchmarkcall)
    def __init__(self):
        _debug_('detach.PluginInterface.__init__()', 2)
        plugin.MainMenuPlugin.__init__(self)
        config.EVENTS['audio'][config.DETACH_KEY] = Event(FUNCTION_CALL, arg=self.detach)
        self.show_item = menu.MenuItem(_('Show player'), action=self.show)
        self.show_item.type = 'detached_player'
        self.event = EventHandler(self._event_handler)
        self.event.register()


    @benchmark(benchmarking, benchmarkcall)
    def config(self):
        """
        config is called automatically,
        freevo plugins -i audio.detach returns the info
        """
        return [
            ('DETACH_KEY', 'DISPLAY', 'Event to activate the detach bar, DISPLAY, ENTER, EXIT'),
        ]


    @benchmark(benchmarking, benchmarkcall)
    def detach(self):
        _debug_('detach()', 1)
        rc.post_event(plugin.event('DETACH'))
        gui = audio.player.get()

        # hide the player and show the menu
        #mplayervis = plugin.getbyname('audio.mplayervis')
        #if mplayervis:
        #    mplayervis.stop_visual()
        #    #mplayervis.detach()

        gui.hide()
        gui.menuw.show()

        # set all menuw's to None to prevent the next title to be
        # visible again
        gui.menuw = None
        gui.item.menuw = None
        if gui.item.parent:
            gui.item.parent.menuw = None


    @benchmark(benchmarking, benchmarkcall)
    def attach(self):
        _debug_('attach()', 1)
        rc.post_event(plugin.event('ATTACH'))
        # hide the player and show the menu
        #mplayervis = plugin.getbyname('audio.mplayervis')
        #if mplayervis:
        #    mplayervis.attach()
        #    mplayervis.start_visual()


    @benchmark(benchmarking, benchmarkcall)
    def _event_handler(self, event):
        _debug_('_event_handler(event=%s)' % (event,), 2)
        gui = audio.player.get()
        if gui:
            p = gui.player
            if event == BUTTON:
                if event.arg == 'FFWD':
                    p.eventhandler(Event('SEEK', arg='10', context='audio'))
                elif event.arg == 'REW':
                    p.eventhandler(Event('SEEK', arg='-10', context='audio'))
                elif event.arg == 'PAUSE':
                    p.eventhandler(Event('PLAY', context='audio'))
                elif event.arg == 'STOP':
                    p.eventhandler(Event('STOP'))
                elif event.arg == 'NEXT':
                    p.eventhandler(Event('PLAYLIST_NEXT', context='audio'))
                elif event.arg == 'PREV':
                    p.eventhandler(Event('PLAYLIST_PREV', context='audio'))
            elif plugin.isevent(event) in ('DETACH', 'ATTACH'):
                p.eventhandler(event)
            elif event == VIDEO_START:
                p.eventhandler(Event('STOP'))


    @benchmark(benchmarking, benchmarkcall)
    def items(self, parent):
        _debug_('items(parent=%r)' % (parent,), 2)
        gui = audio.player.get()
        if gui and gui.player.is_playing():
            self.show_item.parent = parent
            return [ self.show_item ]
        return []


    @benchmark(benchmarking, benchmarkcall)
    def show(self, arg=None, menuw=None):
        _debug_('show(arg=%r, menuw=%r)' % (arg, menuw), 1)
        gui = audio.player.get()

        # restore the menuw's
        gui.menuw = menuw
        gui.item.menuw = menuw
        if gui.item.parent:
            gui.item.parent.menuw = menuw

        # hide the menu and show the player
        menuw.hide()
        gui.show()

        rc.post_event(plugin.event('ATTACH'))
