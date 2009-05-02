# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# This is the Freevo main application code
# -----------------------------------------------------------------------
# $Id$
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

"""
This is the Freevo main entry point
"""

# Must do this here to make sure no os.system() calls generated by module init
# code gets LD_PRELOADed
import os
os.environ['LD_PRELOAD'] = ''

import sys, time
import traceback
import signal
from optparse import Option, OptionValueError, OptionParser, IndentedHelpFormatter
import pprint

try:
    from xml.dom import minidom

    # now load other modules to check if all requirements are installed
    import pygame
    import twisted

    import kaa
    import kaa.metadata as metadata
    import kaa.imlib2 as imlib2

    import config
    import rc
    rc.get_singleton(is_helper=0)

except ImportError, why:
    print 'Can\'t find all Python dependencies:'
    print why
    if str(why)[-7:] == 'Numeric':
        print 'You need to recompile pygame after installing Numeric!'
    print
    print 'Not all requirements of Freevo are installed on your system.'
    print 'Please check the INSTALL file for more information.'
    print
    sys.exit(0)


# check if kaa.base is up to date to avoid bug reports for already fixed bugs
v = 'unknown'
try:
    import kaa.version
    if kaa.version.VERSION < 0.4:
        v = kaa.version.VERSION
        raise ImportError
except (AttributeError, ImportError):
    print 'Error: Installed kaa.base version (%s) is too old.' % v
    print 'Please update kaa.base to version 0.4 or higher or get it with subversion'
    print 'svn export svn://svn.freevo.org/kaa/trunk/base kaa/base'
    print
    sys.exit(0)

# check if kaa.metadata is up to date to avoid bug reports for already fixed bugs
v = 'unknown'
try:
    import kaa.metadata.version
    if kaa.metadata.version.VERSION < 0.7:
        v = kaa.metadata.version.VERSION
        raise ImportError
except ImportError:
    print 'Error: Installed kaa.metadata version (%s) is too old.' % v
    print 'Please update kaa.metadata to version 0.6 or higher or get it with subversion'
    print 'svn export svn://svn.freevo.org/kaa/trunk/metadata kaa/metadata'
    print
    sys.exit(0)

# check if kaa.imlib2 is up to date to avoid bug reports for already fixed bugs
v = 'unknown'
try:
    import kaa.imlib2.version
    if kaa.imlib2.version.VERSION < 0.2:
        v = kaa.metadata.version.VERSION
        raise ImportError
except ImportError:
    print 'Error: Installed kaa.imlib2 version (%s) is too old.' % v
    print 'Please update kaa.imlib2 to version 0.1 or higher or get it with subversion'
    print 'svn export svn://svn.freevo.org/kaa/trunk/imlib2 kaa/imlib2'
    print
    sys.exit(0)

import rc      # The RemoteControl class.
import util    # Various utilities
import osd     # The OSD class, used to communicate with the OSD daemon
import menu    # The menu widget class
import dialog  # Message/Volume/Dialog display function (must be imported after config)
try:
    import skin    # The skin class
except pygame.error, why:
    sys.exit(why)

from item import Item
from event import *
from plugins.shutdown import shutdown

# Create the OSD object
osd = osd.get_singleton()


class SkinSelectItem(Item):
    """
    Item for the skin selector
    """
    def __init__(self, parent, name, image, skin):
        Item.__init__(self, parent)
        self.name  = name
        self.image = image
        self.skin  = skin

    def actions(self):
        return [ ( self.select, '' ) ]

    def select(self, arg=None, menuw=None):
        """
        Load the new skin and rebuild the main menu
        """
        import plugin
        skin.set_base_fxd(self.skin)
        pos = menuw.menustack[0].choices.index(menuw.menustack[0].selected)

        parent = menuw.menustack[0].choices[0].parent
        menuw.menustack[0].choices = []
        for p in plugin.get('mainmenu'):
            menuw.menustack[0].choices += p.items(parent)

        for i in menuw.menustack[0].choices:
            i.is_mainmenu_item = True

        menuw.menustack[0].selected = menuw.menustack[0].choices[pos]
        menuw.back_one_menu()



