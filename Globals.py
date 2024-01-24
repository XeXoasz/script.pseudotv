#   Copyright (C) 2011 Jason Anderson
#
#
# This file is part of PseudoTV.
#
# PseudoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV.  If not, see <http://www.gnu.org/licenses/>.

import os, sys, re, traceback
import xbmcaddon, xbmc, xbmcgui, xbmcvfs
import Settings

from FileAccess import FileLock 
from pyfscache import *

def log(msg, level = xbmc.LOGDEBUG):
    if level == xbmc.LOGDEBUG:
        xbmcgui.Window(10000).setProperty('PTVL.DEBUG_LOG', uni(msg))
    else:
        msg += ' ,' + traceback.format_exc()
        xbmcgui.Window(10000).setProperty('PTVL.ERROR_LOG', uni(msg))
    if DEBUG != True and level == xbmc.LOGDEBUG:
        return
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + uni(msg), level)

def debug(msg, *args):
    try:
        txt=u''
        msg=unicode(msg)
        for arg in args:
            if type(arg) == int:
                arg = unicode(arg)
            if type(arg) == list:
                arg = unicode(arg)
            txt = txt + u"/" + arg
        if txt == u'':
            xbmc.log(u"PSTV: {0}".format(msg).encode('ascii','xmlcharrefreplace'), xbmc.LOGDEBUG)
        else:
            xbmc.log(u"PSTV: {0}#{1}#".format(msg, txt).encode('ascii','xmlcharrefreplace'), xbmc.LOGDEBUG)
    except:
        print ("PSTV: Error in Debugoutput")
        print (msg)
        print (args)

ADDON = xbmcaddon.Addon(id='script.pseudotv')
ADDON_ID = ADDON.getAddonInfo('id')
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_ID = REAL_SETTINGS.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
LANGUAGE = ADDON.getLocalizedString
CWD = ADDON.getAddonInfo('path').decode("utf-8")
VERSION = ADDON.getAddonInfo('version')
ICON = ADDON.getAddonInfo('icon')
ICON = os.path.join(ADDON_PATH, 'icon.png')
FANART = os.path.join(ADDON_PATH, 'fanart.jpg')

def log(msg, level = xbmc.LOGDEBUG):
    try:
        xbmc.log(ADDON_ID + '-' + ascii(msg), level)
    except:
        pass


def uni(string, encoding = 'utf-8'):
    if isinstance(string, basestring):
        if not isinstance(string, unicode):
           string = unicode(string, encoding)

    return string

def ascii(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('ascii', 'ignore')

    return string


TIMEOUT = 15 * 1000
PREP_CHANNEL_TIME = 60 * 60 * 24 * 5
NOTIFICATION_CHECK_TIME = 5
NOTIFICATION_TIME_BEFORE_END = 90
NOTIFICATION_DISPLAY_TIME = 8

MODE_RESUME = 1
MODE_ALWAYSPAUSE = 2
MODE_ORDERAIRDATE = 4
MODE_RANDOM = 8
MODE_REALTIME = 16
MODE_STARTMODES = MODE_RANDOM | MODE_REALTIME | MODE_RESUME

# Ignore seeking for live feeds and other chtypes/plugins that don't support it.
IGNORE_SEEKTIME_CHTYPE = [8,9]
IGNORE_SEEKTIME_PLUGIN = []


# Maximum is 10
RULES_PER_PAGE = 7

# Chtype Limit
NUMBER_CHANNEL_TYPES = 17

# Channel Limit, Current available max is 999
CHANNEL_LIMIT = 999

SETTINGS_LOC = ADDON.getAddonInfo('profile').decode("utf-8")
CHANNEL_SHARING = False
LOCK_LOC = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'cache' + '/'))

if ADDON.getSetting('ChannelSharing') == "true":
    CHANNEL_SHARING = True
    LOCK_LOC = xbmc.translatePath(os.path.join(ADDON.getSetting('SettingsFolder'), 'cache' + '/'))

