#if 0 /*
# -----------------------------------------------------------------------
# coverserarch.py - Plugin for album cover support
# -----------------------------------------------------------------------
# $Id$
#
# Notes: This plugin will allow you to find album covers. At first, only
#        Amazon is supported. Someone could easily add allmusic.com support
#        which is more complete, but lacks a general interface like amazon's
#        web services.
#
#        You also need an Amazon developer key.
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.20  2003/10/20 14:23:08  outlyer
# Tolerate 404 errors from Amazon without crashing. Sorry this is so ugly,
# this whole algorithm needs to be cleaned up.
#
# Revision 1.19  2003/09/10 19:30:08  dischi
# add deactivation when something is wrong
#
# Revision 1.18  2003/09/09 18:54:59  dischi
# Add some doc
#
# Revision 1.17  2003/08/23 12:51:42  dischi
# removed some old CVS log messages
#
# Revision 1.3  2003/06/12 16:47:04  outlyer
# Tried to make the Amazon search more intelligent.
#
# Problem:
#     If a cover is not available, Amazon returns an 807b GIF file instead
#     of saying so
#
# Solution:
#     What we do now is check the content length of the file
#     before downloading and remove those entries from the list.
#
# I've also removed the example, since the plugin itself works better.
#
# Revision 1.2  2003/06/10 13:13:55  outlyer
# Initial revision is complete, current main problem is that it only
# writes 'cover.jpg' someone could add a submenu to choose between
# per-file or per-directory images, but I have to go to class now.
#
# I've tested this, but please let me know if you find problems.
#
# Revision 1.1  2003/06/07 18:43:26  outlyer
# The beginnings of a cover search plugin to complement Dischi's IMDB plugin
# for video. Currently, it uses the ID3 tag to find the album cover from
# amazon and prints the url on the screen.
#
# It doesn't do anything with it yet, because I still need to add a submenu
# to allow the user to choose:
#
# 1. Write a per-song cover (i.e. song_filename.jpg)
# 2. Write a per-album/directory cover (i.e. cover.jpg)
#
# If you want to see it in action, you can do a:
#
# plugin.activate('audio.coversearch')
#
# This only uses Amazon now, but could easily be extended to use allmusic.com
# if someone writes something to interface with it. Amazon was dead-simple
# to use, so I did it first, though Amazon is pretty weak, selection-wise
# compared to allmusic.com
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
# ----------------------------------------------------------------------- */
#endif

import os

import menu
import plugin
import re
import urllib2
import time
import config
import Image
import cStringIO
from xml.dom import minidom # ParseError used by amazon module

from gui.PopupBox import PopupBox
from gui.AlertBox import AlertBox

import amazon