class MainMenu(Item):
    """
    this class handles the main menu
    """
    def getcmd(self):
        """
        Setup the main menu and handle events (remote control, etc)
        """
        import plugin
        menuw = menu.MenuWidget()
        items = []
        for p in plugin.get('mainmenu'):
            items += p.items(self)

        for i in items:
            i.is_mainmenu_item = True

        mainmenu = menu.Menu(_('Freevo Main Menu'), items, item_types='main', umount_all = 1)
        menuw.pushmenu(mainmenu)
        osd.add_app(menuw)


    def eventhandler(self, event=None, menuw=None, arg=None):
        """
        Automatically perform actions depending on the event, e.g. play DVD
        """
        # pressing DISPLAY on the main menu will open a skin selector
        # (only for the new skin code)
        if event == MENU_CHANGE_STYLE:
            items = []
            for name, image, skinfile in skin.get_skins():
                items += [ SkinSelectItem(self, name, image, skinfile) ]

            menuw.pushmenu(menu.Menu(_('Skin Selector'), items))
            return True

        # give the event to the next eventhandler in the list
        return Item.eventhandler(self, event, menuw)



class Splashscreen(skin.Area):
    """
    A simple splash screen for osd startup
    """
    def __init__(self, text):
        skin.Area.__init__(self, 'content')

        self.pos          = 0
        self.bar_border   = skin.Rectange(bgcolor=0xff000000L, size=2)
        self.bar_position = skin.Rectange(bgcolor=0xa0000000L)
        self.text         = text
        self.first_draw   = True


    def update_content(self):
        """
        there is no content in this area
        """
        layout    = self.layout
        area      = self.area_val
        content   = self.calc_geometry(layout.content, copy_object=True)

        self.write_text(self.text, content.font, content, height=-1, align_h='center')

        pos = 0
        x0, x1 = content.x, content.x + content.width
        y = content.y + content.font.font.height + content.spacing
        if self.pos:
            pos = round(float((x1 - x0 - 4)) / (float(100) / self.pos))
        self.drawroundbox(x0, y, x1-x0, 20, self.bar_border)
        self.drawroundbox(x0+2, y+2, pos, 16, self.bar_position)


    def progress(self, pos):
        """
        set the progress position and refresh the screen
        """
        self.pos = pos
        blend = config.FREEVO_USE_ALPHABLENDING and self.first_draw
        skin.draw('splashscreen', None, blend=blend)
        self.first_draw = False



class MainTread:
    """
    The main thread or loop of freevo
    """
    def __init__(self):
        """
        get the list of plugins wanting events
        """
        self.eventhandler_plugins  = []
        self.eventlistener_plugins = []

        for p in plugin.get('daemon_eventhandler'):
            if hasattr(p, 'event_listener') and p.event_listener:
                self.eventlistener_plugins.append(p)
            else:
                self.eventhandler_plugins.append(p)
        kaa.EventHandler(self.eventhandler).register()


    def eventhandler(self, event):
        """
        event handling function for the main loop
        """
        if event == OS_EVENT_POPEN2:
            _debug_('popen2 %s' % event.arg[1])
            event.arg[0].child = util.popen3.Popen3(event.arg[1])
            return

        _debug_('handling event %s' % str(event), 2)

        for p in self.eventlistener_plugins:
            p.eventhandler(event=event)

        if event == FUNCTION_CALL:
            event.arg()

        elif event.handler:
            event.handler(event=event)

        # Pass the event to the dialog subsystem first incase a dialog is being displayed.
        elif dialog.handle_event(event):
            return

        # Send events to either the current app or the menu handler
        elif rc.app():
            if not rc.app()(event):
                for p in self.eventhandler_plugins:
                    if p.eventhandler(event=event):
                        break
                else:
                    _debug_('no eventhandler for event %s' % event, 2)

        else:
            app = osd.focused_app()
            if app:
                try:
                    if config.DEBUG_TIME:
                        t1 = time.clock()
                    app.eventhandler(event)
                    if config.DEBUG_TIME:
                        print time.clock() - t1

                except SystemExit:
                    _debug_('SystemExit re-raised')
                    raise

                except:
                    if config.FREEVO_EVENTHANDLER_SANDBOX:
                        traceback.print_exc()
                        from gui import ConfirmBox
                        pop = ConfirmBox(
                            text=_("Event '%s' crashed\n\n" +
                                "Please take a look at the logfile and report" +
                                "the bug to the Freevo mailing list. The state" +
                                "of Freevo may be corrupt now and this error" +
                                "could cause more errors until you restart" +
                                "Freevo.\n\n" +
                                "Logfile: %s\n\n") %
                            (event, sys.stdout.logfile),
                            width=osd.width-(config.OSD_OVERSCAN_LEFT+config.OSD_OVERSCAN_RIGHT)-50,
                            handler=shutdown,
                            handler_message = _('shutting down...'))
                        pop.b0.set_text(_('Shutdown'))
                        pop.b0.toggle_selected()
                        pop.b1.set_text(_('Continue'))
                        pop.b1.toggle_selected()
                        pop.show()
                    else:
                        raise
            else:
                _debug_('no target for events given')