CHANNELS_LOC = os.path.join(SETTINGS_LOC, 'cache' + '/')
REQUESTS_LOC = xbmc.translatePath(os.path.join(CHANNELS_LOC, 'requests',''))
IMAGES_LOC = xbmc.translatePath(os.path.join(CWD, 'resources', 'images' + '/'))
LOGOS_LOC = xbmc.translatePath(os.path.join(CWD, 'resources', 'logos' + '/'))
GEN_CHAN_LOC = os.path.join(CHANNELS_LOC, 'generated' + '/')
MADE_CHAN_LOC = os.path.join(CHANNELS_LOC, 'stored' + '/')
CHANNELBUG_LOC = xbmc.translatePath(os.path.join(CHANNELS_LOC, 'ChannelBug' + '/'))

CHANNELBUG_POS = [[19,19], [1695,19], [1695,952], [19,952], [250,19], [1483,19], [1483,952], [250,952]]

SHORT_CLIP_ENUM = [15, 30, 60, 90, 120, 180, 240, 300, 360]
INFO_DUR = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
SEEK_FORWARD = [10, 30, 60, 180, 300, 600, 1800]
SEEK_BACKWARD = [-10, -30, -60, -180, -300, -600, -1800]
MEDIA_LIMIT = [10, 25, 50, 100, 250, 500, 1000, 0]
CHANNEL_DELAY = [25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
HOLD_ACTIONS = [.25, .5, 1, 1.5, 2, 2.5, 3, 3.5, 4]
ASSIGNED_DURATION = [1, 5, 10, 15, 30, 45, 60, 90, 120]
DIR_ASSIGNED_DURATION = [1, 5, 10, 15, 30, 45, 60, 90, 120]
BUG_BRIGHTNESS = [.25, .5, .75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]


NUM_COLOUR = ['0xFFFF0000', '0xFF00FF00', '0xFF0000FF', '0xFFFFFF00', '0xFF00FFFF', '0xFFFFA500', '0xFFFF00FF', '0xFF808080', '0xFFFFFFFF']

GlobalFileLock = FileLock()
ADDON_SETTINGS = Settings.Settings()

TIME_BAR = 'pstvTimeBar.png'
BUTTON_NO_FOCUS = 'pstvButtonNoFocus.png'
BUTTON_FOCUS = 'pstvButtonFocus.png'
BUTTON_NO_FOCUS_SHORT = 'pstvButtonNoFocusShort.png'
BUTTON_FOCUS_SHORT = 'pstvButtonFocusShort.png'
BUTTON_NO_FOCUS_ALT1 = 'pstvButtonNoFocusAlt1.png'
BUTTON_NO_FOCUS_ALT2 = 'pstvButtonNoFocusAlt2.png'
BUTTON_NO_FOCUS_ALT3 = 'pstvButtonNoFocusAlt3.png'
BUTTON_NO_FOCUS_ALT1_SHORT = 'pstvButtonNoFocusAlt1Short.png'
BUTTON_NO_FOCUS_ALT2_SHORT = 'pstvButtonNoFocusAlt2Short.png'
BUTTON_NO_FOCUS_ALT3_SHORT = 'pstvButtonNoFocusAlt3Short.png'

RULES_ACTION_START = 1
RULES_ACTION_JSON = 2
RULES_ACTION_LIST = 4
RULES_ACTION_BEFORE_CLEAR = 8
RULES_ACTION_BEFORE_TIME = 16
RULES_ACTION_FINAL_MADE = 32
RULES_ACTION_FINAL_LOADED = 64
RULES_ACTION_OVERLAY_SET_CHANNEL = 128
RULES_ACTION_OVERLAY_SET_CHANNEL_END = 256

# Maximum is 10 for this
RULES_PER_PAGE = 7

ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2
ACTION_MOVE_UP = 3
ACTION_MOVE_DOWN = 4
ACTION_PAGEUP = 5
ACTION_PAGEDOWN = 6
ACTION_SELECT_ITEM = 7
ACTION_SELECT_ITEM2 = 100 #Mouse Left Click
ACTION_PREVIOUS_MENU = (9, 10, 92, 216, 247, 257, 275, 61467, 61448,)
ACTION_SHOW_INFO = 11
ACTION_STOP = 13
ACTION_OSD = 117
ACTION_NUMBER_0 = 58
ACTION_NUMBER_9 = 67
ACTION_INVALID = 999
ACTION_MOUSE_RIGHT_CLICK = 101 #Mouse Right Click
CONTEXT_MENU = 117
ACTION_NEXT_PICTURE = 28
ACTION_PREV_PICTURE = 29

EPG_ROWCOUNT = [3, 6, 9]
ROWCOUNT = EPG_ROWCOUNT[int(ADDON.getSetting("EPGRowcount"))]

REQUESTS_LOC = xbmc.translatePath(os.path.join(CHANNELS_LOC, 'requests',''))
MADE_CHAN_LOC = os.path.join(CHANNELS_LOC, 'stored','')
GEN_CHAN_LOC = os.path.join(CHANNELS_LOC, 'generated','')
XMLTV_CACHE_LOC = xbmc.translatePath(os.path.join(CHANNELS_LOC, 'xmltv',''))
STRM_CACHE_LOC = xbmc.translatePath(os.path.join(CHANNELS_LOC, 'strm','')) 
MOUNT_LOC = xbmc.translatePath(os.path.join(CHANNELS_LOC, 'mountpnt',''))
IMAGES_LOC = xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'images',''))
PTVL_SKIN_LOC = os.path.join(ADDON_PATH, 'resources', 'skins', '') #Path to PTVL Skin folder
SFX_LOC = os.path.join(ADDON_PATH, 'resources','sfx','')
XSP_LOC = xbmc.translatePath("special://profile/playlists/video/")
XMLTV_LOC = xbmc.translatePath(os.path.join(REAL_SETTINGS.getSetting('xmltvLOC'),''))
LOGO_LOC = xbmc.translatePath(os.path.join(REAL_SETTINGS.getSetting('ChannelLogoFolder'),'')) #Channel Logo location   
PVR_DOWNLOAD_LOC = xbmc.translatePath(os.path.join(REAL_SETTINGS.getSetting('PVR_Folder'),'')) #PVR Download location