class PluginInterface(plugin.ItemPlugin):
    """
    This plugin will allow you to search for CD Covers for your albums. To do that
    just go in an audio item and press 'e' (on your keyboard) or 'ENTER' on your
    remote control. That will present you a list of options with Find a cover for
    this music as one item, just select it press 'enter' (on your keyboard) or
    'SELECT' on your remote control and then it will search the cover in amazon.com.

    Please Notice that this plugin use the Amazon.com web services and you will need
    an Amazon developer key. You can get your at: http://www.amazon.com/webservices,
    get that key and put it in a file named ~/.amazonkey or passe it as an argument
    to this plugin.

    To activate this plugin, put the following in your local_conf.py.

    If you have the key in ~/.amazonkey
    plugin.activate( 'audio.coversearch' ) 

    Or this one if you want to pass the key to the plugin directly:
    plugin.activate( 'audio.coversearch', args=('YOUR_KEY',) ) 
    """
    def __init__(self, license=None):
        if not config.USE_NETWORK:
            self.reason = 'no network'
            return
        
        if license:
            amazon.setLicense(license)
        try:
            amazon.getLicense()
        except amazon.NoLicenseKey:
            print 'To search for covers you need an Amazon.com Web Services'
            print 'license key. You can get yours from:'
            print 'https://associates.amazon.com/exec/panama/associates/join/'\
                  'developer/application.html'
            self.reason = 'no amazon key'
            return
            
        plugin.ItemPlugin.__init__(self)


    def actions(self, item):
        self.item = item
        # don't allow this for items on an audio cd, only on the disc itself
        if item.type == 'audio' and item.parent.type == 'audiocd':
            return []

        # don't allow this for items in a playlist
        if item.type == 'audio' and item.parent.type == 'playlist':
            return []
        
        if item.type == 'audio' or item.type == 'audiocd':
            try:
                # use title for audicds and album for normal data
                if self.item.getattr('artist') and \
                   ((self.item.getattr('album') and item.type == 'audio') or \
                    (self.item.getattr('title') and item.type == 'audiocd')):
                    return [ ( self.cover_search_file, 'Find a cover for this music',
                               'imdb_search_or_cover_search') ]
                else:
                    if config.DEBUG:
                        print "WARNING: coversearch disabled for this item! " + \
                              "coversearch needs an item with " + \
                              "Artist and Album (if it's a mp3 or ogg) or " + \
                              "Title (if it's a cd track) to be able to search. " + \
                              "So you need a file with a ID3 tag (mp3) or an Ogg Info. " + \
                              "Maybe you must fix this file (%s) tag?" % item.filename 
            except KeyError:
                if config.DEBUG:
                    print "WARNING: coversearch disabled for this item! " + \
                          "coversearch needs an item with " + \
                          "Artist and Album (if it's a mp3 or ogg) or " + \
                          "Title (if it's a cd track) to be able to search. " + \
                          "So you need a file with a ID3 tag (mp3) or an Ogg Info. " + \
                          "Maybe you must fix this file (%s) tag?" % item.filename
            except AttributeError:
                if config.DEBUG:
                    print "WARNING: Unknown CD, cover searching is disabled"
        return []


    def cover_search_file(self, arg=None, menuw=None):
        """
        search imdb for this item
        """
        box = PopupBox(text='searching Amazon...')
        box.show()

        if self.item.type == 'audio':
            album = self.item.info['album']
        else:
            album = self.item.info['title']

        artist = self.item.info['artist']

        search_string = '%s %s' % (artist,album)
        search_string = re.sub('[\(\[].*[\)\]]', '', search_string)
        try:
            cover = amazon.searchByKeyword(search_string , product_line="music")
        except amazon.AmazonError:
            box.destroy() 
            box = PopupBox(text='No matches for %s - %s' % (str(artist),str(album)))
            box.show()
            time.sleep(2)
            box.destroy()
            return

        except amazon.ParseError:
            box.destroy()
            box = PopupBox(text='The cover provider returned bad information.')
            box.show()
            time.sleep(2)
            box.destroy()
            return

        items = []
        
        # Check if they're valid before presenting the list to the user
        # Grrr I wish Amazon wouldn't return an empty gif (807b)

        MissingFile = False
        m = None
        n = None

        for i in range(len(cover)):
            try:
                m = urllib2.urlopen(cover[i].ImageUrlLarge)
            except urllib2.HTTPError:
                # Amazon returned a 404
                MissingFile = True
            if not MissingFile and not (m.info()['Content-Length'] == '807'):
                image = Image.open(cStringIO.StringIO(m.read()))
                items += [ menu.MenuItem('%s' % cover[i].ProductName,
                                         self.cover_create, cover[i].ImageUrlLarge,
                                         image=image) ]
                m.close()
            else:
                if m: m.close()
                MissingFile = False
                # see if a small one is available
                try:
                    n = urllib2.urlopen(cover[i].ImageUrlMedium)
                except urllib2.HTTPError:
                    MissingFile = True
                if not MissingFile and not (n.info()['Content-Length'] == '807'):
                    image = Image.open(cStringIO.StringIO(n.read()))
                    items += [ menu.MenuItem('%s [small]' % cover[i].ProductName,
                                    self.cover_create, cover[i].ImageUrlMedium) ]
                    n.close()
                else:
                    if n: n.close()
                    # maybe the url is wrong, try to change '.01.' to '.03.'
                    cover[i].ImageUrlLarge = cover[i].ImageUrlLarge.replace('.01.', '.03.')
                    n = urllib2.urlopen(cover[i].ImageUrlLarge)
                    if not (n.info()['Content-Length'] == '807'):
                        image = Image.open(cStringIO.StringIO(n.read()))
                        items += [ menu.MenuItem('%s [small]' % cover[i].ProductName,
                                                 self.cover_create, cover[i].ImageUrlLarge) ]
                    n.close()

        box.destroy()
        if len(items) == 1:
            self.cover_create(arg=items[0].arg, menuw=menuw)
            return
        if items: 
            moviemenu = menu.Menu('Cover Results', items)
            menuw.pushmenu(moviemenu)
            return

        box = PopupBox(text='No covers available from Amazon')
        box.show()
        time.sleep(2)
        box.destroy()
        return


    def cover_create(self, arg=None, menuw=None):
        """
        create cover file for the item
        """
        import amazon
        import directory
        
        box = PopupBox(text='getting data...')
        box.show()
        
        #filename = os.path.splitext(self.item.filename)[0]
        if self.item.type == 'audiocd':
            filename = '%s/mmpython/disc/%s.jpg' % (config.FREEVO_CACHEDIR,
                                                    self.item.info['id'])
        else:
            filename = '%s/cover.jpg' % (os.path.dirname(self.item.filename))

        fp = urllib2.urlopen(str(arg))
        m = open(filename,'wb')
        m.write(fp.read())
        m.close()
        fp.close()

        if self.item.type == 'audiocd':
            self.item.image = filename
            
        if not self.item.type == 'audiocd' and self.item.parent.type == 'dir':
            # set the new cover to all items
            self.item.parent.image = filename
            for i in self.item.parent.menu.choices:
                i.image = filename

        # check if we have to go one menu back (called directly) or
        # two (called from the item menu)
        back = 1
        if menuw.menustack[-2].selected != self.item:
            back = 2

        # maybe we called the function directly because there was only one
        # cover and we called it with an event
        if menuw.menustack[-1].selected == self.item:
            back = 0
            
        # update the directory
        if directory.dirwatcher_thread:
            directory.dirwatcher_thread.scan()

        # go back in menustack
        for i in range(back):
            menuw.delete_menu()

        if back == 0:
            menuw.refresh()
        box.destroy()