def unix_signal_handler(sig, frame):
    """
    Unix signal handler to shut down freevo
    """
    _debug_('unix_signal_handler(sig=%r, frame=%r)' % (sig, frame))
    _debug_('shutdown() called')
    shutdown(exit=True)
    _debug_('SystemExit raised')
    raise SystemExit


def signal_handler():
    """
    the signal handler to shut down freevo
    """
    _debug_('signal_handler()')
    _debug_('shutdown() called')
    shutdown(exit=True)
    _debug_('SystemExit raised')
    raise SystemExit


frames = {}
def tracefunc(frame, event, arg, _indent=[0]):
    """
    function to trace and time everything inside freevo for debugging
    """
    # ignore non-freevo and non-kaa calls
    if opts.trace not in ('all', 'sys'):
        for module in opts.trace:
            if frame.f_code.co_filename.find(module) >= 0:
                break
        else:
            return tracefunc
    elif opts.trace == 'all':
        if frame.f_code.co_filename.find('/freevo/') == -1 and frame.f_code.co_filename.find('/kaa/') == -1:
            return tracefunc
    # ignore debugging calls
    if frame.f_code.co_name == '_debug_function_':
        return tracefunc
    spacer = '  '
    if event == 'call':
        filename = frame.f_code.co_filename
        funcname = frame.f_code.co_name
        lineno = frame.f_code.co_firstlineno
        if 'self' in frame.f_locals:
            try:
                classinst = frame.f_locals['self']
                funcname = '%s.%s' % (classinst.__class__.__name__, funcname)
            except (AssertionError, AttributeError):
                pass
        here = '%s:%s %s()' % (filename, lineno, funcname)
        tracefd.write('%03d%s-> %s\n' % (_indent[0], spacer * _indent[0], here))
        tracefd.flush()
        frames[frame] = (time.clock(), here)
        _indent[0] += 1
    elif event == 'return':
        try:
            startclock, here = frames[frame]
            _indent[0] -= 1
            tracefd.write('%03d%s<- %s %.6f\n' % (_indent[0], spacer * _indent[0], here, (time.clock() - startclock)))
            tracefd.flush()
            del(frames[frame])
        except KeyError:
            filename = frame.f_code.co_filename
            funcname = frame.f_code.co_name
            lineno = frame.f_code.co_firstlineno
            here = '%s:%s %s()' % (filename, lineno, funcname)
            tracefd.write('%s** %s\n' % (spacer * _indent[0], here))
            tracefd.flush()

    return tracefunc


main_usage = """
%prog [options]

Main freevo module"""

def parse_options(defaults, version):
    """
    Parse command line options
    """
    print 'version:', version
    formatter=IndentedHelpFormatter(indent_increment=2, max_help_position=32, width=100, short_first=0)
    parser = OptionParser(conflict_handler='resolve', formatter=formatter, usage=main_usage, version='freevo-'+version)
    #parser.add_option('-v', '--verbose', action='count', default=0,
    #    help='set the level of verbosity [default:%default]')
    parser.add_option('-d', '--debug', action='count', dest='debug', default=0,
        help='set the level of debuging')
    parser.add_option('--trace', action='append', default=[],
        help='activate tracing of one or more modules (useful for debugging)')
    parser.add_option('--daemon', action='store_true', default=False,
        help='run freevo or a helper as a daemon [default:%default]')
    parser.add_option('-f', '--force-fs', action='store_true', default=False,
        help='force X11 to start full-screen [default:%default]')
    parser.add_option('--doc', action='store_true', default=False,
        help='generate API documentation [default:%default]')
    return parser.parse_args()


#
# Freevo main function
#
try:
    try:
        import freevo.version as version
    except ImportError:
        import version
except ImportError:
    pass

# parse arguments
defaults = { }
(opts, args) = parse_options(defaults, version.version)
defaults.update(opts.__dict__)

if opts.force_fs:
    # force fullscreen mode
    # deactivate screen blanking and set osd to fullscreen
    _debug_('os.system("xset -dpms s off")')
    os.system('xset -dpms s off')
    if config.OSD_X11_CURSORS is not None:
        _debug_('os.system("xsetroot -cursor %s")' % config.OSD_X11_CURSORS)
        os.system('xsetroot -cursor %s' % config.OSD_X11_CURSORS)
    config.START_FULLSCREEN_X = 1

if opts.debug:
    config.DEBUG = opts.debug