# pyfscache globals
cache_hourly = FSCache(REQUESTS_LOC, days=0, hours=1, minutes=0)
cache_daily = FSCache(REQUESTS_LOC, days=1, hours=0, minutes=0)
cache_weekly = FSCache(REQUESTS_LOC, days=7, hours=0, minutes=0)
cache_monthly = FSCache(REQUESTS_LOC, days=28, hours=0, minutes=0)

MUSIC_TYPES = (xbmc.getSupportedMedia('music')).split('|')  
IMAGE_TYPES = (xbmc.getSupportedMedia('picture')).split('|')
MEDIA_TYPES = (xbmc.getSupportedMedia('video')).split('|')
STREAM_TYPES = ('http','https','rtsp','rtmp','udp','PlayMedia')
BCT_TYPES = ['bumper', 'commercial', 'trailer', 'rating', 'pseudocinema', 'intro', 'cellphone', 'coming soon', 'premovie', 'feature presentation', 'intermission']

# Eventghost broadcasts
EG_ALL = ['Starting','Loading: CHANNELNAME','Sleeping','Exiting']

# Limits
FILELIST_LIMIT = [2048,4096,8192,16384]
MAXFILE_DURATION = 16000
MINFILE_DURATION = 900

# Plugin exclusion strings
SF_FILTER = ['isearch', 'iplay - kodi playlist manager','create new super folder','explore kodi favourites']
EX_FILTER = SF_FILTER + ['This folder contains no content.','video resolver settings','<<','back','previous','home','search','find','clips','seasons','trailers']
GETADDONS_FILTER = ['hdhomerun','pseudolibrary']

# Duration in seconds "stacked" for chtypes >= 10
BYPASS_EPG_SECONDS = 900

