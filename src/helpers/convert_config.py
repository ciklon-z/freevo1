import sys
import os
import re

change_map = {
    'DIR_MOVIES': 'VIDEO_ITEMS',
    'DIR_AUDIO' : 'AUDIO_ITEMS',
    'DIR_IMAGES': 'IMAGE_ITEMS',
    'DIR_GAMES' : 'GAMES_ITEMS',
    'DIR_RECORD': 'TV_RECORD_DIR',
    'SUFFIX_VIDEO_MPLAYER_FILES': 'VIDEO_MPLAYER_SUFFIX',
    'SUFFIX_VIDEO_XINE_FILES': 'VIDEO_XINE_SUFFIX',
    'ONLY_SCAN_DATADIR': 'VIDEO_ONLY_SCAN_DATADIR',
    'SUFFIX_AUDIO_FILES': 'AUDIO_SUFFIX',
    'SUFFIX_AUDIO_PLAYLISTS': 'PLAYLIST_SUFFIX',
    'SUFFIX_IMAGE_FILES': 'IMAGE_SUFFIX',
    'SUFFIX_IMAGE_SSHOW': 'IMAGE_SSHOW_SUFFIX',
    'MAME_CACHE': 'GAMES_MAME_CACHE',
    'OSD_SKIN': 'SKIN_MODULE',
    }

def help():
    print 'convert local_conf.py to use the new variable names'
    print 'usage: convert_config local_conf.py [ -w ]'
    print
    print 'if -w is given the local_conf.py wil be rewritten, without the option'
    print 'the script will only print the changes.'
    print
    print 'Developer may use the option -s (without local_conf) to scan for files'
    print 'which use the deleted variables'
    print
    sys.exit(0)
    
seperator = ' #=[]{}().:,\n'

out = None

if len(sys.argv) <= 2 and sys.argv[1] == '-s':
    print 'searching for files using old style variables'
    s = ''
    for var in change_map:
        s += '|%s' % var
    s = '(%s)' % s[1:]
    pipe = 'xargs egrep \'%s\' | grep -v helpers/convert_config' % s
    os.system('find . -name \*.py | %s' % pipe)
    os.system('find . -name \*.rpy | %s' % pipe)
    sys.exit(0)
    
try:
    cfg = open(sys.argv[1])
except:
    help()

data = cfg.readlines()
cfg.close()

if len(sys.argv) == 3 and sys.argv[2] == '-w':
    print 'write output file'
    out = open(sys.argv[1], 'w')

change = True
if sys.argv[1] == 'freevo_config.py':
    change = False
    
for line in data:
    if line.startswith('FREEVO_CONF_VERSION'):
        change = True
        
    if not change:
        if out:
            out.write(line)
        continue

    for var in change_map:
        if line.find(var) >= 0 and \
           (line.startswith(var) or line[line.find(var)-1] in seperator) and \
           line[line.find(var)+len(var)] in seperator:
            if out:
                line = line.replace(var, change_map[var])
            else:
                print 'changing config file line:'
                print line[:-1]
                print line[:-1].replace(var, change_map[var])
                print
    if out:
        out.write(line)

if out:
    out.close()
    