if opts.trace:
    # activate a trace function
    global trace_pat
    tracefd = open(os.path.join(config.FREEVO_LOGDIR, 'trace.txt'), 'w')
    sys.settrace(tracefunc)

if opts.doc:
    # create api doc for Freevo and move it to Docs/api
    import pydoc
    import re
    for file in util.match_files_recursively('src/', ['py' ]):
        # doesn't work for everything :-(
        if file not in ( 'src/tv/record_server.py', ) and \
               file.find('src/www') == -1 and file.find('src/helpers') == -1:
            file = re.sub('/', '.', file)
            try:
                pydoc.writedoc(file[4:-3])
            except:
                pass
    try:
        os.mkdir('Docs/api')
    except:
        pass
    for file in util.match_files('.', ['html', ]):
        print 'moving %s' % file
        os.rename(file, 'Docs/api/%s' % file)
    print
    print 'wrote api doc to \'Docs/api\''
    shutdown(exit=True)


try:
    # signal handler
    signal.signal(signal.SIGTERM, unix_signal_handler)
    signal.signal(signal.SIGINT, unix_signal_handler)
    kaa.main.signals['shutdown'].connect(signal_handler)

    # load the fxditem to make sure it's the first in the
    # mimetypes list
    import fxditem

    # load all plugins
    import plugin

    # prepare the skin
    skin.prepare()

    # Fire up splashscreen and load the plugins
    splash = Splashscreen(_('Starting Freevo-%s, please wait ...') % version.version)
    skin.register('splashscreen', ('screen', splash))
    plugin.init(splash.progress)
    dialog.init()
    skin.delete('splashscreen')

    # Fire up splashscreen and load the cache
    if config.MEDIAINFO_USE_MEMORY == 2:
        import util.mediainfo

        splash = Splashscreen(_('Reading cache, please wait ...'))
        skin.register('splashscreen', ('screen', splash))

        cachefiles = []
        for type in ('video', 'audio', 'image', 'games'):
            if plugin.is_active(type):
                n = 'config.%s_ITEMS' % type.upper()
                x = eval(n)
                for item in x:
                    if os.path.isdir(item[1]):
                        cachefiles += [ item[1] ] + util.get_subdirs_recursively(item[1])


        cachefiles = util.unique(cachefiles)

        for f in cachefiles:
            splash.progress(int((float((cachefiles.index(f)+1)) / len(cachefiles)) * 100))
            util.mediainfo.load_cache(f)
        skin.delete('splashscreen')

    # prepare again, now that all plugins are loaded
    skin.prepare()

    # start menu
    MainMenu().getcmd()

    # Kick off the main menu loop
    _debug_('Main loop starting...',2)

    MainTread()

    print 'Freevo %s ready' % (version.version,)
    rc.post_event(FREEVO_READY)
    kaa.main.run()
    print 'Freevo %s finished' % (version.version,)

#except KeyboardInterrupt:
#    print 'Shutdown by keyboard interrupt'
#    # Shutdown the application
#    shutdown()

except SystemExit, why:
    print 'Freevo %s exited' % (version.version,)

except Exception, why:
    _debug_('Crash!: %s' % (why), config.DCRITICAL)
    try:
        tb = sys.exc_info()[2]
        fname, lineno, funcname, text = traceback.extract_tb(tb)[-1]

        if config.FREEVO_EVENTHANDLER_SANDBOX:
            secs = 5
        else:
            secs = 1
        for i in range(secs, 0, -1):
            osd.clearscreen(color=osd.COL_BLACK)
            osd.drawstring(_('Freevo crashed!'), 70, 70, fgcolor=osd.COL_ORANGE)
            osd.drawstring(_('Filename: %s') % fname, 70, 130, fgcolor=osd.COL_ORANGE)
            osd.drawstring(_('Lineno: %s') % lineno, 70, 160, fgcolor=osd.COL_ORANGE)
            osd.drawstring(_('Function: %s') % funcname, 70, 190, fgcolor=osd.COL_ORANGE)
            osd.drawstring(_('Text: %s') % text, 70, 220, fgcolor=osd.COL_ORANGE)
            osd.drawstring(str(sys.exc_info()[1]), 70, 280, fgcolor=osd.COL_ORANGE)
            osd.drawstring(_('Please see the logfiles for more info'), 70, 350, fgcolor=osd.COL_ORANGE)
            osd.drawstring(_('Exit in %s seconds') % i, 70, 410, fgcolor=osd.COL_ORANGE)
            osd.update()
            time.sleep(1)

    except:
        pass
    traceback.print_exc()

    # Shutdown the application, but not the system even if that is
    # enabled
    shutdown()