# HEX COLOR OPTIONS 4 (Overlay CHANBUG, EPG Genre & CHtype) 
# http://www.w3schools.com/html/html_colornames.asp
COLOR_RED = '#FF0000'
COLOR_GREEN = '#008000'
COLOR_mdGREEN = '#3CB371'
COLOR_BLUE = '#0000FF'
COLOR_ltBLUE = '#ADD8E6'
COLOR_CYAN = '#00FFFF'
COLOR_ltCYAN = '##E0FFFF'
COLOR_PURPLE = '#800080'
COLOR_ltPURPLE = '#9370DB'
COLOR_ORANGE = '#FFA500'
COLOR_YELLOW = '#FFFF00'
COLOR_GRAY = '#808080'
COLOR_ltGRAY = '#D3D3D3'
COLOR_mdGRAY = '#696969'
COLOR_dkGRAY = '#A9A9A9'
COLOR_BLACK = '#000000'
COLOR_WHITE = '#FFFFFF'
COLOR_HOLO = 'FF0297eb'
COLOR_SMOKE = '#F5F5F5'

# EPG Chtype/Genre COLOR TYPES
COLOR_RED_TYPE = ['10', '17', 'TV-MA', 'R', 'NC-17', 'Youtube', 'Gaming', 'Sports', 'Sport', 'Sports Event', 'Sports Talk', 'Archery', 'Rodeo', 'Card Games', 'Martial Arts', 'Basketball', 'Baseball', 'Hockey', 'Football', 'Boxing', 'Golf', 'Auto Racing', 'Playoff Sports', 'Hunting', 'Gymnastics', 'Shooting', 'Sports non-event']
COLOR_GREEN_TYPE = ['5', 'News', 'Public Affairs', 'Newsmagazine', 'Politics', 'Entertainment', 'Community', 'Talk', 'Interview', 'Weather']
COLOR_mdGREEN_TYPE = ['9', 'Suspense', 'Horror', 'Horror Suspense', 'Paranormal', 'Thriller', 'Fantasy']
COLOR_BLUE_TYPE = ['Comedy', 'Comedy-Drama', 'Romance-Comedy', 'Sitcom', 'Comedy-Romance']
COLOR_ltBLUE_TYPE = ['2', '4', '14', '15', '16', 'Movie']
COLOR_CYAN_TYPE = ['8', 'Documentary', 'History', 'Biography', 'Educational', 'Animals', 'Nature', 'Health', 'Science & Tech', 'Learning & Education', 'Foreign Language']
COLOR_ltCYAN_TYPE = ['Outdoors', 'Special', 'Reality', 'Reality & Game Shows']
COLOR_PURPLE_TYPE = ['Drama', 'Romance', 'Historical Drama']
COLOR_ltPURPLE_TYPE = ['12', '13', 'LastFM', 'Vevo', 'VevoTV', 'Musical', 'Music', 'Musical Comedy']
COLOR_ORANGE_TYPE = ['11', 'TV-PG', 'TV-14', 'PG', 'PG-13', 'RSS', 'Animation', 'Animation & Cartoons', 'Animated', 'Anime', 'Children', 'Cartoon', 'Family']
COLOR_YELLOW_TYPE = ['1', '3', '6', 'TV-Y7', 'TV-Y', 'TV-G', 'G', 'Classic TV', 'Action', 'Adventure', 'Action & Adventure', 'Action and Adventure', 'Action Adventure', 'Crime', 'Crime Drama', 'Mystery', 'Science Fiction', 'Series', 'Western', 'Soap', 'Soaps', 'Variety', 'War', 'Law', 'Adults Only']
COLOR_GRAY_TYPE = ['Auto', 'Collectibles', 'Travel', 'Shopping', 'House Garden', 'Home & Garden', 'Home and Garden', 'Gardening', 'Fitness Health', 'Fitness', 'Home Improvement', 'How-To', 'Cooking', 'Fashion', 'Beauty & Fashion', 'Aviation', 'Dance', 'Auction', 'Art', 'Exercise', 'Parenting', 'Food', 'Health & Fitness']
COLOR_ltGRAY_TYPE = ['0', '7', 'NR', 'Consumer', 'Game Show', 'Other', 'Unknown', 'Religious', 'Anthology', 'None']

# Core Default Image Locations
DEFAULT_MEDIA_LOC =  xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', 'Default', 'media',''))
DEFAULT_EPGGENRE_LOC = xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', 'Default', 'media', 'epg-genres',''))