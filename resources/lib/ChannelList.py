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

import xbmc, xbmcgui, xbmcaddon
import subprocess, os
import time, threading
import datetime
import sys, re
import random


reload(sys)
sys.setdefaultencoding('utf-8')

from xml.dom.minidom import parse, parseString

from Playlist import Playlist
from Globals import *
from Channel import Channel
from VideoParser import VideoParser
from FileAccess import FileLock, FileAccess
from pyfscache import *
from random import randint

class ChannelList:
    def __init__(self):
        self.networkList = []
        self.studioList = []
        self.mixedGenreList = []
        self.showGenreList = []
        self.movieGenreList = []
        self.showList = []
        self.channels = []
        self.videoParser = VideoParser()
        self.sleepTime = 0
        self.threadPaused = False
        self.runningActionChannel = 0
        self.runningActionId = 0
        self.enteredChannelCount = 0
        self.background = True
        self.quickFlip = False
        self.quickflipEnabled = False
        self.AlreadyWarned = False
        self.DirAlreadyWarned = False
        self.FailWarning = False
        self.DirFailWarning = False
        self.AssignDuration = False
        self.DirAssignDuration = False
        self.AssignedDuration = 1800
        self.DirAssignedDuration = 1800
        self.SingleShowTitleIsEp = True
        self.UseEpisodeTitleKeepShowTitle = []
        self.UseEpisodeTitleHideTitle = []
        self.UseEpisodeTitleHideTitle = []
        self.HideDirectoryTitle = []
        random.seed()
        self.maxNeededChannels = 999


    def readConfig(self):
        self.channelResetSetting = int(ADDON.getSetting("ChannelResetSetting"))
        self.log('Channel Reset Setting is ' + str(self.channelResetSetting))
        self.forceReset = ADDON.getSetting('ForceChannelReset') == "true"
        self.log('Force Reset is ' + str(self.forceReset))
        self.updateDialog = xbmcgui.DialogProgress()
        self.startMode = int(ADDON.getSetting("StartMode"))
        self.log('Start Mode is ' + str(self.startMode))
        self.backgroundUpdating = int(ADDON.getSetting("ThreadMode"))
        self.mediaLimit = MEDIA_LIMIT[int(ADDON.getSetting("MediaLimit"))]
        self.YearEpInfo = ADDON.getSetting('HideYearEpInfo')
        self.maxNeededChannels = int(ADDON.getSetting("maxNeededChannels"))*50 + 100
        self.findMaxChannels()
        self.FailWarning = ADDON.getSetting('FailWarning') == "true"
        self.DirFailWarning = ADDON.getSetting('DirFailWarning') == "true"
        self.AssignDuration = ADDON.getSetting('AssignDuration') == "true"
        self.DirAssignDuration = ADDON.getSetting('DirAssignDuration') == "true"
        self.AssignedDuration = ASSIGNED_DURATION[int(ADDON.getSetting("AssignedDuration"))] * 60
        self.DirAssignedDuration = DIR_ASSIGNED_DURATION[int(ADDON.getSetting("DirAssignedDuration"))] * 60
        self.SingleShowTitleIsEp = ADDON.getSetting('SingleShowTitleIsEp') == "true"
        self.UseEpisodeTitleKeepShowTitle = ADDON.getSetting('UseEpisodeTitleKeepShowTitle').split(",")
        self.UseEpisodeTitleHideTitle = ADDON.getSetting('UseEpisodeTitleHideTitle').split(",")
        self.HideDirectoryTitle = ADDON.getSetting('HideDirectoryTitle').split(",")
        self.incIceLibrary = ADDON.getSetting('IncludeIceLib') == "true"
        self.quickFlip = ADDON.getSetting('Enable_quickflip') == "true"
        self.startTime = time.time()
        self.log("IceLibrary is " + str(self.incIceLibrary))
        self.incBCTs = ADDON.getSetting('IncludeBCTs') == "true"
        self.log("IncludeBCTs is " + str(self.incBCTs))
        self.includeMeta = ADDON.getSetting('IncludeMeta') == "true"
        self.log("IncludeMeta is " + str(self.includeMeta))
        
        
        if self.forceReset:
            ADDON.setSetting('ForceChannelReset', "False")
            self.forceReset = False

        try:
            self.lastResetTime = int(ADDON_SETTINGS.getSetting("LastResetTime"))
        except:
            self.lastResetTime = 0

        try:
            self.lastExitTime = int(ADDON_SETTINGS.getSetting("LastExitTime"))
        except:
            self.lastExitTime = int(time.time())


    def setupList(self):
        self.readConfig()
        self.updateDialog.create(ADDON_NAME, LANGUAGE(30167))
        self.updateDialog.update(0, LANGUAGE(30167))
        self.updateDialogProgress = 0
        foundvalid = False
        makenewlists = False
        self.background = False

        if self.backgroundUpdating > 0 and self.myOverlay.isMaster == True:
            makenewlists = True

        # Go through all channels, create their arrays, and setup the new playlist
        for i in range(self.maxChannels):
            self.updateDialogProgress = i * 100 // self.enteredChannelCount
            self.updateDialog.update(self.updateDialogProgress, ''.join(LANGUAGE(30166)) % (str(i + 1)), LANGUAGE(30165))
            self.channels.append(Channel())

            # If the user pressed cancel, stop everything and exit
            if self.updateDialog.iscanceled():
                self.log('Update channels cancelled')
                self.updateDialog.close()
                return None

            self.setupChannel(i + 1, False, makenewlists, False)

            if self.channels[i].isValid:
                foundvalid = True

        if makenewlists == True:
            ADDON.setSetting('ForceChannelReset', 'false')

        if foundvalid == False and makenewlists == False:
            for i in range(self.maxChannels):
                self.updateDialogProgress = i * 100 // self.enteredChannelCount
                self.updateDialog.update(self.updateDialogProgress, ''.join(LANGUAGE(30168)) % (str(i + 1)), LANGUAGE(30165), '')
                self.setupChannel(i + 1, False, True, False)

                if self.channels[i].isValid:
                    foundvalid = True
                    break

        self.updateDialog.update(100, LANGUAGE(30170))
        self.updateDialog.close()

        return self.channels


    def log(self, msg, level = xbmc.LOGDEBUG):
        log('ChannelList: ' + msg, level)


    # Determine the maximum number of channels by opening consecutive
    # playlists until we don't find one
    # Determine the maximum number of channels by opening consecutive settings until we don't find one.
    def findMaxChannels(self):
        self.log('findMaxChannels')
        localCount = 0
        self.maxChannels = 0
        self.enteredChannelCount = 0      
        self.freshBuild = False

        for i in range(CHANNEL_LIMIT):
            chtype = 9999
            chsetting1 = ''
            chsetting2 = ''
            chsetting3 = ''
            chsetting4 = ''
            
            try:
                chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_type'))
                chsetting1 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_1')
                chsetting2 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_2')
                chsetting3 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_3')
                chsetting4 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_4')
            except Exception,e:
                pass

            if chtype == 0:
                if FileAccess.exists(xbmc.translatePath(chsetting1)):
                    localCount += 1
                    self.maxChannels = i + 1
                    self.enteredChannelCount += 1
            elif chtype <= 7:
                if len(chsetting1) > 0:
                    localCount += 1
                    self.maxChannels = i + 1
                    self.enteredChannelCount += 1
            elif chtype != 9999:
                if len(chsetting1) > 0:
                    self.maxChannels = i + 1
                    self.enteredChannelCount += 1

            if self.forceReset and (chtype != 9999):
                ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_changed', "True")

        #if local quota not met, disable quickFlip.
        if self.quickFlip == True and localCount > (self.enteredChannelCount/4):
            self.quickflipEnabled = True
        
        if self.maxChannels == 1:
            REAL_SETTINGS.setSetting("Config","%i channel"%self.enteredChannelCount)
        else:
            REAL_SETTINGS.setSetting("Config","%i channels"%self.enteredChannelCount)
        self.log('findMaxChannels, quickflipEnabled = ' + str(self.quickflipEnabled))
        self.log('findMaxChannels return ' + str(self.maxChannels))

    def sendJSON(self, command):
        self.log('sendJSON')
        data = ''
        try:
            data = xbmc.executeJSONRPC(uni(command))
        except UnicodeEncodeError:
            data = xbmc.executeJSONRPC(ascii(command))
        return uni(data)

    def setupChannel(self, channel, background = False, makenewlist = False, append = False):
        self.log('setupChannel ' + str(channel))
        returnval = False
        createlist = makenewlist
        chtype = 9999
        chsetting1 = ''
        chsetting2 = ''
        chsetting3 = ''
        chsetting4 = ''
        needsreset = False
        self.background = background
        self.settingChannel = channel

        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_type'))
            chsetting1 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_1')
            chsetting2 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_2')
            chsetting3 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_3')
            chsetting4 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_4')
        except:
            pass

        while len(self.channels) < channel:
            self.channels.append(Channel())

        if chtype == 9999:
            valid = False
        elif chtype == 0:
            if FileAccess.exists(xbmc.translatePath(chsetting1)) == True:
                valid = True
        elif chtype == 7:
            if FileAccess.exists(chsetting1) == True:
                valid = True
        elif chtype in [8,9]:
            if self.Valid_ok(chsetting2) == True:
                valid = True
        elif chtype == 10:
            if self.youtube_player != 'False':
                valid = True
        elif chtype in [11,15,16]:
            if self.Valid_ok(chsetting1) == True:
                valid = True
        else:
            if len(chsetting1) > 0:
                valid = True
        self.log('setupChannel ' + str(channel) + ', valid = ' + str(valid))
        
        if valid == False:
            self.channels[channel - 1].isValid = False
            return False
        
        self.channels[channel - 1].isSetup = True
        self.channels[channel - 1].isSetup = True
        self.channels[channel - 1].hasChanged = False
        self.channels[channel - 1].loadRules(channel)
        self.runActions(RULES_ACTION_START, channel, self.channels[channel - 1])

        try:
            needsreset = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_changed') == 'True'
        except:
            needsreset = False

        if needsreset:
           self.channels[channel - 1].isSetup = False

        self.log('setupChannel ' + str(channel) + ', needsreset = ' + str(needsreset))
        self.log('setupChannel ' + str(channel) + ', makenewlist = ' + str(makenewlist))

        # If possible, use an existing playlist
        # Don't do this if we're appending an existing channel
        # Don't load if we need to reset anyway
        if FileAccess.exists(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') and append == False and needsreset == False:
            try:
                self.channels[channel - 1].totalTimePlayed = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_time', True))
                createlist = True

                if self.channels[channel - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') == True:
                    self.channels[channel - 1].isValid = True
                    self.channels[channel - 1].fileName = CHANNELS_LOC + 'channel_' + str(channel) + '.m3u'
                    timedif = time.time() - self.lastResetTime
                    returnval = True
                    
                    if chtype == 8: 
                        # If this channel has been watched for longer than it lasts, reset the channel
                        if self.channels[channel - 1].totalTimePlayed < self.channels[channel - 1].getTotalDuration():
                            createlist = False 
       
                        if timedif >= (LIVETV_MAXPARSE - 7200) or self.channels[channel - 1].totalTimePlayed >= (LIVETV_MAXPARSE - 7200):
                            createlist = True
                    else: 
                        if self.channelResetSetting == 0:
                            # If this channel has been watched for longer than it lasts, reset the channel
                            if self.channels[channel - 1].totalTimePlayed < self.channels[channel - 1].getTotalDuration():
                                createlist = False

                        if self.channelResetSetting > 0 and self.channelResetSetting < 4:
                        
                            if self.channelResetSetting == 1 and timedif < (60 * 60 * 24):
                                createlist = False

                            if self.channelResetSetting == 2 and timedif < (60 * 60 * 24 * 7):
                                createlist = False

                            if self.channelResetSetting == 3 and timedif < (60 * 60 * 24 * 30):
                                createlist = False

                            if timedif < 0:
                                createlist = False

                        if self.channelResetSetting == 4:
                            createlist = False
            except Exception,e:
                self.log('setupChannel ' + str(channel) + ', _time failed! ' + str(e))                

        if createlist or needsreset:
            # self.clearFileListCache(chtype, channel)
            self.channels[channel - 1].isValid = False
            if makenewlist:
                try:
                    FileAccess.delete(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u')
                except:
                    self.log("Unable to delete " + 'channel_' + str(channel) + '.m3u', xbmc.LOGERROR)
                append = False

                if createlist:
                    ADDON_SETTINGS.setSetting('LastResetTime', str(int(time.time())))

        if append == False:
            if chtype in [0,1,3,5,6] and chsetting2 == str(MODE_ORDERAIRDATE):
                self.channels[channel - 1].mode = MODE_ORDERAIRDATE

            # if there is no start mode in the channel mode flags, set it to the default
            if self.channels[channel - 1].mode & MODE_STARTMODES == 0:
                if self.startMode == 0:
                    self.channels[channel - 1].mode |= MODE_RESUME
                elif self.startMode == 1:
                    self.channels[channel - 1].mode |= MODE_REALTIME
                elif self.startMode == 2:
                    self.channels[channel - 1].mode |= MODE_RANDOM


        if ((createlist or needsreset) and makenewlist) or append:
            self.log('setupChannel, Updating Channel ' + str(channel))
            
            if self.makeChannelList(channel, chtype, chsetting1, chsetting2, chsetting3, chsetting4, append) == True:
                if self.channels[channel - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') == True:
                    returnval = True
                    self.updateDialogProgress = (channel - 1) // self.enteredChannelCount
                    self.channels[channel - 1].fileName = CHANNELS_LOC + 'channel_' + str(channel) + '.m3u'
                    self.channels[channel - 1].isValid = True
                    
                    # Don't reset variables on an appending channel
                    if append == False:
                        self.channels[channel - 1].totalTimePlayed = 0
                        ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_time', '0')

                        if needsreset and self.channels[channel - 1].hasChanged == False:
                            ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_changed', 'False')
                            self.channels[channel - 1].isSetup = True

        if self.channels[channel - 1].hasChanged == True:
            ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_changed', 'True')                    

        self.runActions(RULES_ACTION_BEFORE_CLEAR, channel, self.channels[channel - 1])

        # Don't clear history when appending channels            
        if append == False and self.myOverlay.isMaster:
            self.clearPlaylistHistory(channel)
            self.updateDialogProgress = (channel - 1) // self.enteredChannelCount
            
        if append == False:
            self.runActions(RULES_ACTION_BEFORE_TIME, channel, self.channels[channel - 1])

            if self.channels[channel - 1].mode & MODE_ALWAYSPAUSE > 0:
                self.channels[channel - 1].isPaused = True

            if self.channels[channel - 1].mode & MODE_RANDOM > 0:
                self.channels[channel - 1].showTimeOffset = random.randint(0, self.channels[channel - 1].getTotalDuration())

            if self.channels[channel - 1].mode & MODE_REALTIME > 0:
                timedif = int(self.myOverlay.timeStarted) - self.lastExitTime
                self.channels[channel - 1].totalTimePlayed += timedif

            if self.channels[channel - 1].mode & MODE_RESUME > 0:
                self.channels[channel - 1].showTimeOffset = self.channels[channel - 1].totalTimePlayed
                self.channels[channel - 1].totalTimePlayed = 0

            while self.channels[channel - 1].showTimeOffset > self.channels[channel - 1].getCurrentDuration():
                self.channels[channel - 1].showTimeOffset -= self.channels[channel - 1].getCurrentDuration()
                self.channels[channel - 1].addShowPosition(1)

        if ((createlist or needsreset) and makenewlist) and returnval:
            self.runActions(RULES_ACTION_FINAL_MADE, channel, self.channels[channel - 1])
        else:
            self.runActions(RULES_ACTION_FINAL_LOADED, channel, self.channels[channel - 1])
            
        self.log('setupChannel ' + str(channel) + ', append = ' + str(append))
        self.log('setupChannel ' + str(channel) + ', createlist = ' + str(createlist))
        return returnval


    def clearPlaylistHistory(self, channel):
        self.log("clearPlaylistHistory")

        if self.channels[channel - 1].isValid == False:
            self.log("channel not valid, ignoring")
            return

        # if we actually need to clear anything
        if self.channels[channel - 1].totalTimePlayed > (60 * 60 * 24 * 2):
            try:
                fle = FileAccess.open(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u', 'w')
            except:
                self.log("clearPlaylistHistory Unable to open the smart playlist", xbmc.LOGERROR)
                return

            flewrite = uni("#EXTM3U\n")
            tottime = 0
            timeremoved = 0

            for i in range(self.channels[channel - 1].Playlist.size()):
                tottime += self.channels[channel - 1].getItemDuration(i)

                if tottime > (self.channels[channel - 1].totalTimePlayed - (60 * 60 * 12)):
                    tmpstr = str(self.channels[channel - 1].getItemDuration(i)) + ','
                    tmpstr += self.channels[channel - 1].getItemTitle(i) + "//" + self.channels[channel - 1].getItemEpisodeTitle(i) + "//" + self.channels[channel - 1].getItemDescription(i) + "//" + str(self.channels[channel - 1].getItemPlaycount(i))
                    tmpstr = uni(tmpstr[:2036])
                    tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                    tmpstr = uni(tmpstr) + uni('\n') + uni(self.channels[channel - 1].getItemFilename(i))
                    flewrite += uni("#EXTINF:") + uni(tmpstr) + uni("\n")
                else:
                    timeremoved = tottime

            fle.write(flewrite)
            fle.close()

            if timeremoved > 0:
                if self.channels[channel - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') == False:
                    self.channels[channel - 1].isValid = False
                else:
                    self.channels[channel - 1].totalTimePlayed -= timeremoved
                    # Write this now so anything sharing the playlists will get the proper info
                    ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_time', str(self.channels[channel - 1].totalTimePlayed))


    def getChannelName(self, chtype, setting1):
        self.log('getChannelName ' + str(chtype))

        if len(setting1) == 0:
            return ''

        if chtype == 0:
            return self.getSmartPlaylistName(setting1)
        elif chtype == 1 or chtype == 2 or chtype == 5 or chtype == 6:
            return setting1
        elif chtype == 3:
            return setting1 + " TV"
        elif chtype == 4:
            return setting1 + " Movies"
        elif chtype == 7:
            if setting1[-1] == '/' or setting1[-1] == '\\':
                return os.path.split(setting1[:-1])[1]
            else:
                return os.path.split(setting1)[1]

        return ''
    
    def getChtype(self, channel): 
        self.log("getChtype")
        try:
            return int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_type'))
        except:
            return 9999
        
        
    def getChname(self, channel):
        self.log("getChname")
        try:
            if int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_rulecount')) > 0:
                for i in range(RULES_PER_PAGE):         
                    try:
                        if int(ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_rule_%s_id" %str(i+1))) == 1:
                            return ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_rule_%s_opt_1" %str(i+1))
                    except:
                        pass
        except:
            pass
        return ''

    # Open the smart playlist and read the name out of it...this is the channel name
    def getSmartPlaylistName(self, fle):
        self.log('getSmartPlaylistName')
        fle = xbmc.translatePath(fle)

        try:
            xml = FileAccess.open(fle, "r")
        except:
            self.log("getSmartPlaylisyName Unable to open the smart playlist " + fle, xbmc.LOGERROR)
            return ''

        try:
            dom = parse(xml)
        except:
            self.log('getSmartPlaylistName Problem parsing playlist ' + fle, xbmc.LOGERROR)
            xml.close()
            return ''

        xml.close()

        try:
            plname = dom.getElementsByTagName('name')
            self.log('getSmartPlaylistName return ' + plname[0].childNodes[0].nodeValue)
            return plname[0].childNodes[0].nodeValue
        except:
            self.log("Unable to get the playlist name.", xbmc.LOGERROR)
            return ''
    
    # Based on a smart playlist, create a normal playlist that can actually be used by us
    def makeChannelList(self, channel, chtype, setting1, setting2, append = False):
        self.log('makeChannelList, CHANNEL: ' + str(channel))
        # self.getFileListCache(chtype, channel)
        msg = 'default' 
        fileListCHK = False
        israndom = False
        isreverse = False
        bctType = None
        fileList = []
        limit = MEDIA_LIMIT #Global

        if chtype == 7:
            fileList = self.createDirectoryPlaylist(setting1, channel, limit)
            israndom = True
        else:
            if chtype == 0:
                if FileAccess.copy(setting1, MADE_CHAN_LOC + os.path.split(setting1)[1]) == False:
                    if FileAccess.exists(MADE_CHAN_LOC + os.path.split(setting1)[1]) == False:
                        self.log("Unable to copy or find playlist " + setting1)
                        return False

                fle = MADE_CHAN_LOC + os.path.split(setting1)[1]
            else:
                fle = self.makeTypePlaylist(chtype, setting1, setting2)
                
            fle = uni(fle)

            if len(fle) == 0:
                self.log('Unable to locate the playlist for channel ' + str(channel), xbmc.LOGERROR)
                return False

            try:
                xml = FileAccess.open(fle, "r")
            except:
                self.log("makeChannelList Unable to open the smart playlist " + fle, xbmc.LOGERROR)
                return False

            try:
                dom = parse(xml)
            except:
                self.log('makeChannelList Problem parsing playlist ' + fle, xbmc.LOGERROR)
                xml.close()
                return False

            xml.close()

            if self.getSmartPlaylistType(dom) == 'mixed':
                bctType = 'mixed'
                fileList = self.buildMixedFileList(dom, channel)

            elif self.getSmartPlaylistType(dom) == 'movies':
                bctType = 'movies'
                fileList = self.buildFileList(fle, channel, limit, 'video')
            
            elif self.getSmartPlaylistType(dom) in ['episodes','tvshow']:
                bctType = 'episodes'
                fileList = self.buildFileList(fle, channel, limit, 'video')
                
            elif self.getSmartPlaylistType(dom) in ['songs','albums','artists']:
                fileList = self.buildFileList(fle, channel, limit, 'music')
                
            else:
                fileList = self.buildFileList(fle, channel, limit, 'video')
           
            try:
                order = dom.getElementsByTagName('order')

                if order[0].childNodes[0].nodeValue.lower() == 'random':
                    israndom = True
            except:
                pass

        try:
            if append == True:
                channelplaylist = FileAccess.open(CHANNELS_LOC + "channel_" + str(channel) + ".m3u", "r")
                channelplaylist.seek(0, 2)
                channelplaylist.close()
            else:
                channelplaylist = FileAccess.open(CHANNELS_LOC + "channel_" + str(channel) + ".m3u", "w")
        except:
            self.log('Unable to open the cache file ' + CHANNELS_LOC + 'channel_' + str(channel) + '.m3u', xbmc.LOGERROR)
            return False

        if append == False:
            channelplaylist.write(uni("#EXTM3U\n"))

        if israndom:
            random.shuffle(fileList)
            msg = 'random' 
        elif isreverse:
            fileList.reverse()
            msg = 'reverse'
        self.log("makeChannelList, Using Media Sort " + msg)
        self.channels[channel - 1].isRandom = israndom
        self.channels[channel - 1].isReverse = isreverse    

        if len(fileList) > self.Playlist_Limit:
            fileList = fileList[:self.Playlist_Limit]

        fileList = self.runActions(RULES_ACTION_LIST, channel, fileList)
        
        # inject BCT into filelist
        if self.incBCTs == True and bctType != None:
            fileList = self.insertBCT(chtype, channel, fileList, bctType)

        if append:
            if len(fileList) + self.channels[channel - 1].Playlist.size() > self.Playlist_Limit:
                fileList = fileList[:(self.Playlist_Limit - self.channels[channel - 1].Playlist.size())]
        else:
            if len(fileList) > self.Playlist_Limit:

                fileList = fileList[:self.Playlist_Limit]
                        
        if len(fileList) == 0:
            self.channels[channel - 1].isValid = False

        # Write each entry into the new playlist
        for string in fileList:
            channelplaylist.write(uni("#EXTINF:") + uni(string) + uni("\n"))
         
        # cleanup   
        del fileList[:]
        channelplaylist.close()
        self.log('makeChannelList return')
        return True


    def makeTypePlaylist(self, chtype, setting1, setting2):
        if chtype == 1:
            if len(self.networkList) == 0:
                self.fillTVInfo()

            return self.createNetworkPlaylist(setting1)
        elif chtype == 2:
            if len(self.studioList) == 0:
                self.fillMovieInfo()

            return self.createStudioPlaylist(setting1)
        elif chtype == 3:
            if len(self.showGenreList) == 0:
                self.fillTVInfo()

            return self.createGenrePlaylist('episodes', chtype, setting1)
        elif chtype == 4:
            if len(self.movieGenreList) == 0:
                self.fillMovieInfo()

            return self.createGenrePlaylist('movies', chtype, setting1)
        elif chtype == 5:
            if len(self.mixedGenreList) == 0:
                if len(self.showGenreList) == 0:
                    self.fillTVInfo()

                if len(self.movieGenreList) == 0:
                    self.fillMovieInfo()

                self.mixedGenreList = self.makeMixedList(self.showGenreList, self.movieGenreList)
                self.mixedGenreList.sort(key=lambda x: x.lower())

            return self.createGenreMixedPlaylist(setting1)
        elif chtype == 6:
            if len(self.showList) == 0:
                self.fillTVInfo()


            return self.createShowPlaylist(setting1, setting2)

        self.log('makeTypePlaylists invalid channel type: ' + str(chtype))
        return ''


    def createNetworkPlaylist(self, network):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'Network_' + network + '.xsp')

        try:
            fle = FileAccess.open(flename, "w")
        except:
            self.log(LANGUAGE(30034) + ' ' + flename, xbmc.LOGERROR)
            return ''

        self.writeXSPHeader(fle, "episodes", self.getChannelName(1, network))
        network = network.lower()
        added = False

        fle.write('    <rule field="tvshow" operator="is">\n')

        for i in range(len(self.showList)):
            if self.showList[i][1].lower() == network:
                theshow = self.cleanString(self.showList[i][0])
                fle.write('        <value>' + uni(theshow) + '</value>\n')
                added = True

        fle.write('    </rule>\n')

        self.writeXSPFooter(fle, 0, "random")
        fle.close()

        if added == False:
            return ''

        return flename


    def createShowPlaylist(self, show, setting2):
        order = 'random'

        try:
            setting = int(setting2)

            if setting & MODE_ORDERAIRDATE > 0:
                order = 'episode'
        except:
            pass

        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'Show_' + uni(show) + '_' + order + '.xsp')

        try:
            fle = FileAccess.open(flename, "w")
        except:
            self.log(LANGUAGE(30034) + ' ' + flename, xbmc.LOGERROR)
            return ''

        self.writeXSPHeader(fle, 'episodes', self.getChannelName(6, show))
        show = self.cleanString(show)
        fle.write('    <rule field="tvshow" operator="is">\n')
        fle.write('        <value>' + uni(show) + '</value>\n')
        fle.write('    </rule>\n')
        self.writeXSPFooter(fle, 0, order)
        fle.close()
        return flename



    def createGenreMixedPlaylist(self, genre):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'Mixed_' + genre + '.xsp')

        try:
            fle = FileAccess.open(flename, "w")
        except:
            self.log(LANGUAGE(30034) + ' ' + flename, xbmc.LOGERROR)
            return ''

        epname = os.path.basename(self.createGenrePlaylist('episodes', 3, genre))
        moname = os.path.basename(self.createGenrePlaylist('movies', 4, genre))
        self.writeXSPHeader(fle, 'mixed', self.getChannelName(5, genre))
        fle.write('    <rule field="playlist" operator="is">' + epname + '</rule>\n')
        fle.write('    <rule field="playlist" operator="is">' + moname + '</rule>\n')
        self.writeXSPFooter(fle, 0, "random")
        fle.close()
        return flename


    def createGenrePlaylist(self, pltype, chtype, genre):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + pltype + '_' + genre + '.xsp')
        debug('genre flename = ', flename)
        try:
            fle = FileAccess.open(flename, "w")
        except:
            self.log(LANGUAGE(30034) + ' ' + flename, xbmc.LOGERROR)
            return ''

        self.writeXSPHeader(fle, pltype, self.getChannelName(chtype, genre))
        genre = self.cleanString(genre)
        fle.write('    <rule field="genre" operator="is">\n')
        fle.write('        <value>' + uni(genre) + '</value>\n')
        fle.write('    </rule>\n')
        self.writeXSPFooter(fle, 0, "random")
        fle.close()
        return flename

    def createStudioPlaylist(self, studio):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'Studio_' + studio + '.xsp')

        try:
            fle = FileAccess.open(flename, "w")
        except:
            self.log(LANGUAGE(30034) + ' ' + flename, xbmc.LOGERROR)
            return ''

        self.writeXSPHeader(fle, "movies", self.getChannelName(2, studio))
        studio = self.cleanString(studio)
        fle.write('    <rule field="studio" operator="is">\n')
        fle.write('        <value>' + uni(studio) + '</value>\n')
        fle.write('    </rule>\n')
        self.writeXSPFooter(fle, 0, "random")
        fle.close()
        return flename


    def createDirectoryPlaylist(self, setting1, setting3, setting4, channel):
        self.log("createDirectoryPlaylist " + setting1)
        fileList = []
        LocalLST = []
        LocalFLE = ''
        filecount = 0

        if not setting1.endswith('/'):
            setting1 = os.path.join(setting1,'')
        LocalLST = self.walk(setting1)

        for i in range(len(LocalLST)):         
            if self.threadPause() == False:
                del fileList[:]
                break
        
            LocalFLE = (LocalLST[i])
            duration = self.getDuration(LocalFLE)

            if duration > 0:
               filecount += 1
               title = (os.path.split(LocalFLE)[1])
               title = os.path.splitext(title)[0].replace('.', ' ')
               description = LocalFLE.replace('//','/').replace('/','\\')
               GenreLiveID = ['Unknown', 'other', 0, 0, False, 1, 'NR', False, False, 0.0, 0]
               tmpstr = self.makeTMPSTR(duration, title, 0, 'Directory Video', description, GenreLiveID, LocalFLE)
               fileList.append(tmpstr)
                
               if filecount >= channel:
                   break

        if filecount == 0:
            self.log('Unable to access Videos files in ' + setting1)
        
        # cleanup   
        del LocalLST[:]
        return fileList


    def writeXSPHeader(self, fle, pltype, plname):
        fle.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')
        fle.write('<smartplaylist type="' + pltype + '">\n')
        plname = self.cleanString(plname)
        fle.write('    <name>' + plname + '</name>\n')
        fle.write('    <match>one</match>\n')


    def writeXSPFooter(self, fle, limit, order):
        if self.mediaLimit > 0:
            fle.write('    <limit>' + str(self.mediaLimit) + '</limit>\n')

        fle.write('    <order direction="ascending">' + order + '</order>\n')
        fle.write('</smartplaylist>\n')


    def cleanString(self, string):
        newstr = uni(string)
        newstr = newstr.replace('&', '&amp;')
        newstr = newstr.replace('>', '&gt;')
        newstr = newstr.replace('<', '&lt;')
        return uni(newstr)


    def fillTVInfo(self, sortbycount = False):
        self.log("fillTVInfo")
        json_query = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties":["studio", "genre"]}, "id": 1}'

        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, ''.join(LANGUAGE(30168)) % (str(self.settingChannel)), LANGUAGE(30172), LANGUAGE(30177))

        json_folder_detail = self.sendJSON(json_query)
        detail = re.compile("{(.*?)}", re.DOTALL).findall(json_folder_detail)

        for f in detail:
            if self.threadPause() == False:
                del self.networkList[:]
                del self.showList[:]
                del self.showGenreList[:]
                return

            match = re.search('"studio" *: *\[(.*?)\]', f)

            network = ''

            if match:
                network = (match.group(1).split(','))[0]
                network = network.strip('"').strip()
                found = False

                for item in range(len(self.networkList)):
                    if self.threadPause() == False:
                        del self.networkList[:]
                        del self.showList[:]
                        del self.showGenreList[:]
                        return

                    itm = self.networkList[item]

                    if sortbycount:
                        itm = itm[0]

                    if itm.lower() == network.lower():
                        found = True

                        if sortbycount:
                            self.networkList[item][1] += 1

                        break

                if found == False and len(network) > 0:
                    if sortbycount:
                        self.networkList.append([network, 1])
                    else:
                        self.networkList.append(network)

            match = re.search('"label" *: *"(.*?)",', f)

            if match:
                show = match.group(1).strip()
                self.showList.append([show, network])

            match = re.search('"genre" *: *\[(.*?)\]', f)

            if match:
                genres = match.group(1).split(',')

                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip('"').strip()

                    for g in range(len(self.showGenreList)):
                        if self.threadPause() == False:
                            del self.networkList[:]
                            del self.showList[:]
                            del self.showGenreList[:]
                            return

                        itm = self.showGenreList[g]

                        if sortbycount:
                            itm = itm[0]

                        if curgenre == itm.lower():
                            found = True

                            if sortbycount:
                                self.showGenreList[g][1] += 1

                            break

                    if found == False:
                        if sortbycount:
                            self.showGenreList.append([genre.strip('"').strip(), 1])
                        else:
                            self.showGenreList.append(genre.strip('"').strip())

        if sortbycount:
            self.networkList.sort(key=lambda x: x[1], reverse = True)
            self.showGenreList.sort(key=lambda x: x[1], reverse = True)
        else:
            self.networkList.sort(key=lambda x: x.lower())
            self.showGenreList.sort(key=lambda x: x.lower())

        if (len(self.showList) == 0) and (len(self.showGenreList) == 0) and (len(self.networkList) == 0):
            self.log(json_folder_detail)

        self.log("found shows " + str(self.showList))
        self.log("found genres " + str(self.showGenreList))
        self.log("fillTVInfo return " + str(self.networkList))


    def fillMovieInfo(self, sortbycount = False):
        self.log("fillMovieInfo")
        studioList = []
        json_query = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"properties":["studio", "genre"]}, "id": 1}'

        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, ''.join(LANGUAGE(30168)) % (str(self.settingChannel)), LANGUAGE(30172), LANGUAGE(30178))

        json_folder_detail = self.sendJSON(json_query)
        detail = re.compile("{(.*?)}", re.DOTALL).findall(json_folder_detail)

        for f in detail:
            if self.threadPause() == False:
                del self.movieGenreList[:]
                del self.studioList[:]
                del studioList[:]
                break

            match = re.search('"genre" *: *\[(.*?)\]', f)

            if match:
                genres = match.group(1).split(',')

                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip('"').strip()

                    for g in range(len(self.movieGenreList)):
                        itm = self.movieGenreList[g]

                        if sortbycount:
                            itm = itm[0]

                        if curgenre == itm.lower():
                            found = True

                            if sortbycount:
                                self.movieGenreList[g][1] += 1

                            break

                    if found == False:
                        if sortbycount:
                            self.movieGenreList.append([genre.strip('"').strip(), 1])
                        else:
                            self.movieGenreList.append(genre.strip('"').strip())

            match = re.search('"studio" *: *\[(.*?)\]', f)

            if match:
                studios = match.group(1).split(',')

                for studio in studios:
                    curstudio = studio.strip('"').strip()
                    found = False

                    for i in range(len(studioList)):
                        if studioList[i][0].lower() == curstudio.lower():
                            studioList[i][1] += 1
                            found = True
                            break

                    if found == False and len(curstudio) > 0:
                        studioList.append([curstudio, 1])

        maxcount = 0

        for i in range(len(studioList)):
            if studioList[i][1] > maxcount:
                maxcount = studioList[i][1]

        bestmatch = 1
        lastmatch = 1000
        counteditems = 0

        for i in range(maxcount, 0, -1):
            itemcount = 0

            for j in range(len(studioList)):
                if studioList[j][1] == i:
                    itemcount += 1

            if abs(itemcount + counteditems - 8) < abs(lastmatch - 8):
                bestmatch = i
                lastmatch = itemcount

            counteditems += itemcount

        if sortbycount:
            studioList.sort(key=lambda x: x[1], reverse=True)
            self.movieGenreList.sort(key=lambda x: x[1], reverse=True)
        else:
            studioList.sort(key=lambda x: x[0].lower())
            self.movieGenreList.sort(key=lambda x: x.lower())

        for i in range(len(studioList)):
            if studioList[i][1] >= bestmatch:
                if sortbycount:
                    self.studioList.append([studioList[i][0], studioList[i][1]])
                else:
                    self.studioList.append(studioList[i][0])

        if (len(self.movieGenreList) == 0) and (len(self.studioList) == 0):
            self.log(json_folder_detail)

        self.log("found genres " + str(self.movieGenreList))
        self.log("fillMovieInfo return " + str(self.studioList))


    def makeMixedList(self, list1, list2):
        self.log("makeMixedList")
        newlist = []

        for item in list1:
            curitem = item.lower()

            for a in list2:
                if curitem == a.lower():
                    newlist.append(item)
                    break

        self.log("makeMixedList return " + str(newlist))
        return newlist


    def buildFileList(self, dir_name, channel, chtype):
        self.log("buildFileList")
        fileList = []
        seasoneplist = []
        filecount = 0
        
        #sending the xsp playlist path to jason, which is what generates the file data to be put into the m3u playlists        
        json_query = '{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "video", "properties":["duration","runtime","showtitle","plot","plotoutline","season","episode","year","lastplayed","playcount","resume","artist"]}, "id": 1}' % (self.escapeDirJSON(dir_name))

        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, ''.join(LANGUAGE(30168)) % (str(self.settingChannel)), LANGUAGE(30172), LANGUAGE(30179))

        json_folder_detail = self.sendJSON(json_query)
        json_folder_detail = json_folder_detail.replace('"id":1,"jsonrpc":"2.0"','')
        self.log(json_folder_detail)

        #next two lines accounting for how JSON returns resume info; stripping it down to just get the position
        json_folder_detail = json_folder_detail.replace('"resume":{', '')
        json_folder_detail = re.sub(r',"total":.+?}', '', json_folder_detail)
        file_detail = re.compile("{(.*?)}", re.DOTALL).findall(json_folder_detail)
        for f in file_detail:
            if self.threadPause() == False:
                del fileList[:]
                break

            f = uni(f)
            match = re.search('"file" *: *"(.*?)",', f)

            if match:
                if(match.group(1).endswith("/") or match.group(1).endswith("\\")):
                    fileList.extend(self.buildFileList(match.group(1), channel, chtype))
                else:
                    f = self.runActions(RULES_ACTION_JSON, channel, f)
                    duration = re.search('"duration" *: *([0-9]*?),', f)
                    try:
                        dur = int(duration.group(1))
                    except:
                        dur = 0

                    if dur == 0:
                        duration = re.search('"runtime" *: *([0-9]*?),', f)
                        try:
                            dur = int(duration.group(1))
                        except:
                            dur = 0

                    if dur == 0:
                        try:
                            dur = self.videoParser.getVideoLength(uni(match.group(1)).replace("\\\\", "\\"))
                        except:
                            dur = 0

                    if dur == 0:
                        self.log('file_detail = ' + str(file_detail))
                        self.log("Failed to find duration for video " + str(f), xbmc.LOGWARNING)
                        if self.FailWarning:
                            if self.AlreadyWarned == False:
                                assetMsg = "Possible Failure Adding Video.  Check log."
                                xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % ("PseudoTV BuildFileList", assetMsg, NOTIFICATION_DISPLAY_TIME * 500, ICON))
                                self.AlreadyWarned = True
                        if self.AssignDuration:
                            self.log("Setting default duration for " + str(f), xbmc.LOGWARNING)
                            dur = self.AssignedDuration
                    try:
                        if dur > 0:
                            filecount += 1

                            if self.background == False:
                                if filecount == 1:
                                    self.updateDialog.update(self.updateDialogProgress, ''.join(LANGUAGE(30168)) % (str(self.settingChannel)), LANGUAGE(30172), ''.join(LANGUAGE(30175)) % (str(filecount)))
                                else:
                                    self.updateDialog.update(self.updateDialogProgress, ''.join(LANGUAGE(30168)) % (str(self.settingChannel)), LANGUAGE(30172), ''.join(LANGUAGE(30176)) % (str(filecount)))

                            tmpstr = str(dur) + ','
                            title = re.search('"label" *: *"(.*?)"', f)
                            showtitle = re.search('"showtitle" *: *"(.*?)"', f)
                            
                            plot = re.search('"plot" *: *"(.*?)","', f)
                            plotoutline = re.search('"plotoutline" *: *"(.*?)","', f)
                            artist = re.search('"artist" *: *\[(.*?)\]',f)
                            
                            if plotoutline is None:
                                plotoutlineCandidate = ""
                            else:
                                plotoutlineCandidate = plotoutline.group(1)
                            
                            if plot is None:
                                plotCandidate = ""
                            else:
                                plotCandidate = plot.group(1)
                           
                            if plotCandidate is None:
                                plotCandidate = ""
                            
                            if len(plotoutlineCandidate) > 0:
                                theplot = plotoutlineCandidate
                            elif len(plotoutlineCandidate) == 0 and len(plotCandidate) > 0:
                                theplot = plotCandidate
                            else:
                                theplot = LANGUAGE(30023)

                            theplot = theplot.replace('//','')

                            #values needed to reset watched status should be captured whether or not the setting is enabled, in case user changes setting later
                            playcount = re.search('"playcount" *: *([0-9]+)', f)
                            lastplayed = re.search('"lastplayed" *: *"(.*?)"', f)
                            resumePosition = re.search('"position" *: *([0-9]+\.[0-9]),', f)
                            id = re.search('"id" *: *([0-9]+)', f)

                            if playcount != None:
                                playcountval = playcount.group(1)
                            
                            if resumePosition != None:
                                resumePositionval = resumePosition.group(1)
                                
                            if lastplayed != None:
                                lastplayedval = lastplayed.group(1)
                            
                            if id != None:
                                idval = id.group(1)
                                
                            if artist != None:
                                artist = artist.group(1)
                                artist = artist.strip('"')
                                  
                            # This is a TV show
                            if showtitle != None and len(showtitle.group(1)) > 0:
                                if title != None:
                                    eptitle = title.group(1)
                                
                                if "." in eptitle:
                                    param, eptitle = eptitle.split(". ", 1)
                                
                                season = re.search('"season" *: *(.*?),', f)
                                episode = re.search('"episode" *: *(.*?),', f)
                                seasonval = season.group(1)
                                epval = episode.group(1).zfill(2)
                                sxexx = (' ({})'.format(seasonval + 'x' + epval))

                                if str(channel) in self.UseEpisodeTitleKeepShowTitle:
                                    newShowTitle = eptitle
                                    #if single show, put the episode title in the show title, and then clear it from episode
                                    if epval != None and len(episode.group(1)) > 0 and self.YearEpInfo == 'false':
                                        eptitle = showtitle.group(1) + sxexx
                                    elif epval != None and len(episode.group(1)) > 0 and self.YearEpInfo == 'true':
                                        eptitle = showtitle.group(1)
                                    tmpstr += newShowTitle + "//" + eptitle + "//" + theplot
                                elif str(channel) in self.UseEpisodeTitleHideTitle:
                                    newShowTitle = eptitle
                                    self.log('newShowTitle = ' + str(newShowTitle))
                                    #if single show, put the episode title in the show title, and then clear it from episode
                                    if epval != None and len(episode.group(1)) > 0 and self.YearEpInfo == 'false':
                                        eptitle = sxexx
                                    elif epval != None and len(episode.group(1)) > 0 and self.YearEpInfo == 'true':
                                        eptitle = ""
                                    tmpstr += newShowTitle + "//" + eptitle + "//" + theplot
                                else: 
                                    eptitle = ('"{}"'.format(eptitle))
                                    self.log('eptitle = ' + str(eptitle))
                                    if epval != None and len(episode.group(1)) > 0 and self.YearEpInfo == 'false':
                                        eptitle = eptitle + sxexx
                                    tmpstr += showtitle.group(1) + "//" + eptitle + "//" + theplot
                            else:
                                # This is a movie or music video
                                if showtitle == None or len(showtitle.group(1)) == 0:
                                    #This is a music video
                                    if artist != None and len(artist) > 0:
                                         tmpstr += artist + " - " + title.group(1)
                                    else:
                                        tmpstr += title.group(1)
                                    
                                    years = re.search('"year" *: *([\d.]*\d+)', f)
                                    year = ('({})'.format(years.group(1)))

                                    if len(years.group(1)) > 0 and self.YearEpInfo == 'false':
                                        tmpstr += "//" + year + "//" + theplot
                                    else:
                                        tmpstr += "//" + "//" + theplot

                            #cutting off extremely long plots
                            tmpstr = uni(tmpstr[:1990])
                            
                            tmpstr += "//"  + playcountval
                            tmpstr += "//"  + resumePositionval
                            tmpstr += "//"  + lastplayedval
                            if artist != None and len(artist) > 0:
                               tmpstr += "//"  + idval + "MTV"
                            else:
                                tmpstr += "//"  + idval

                            tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                            tmpstr = tmpstr + '\n' + match.group(1).replace("\\\\", "\\")

                            if self.channels[channel - 1].mode & MODE_ORDERAIRDATE > 0:
                                seasoneplist.append([seasonval, epval, tmpstr])
                            else:
                                fileList.append(tmpstr)
                    except:
                        self.log('error in the try/except for build file (probably just excludes from Dont Play Watched?)' + str(match.group(1)))
                        pass
            else:
                continue

        if self.channels[channel - 1].mode & MODE_ORDERAIRDATE > 0:
            
            seasoneplist.sort(key=lambda seep: int(seep[1]))
            seasoneplist.sort(key=lambda seep: int(seep[0]))

            for seepitem in seasoneplist:
                fileList.append(seepitem[2])
        
        if filecount == 0:
            self.log(json_folder_detail)

        self.log("buildFileList return")
        return fileList


    def buildMixedFileList(self, dom1, channel):
        fileList = []
        self.log('buildMixedFileList')

        try:
            rules = dom1.getElementsByTagName('rule')
            order = dom1.getElementsByTagName('order')
        except:
            self.log('buildMixedFileList Problem parsing playlist ' + filename, xbmc.LOGERROR)
            xml.close()
            return fileList

        for rule in rules:
            rulename = rule.childNodes[0].nodeValue

            if FileAccess.exists(xbmc.translatePath('special://profile/playlists/video/') + rulename):
                FileAccess.copy(xbmc.translatePath('special://profile/playlists/video/') + rulename, MADE_CHAN_LOC + rulename)
                fileList.extend(self.buildFileList(MADE_CHAN_LOC + rulename, channel, 5))
            else:
                fileList.extend(self.buildFileList(GEN_CHAN_LOC + rulename, channel, 5))

        self.log("buildMixedFileList returning")
        return fileList


    # Run rules for a channel
    def runActions(self, action, channel, parameter):
        self.log("runActions " + str(action) + " on channel " + str(channel))
        if channel < 1:
            return

        self.runningActionChannel = channel
        index = 0

        for rule in self.channels[channel - 1].ruleList:
            if rule.actions & action > 0:
                self.runningActionId = index

                if self.background == False:
                    self.updateDialog.update(self.updateDialogProgress, ''.join(LANGUAGE(30168)) % (str(self.settingChannel)), ''.join(LANGUAGE(30180)) % (str(index + 1)), '')

                parameter = rule.runAction(action, self, parameter)

            index += 1

        self.runningActionChannel = 0
        self.runningActionId = 0
        return parameter


    def threadPause(self):
        if threading.activeCount() > 1:
            while self.threadPaused == True and self.myOverlay.isExiting == False:
                time.sleep(self.sleepTime)

            # This will fail when using config.py
            try:
                if self.myOverlay.isExiting == True:
                    self.log("IsExiting")
                    return False
            except:
                pass

        return True


    def escapeDirJSON(self, dir_name):
        mydir = uni(dir_name)

        if (mydir.find(":")):
            mydir = mydir.replace("\\", "\\\\")

        return mydir


    def getSmartPlaylistType(self, dom):
        self.log('getSmartPlaylistType')

        try:
            pltype = dom.getElementsByTagName('smartplaylist')
            return pltype[0].attributes['type'].value
        except:
            self.log("Unable to get the playlist type.", xbmc.LOGERROR)
            return ''

    def insertBCT(self, chtype, channel, fileList, type):
        self.log("insertBCT, channel = " + str(channel))
        newFileList = []
        try:
            chname = self.getChannelName(chtype, channel, ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_1'))
            #Bumpers & Ratings
            BumperLST = []
            BumpersType = REAL_SETTINGS.getSetting("bumpers")      
            if BumpersType != "0" and type != 'movies': 
                BumperLST = self.getBumperList(BumpersType, chname)

                if REAL_SETTINGS.getSetting('bumperratings') == 'true':
                    fileList = self.getRatingList(chtype, chname, channel, fileList)

                # #3D, insert "put glasses on" for 3D and use 3D ratings if enabled. todo
                # if BumpersType!= "0" and type == 'movies' and REAL_SETTINGS.getSetting('bumper3d') == 'true':
                    # fileList = self.get3DList(chtype, chname, channel, fileList)
                    
            #Commercial
            CommercialLST = []
            CommercialsType = REAL_SETTINGS.getSetting("commercials") 
            if CommercialsType != '0' and type != 'movies':
                CommercialLST = self.getCommercialList(CommercialsType, chname)

            #Trailers
            try:
                if type == 'movies' and REAL_SETTINGS.getSetting('Movietrailers') == 'false':
                    raise Exception()
                    
                TrailerLST = []
                TrailersType = REAL_SETTINGS.getSetting("trailers")
                if TrailersType != '0':
                    TrailerLST = self.getTrailerList(chtype, chname)
            except:
                pass

            # Inject BCTs into filelist          
            for i in range(len(fileList)):
                newFileList.append(fileList[i])
                if len(BumperLST) > 0:  
                    random.shuffle(BumperLST)              
                    for n in range(int(REAL_SETTINGS.getSetting("numbumpers")) + 1):
                        newFileList.append(random.choice(BumperLST))#random fill

                if len(CommercialLST) > 0:
                    random.shuffle(CommercialLST)                
                    for n in range(int(REAL_SETTINGS.getSetting("numcommercials")) + 1):
                        newFileList.append(random.choice(CommercialLST))#random fill
                        
                if len(TrailerLST) > 0:
                    random.shuffle(TrailerLST)                
                    for n in range(int(REAL_SETTINGS.getSetting("numtrailers")) + 1):
                        newFileList.append(random.choice(TrailerLST))#random fill
    #random.shuffle(newFileList)
                
            # cleanup   
            del fileList[:]
            del BumperLST[:]
            del CommercialLST[:]
            del TrailerLST[:]
            return newFileList
        except:
            del newFileList[:]
            return fileList
        
        
    def getBumperList(self, BumpersType, chname):
        self.log("getBumperList")
        BumperLST = []
        BumperTMPstrLST = []
        
        #Local
        if BumpersType == "1":  
            self.log("getBumperList, Local - " + chname)
            PATH = xbmc.translatePath(os.path.join(REAL_SETTINGS.getSetting('bumpersfolder'),chname,''))
            self.log("getBumperList, Local - PATH = " + PATH)
            BumperLST.extend(self.createDirectoryPlaylist(PATH, 100, 1, 100)) 
        #Internet
        elif BumpersType == "2":
            self.log("getBumperList - Internet - " + chname)
            Bumper_List = 'http://raw.github.com/PseudoTV/PseudoTV_Lists/master/bumpers.ini'
            linesLST = read_url_cached(Bumper_List, return_type='readlines')
            for i in range(len(Bumper_List)):                 
                try:                 
                    ChannelName,BumperNumber,BumperSourceID = (str(linesLST[i]).replace('\n','').replace('\r','').replace('\t','')).split('|')
                    BumperSource,BumperID = BumperSourceID.split('_')
                    
                    if chname.lower() == ChannelName.lower():
                        if BumperSource.lower() == 'vimeo':
                            if self.vimeo_player != 'False':
                                GenreLiveID = ['Bumper', 'bct', 0, 0 , False, 1, 'NR', False, False, 0.0, 0]
                                BumperTMPstrLST.append(self.makeTMPSTR(self.getVimeoMeta(BumperID)[2], chname, 0, 'Bumper', 'Bumper', GenreLiveID, self.vimeo_player + BumperID))
                                
                        elif BumperSource.lower() == 'youtube':
                            if self.youtube_player != 'False':           
                                GenreLiveID = ['Bumper', 'bct', 0, 0 , False, 1, 'NR', False, False, 0.0, 0]
                                BumperTMPstrLST.append(self.makeTMPSTR(self.getYoutubeDuration(BumperID), chname, 0, 'Bumper', 'Bumper', GenreLiveID, self.youtube_player + BumperID, includeMeta=False))        
                except: 
                    pass
            BumperLST.extend(BumperTMPstrLST)      
        # cleanup   
        del BumperTMPstrLST[:]
        return random.shuffle(BumperLST)    
    

    def getRatingList(self, chtype, chname, channel, fileList, ddd=False):
        self.log("getRatingList")
        newFileList = []
        Ratings = (['NR','qlRaA8tAfc0'],['R','s0UuXOKjH-w'],['NC-17','Cp40pL0OaiY'],['PG-13','lSg2vT5qQAQ'],['PG','oKrzhhKowlY'],['G','QTKEIFyT4tk'],['18','g6GjgxMtaLA'],['16','zhB_xhL_BXk'],['12','o7_AGpPMHIs'],['6','XAlKSm8D76M'],['0','_YTMglW0yk'])
        Ratings_3D = [] # todo 3d ratings
                       
        if self.youtube_player != 'False': 
            for i in range(len(fileList)):
                if self.threadPause() == False:
                    del newFileList[:]
                    break  
                try:
                    newFileList.append(fileList[i])
                    lineLST = (fileList[i]).split('movie|')[1]
                    mpaa = (lineLST.split('\n')[0]).split('|')[4]
                    
                    for i in range(len(Ratings)):
                        ID = 'qlRaA8tAfc0'
                        rating = Ratings[i]        
                        if mpaa.lower() == rating[0].lower():
                            ID = rating[1]
                            break

                    GenreLiveID = ['Rating', 'bct', 0, 0, False, 1, mpaa, False, False, 0.0, 0]
                    newFileList.append(self.makeTMPSTR(self.getYoutubeDuration(ID), chname, 0, 'Rating', 'Rating', GenreLiveID, self.youtube_player + ID, includeMeta=False))
                except:
                    pass
            # cleanup   
            del fileList[:]
            return newFileList
        else:
            return fileList
        
    
    def getCommercialList(self, CommercialsType, chname):  
        self.log("getCommercialList") 
        CommercialLST = []       

        #Local
        if CommercialsType == '1':
            self.log("getCommercialList, Local - " + chname)
            PATH = xbmc.translatePath(os.path.join(PATH,''))
            self.log("getCommercialList, Local - PATH = " + PATH)
            CommercialLST.extend(self.createDirectoryPlaylist(PATH, 100, 1, 100)) 
                    
        #Youtube
        elif CommercialsType == '2':   
            #Youtube - As Seen On TV
            if REAL_SETTINGS.getSetting('AsSeenOn') == 'true':
                self.log("getCommercialList, AsSeenOn") 
                CommercialLST.extend(self.createYoutubeFilelist('PL_ikfJ-FJg77ioZ9nPuhJxuMe9GKu7plT|PL_ikfJ-FJg774gky7eu8DroAqCR_COS79|PL_ikfJ-FJg75N3Gn6DjL0ZArAcfcGigLY|PL_ikfJ-FJg765O5ppOPGTpQht1LwXmck4|PL_ikfJ-FJg75wIMSXOTdq0oMKm63ucQ_H|PL_ikfJ-FJg77yht1Z6Xembod33QKUtI2Y|PL_ikfJ-FJg77PW8AJ3yk5HboSwWatCg5Z|PL_ikfJ-FJg75v4dTW6P0m4cwEE4-Oae-3|PL_ikfJ-FJg76zae4z0TX2K4i_l5Gg-Flp|PL_ikfJ-FJg74_gFvBqCfDk2E0YN8SsGS8|PL_ikfJ-FJg758W7GVeTVZ4aBAcCBda63J', '7', '200', '1', '200'))
            self.log("getCommercialList, Youtube") 
            CommercialLST.extend(self.createYoutubeFilelist(REAL_SETTINGS.getSetting('commercialschannel'), '2', '200', '2', '200'))
        
        #Internet
        elif CommercialsType == '3':
            self.log("getCommercialList, Internet") 
            CommercialLST.extend(self.InternetCommercial())
        return random.shuffle(CommercialLST) 
   
        
    def InternetCommercial(self):
        self.log("InternetCommercial")
        CommercialLST = []
        #todo add plugin parsing...
        if len(CommercialLST) > 0:
            random.shuffle(CommercialLST)
        return CommercialLST       

    
    def getTrailerList(self, chtype, chname):
        self.log("getTrailerList")
        TrailerLST = [] 
        TrailerTMPstrLST = []
        GenreChtype = False
        if chtype == '3' or chtype == '4' or chtype == '5':
            GenreChtype = True

        #Local
        if TrailersType == '1': 
            PATH = xbmc.translatePath(os.path.join(REAL_SETTINGS.getSetting('trailersfolder'),''))
            self.log("getTrailerList, Local - PATH = " + PATH)
            
            if FileAccess.exists(PATH):
                LocalFLE = ''
                LocalTrailer = ''
                LocalLST = self.walk(PATH)        
                for i in range(len(LocalLST)): 
                    try:   
                        LocalFLE = LocalLST[i]
                        if '-trailer' in LocalFLE:
                            duration = self.getDuration(LocalFLE)
                            if duration > 0:
                                GenreLiveID = ['Trailer', 'bct', 0, 0, False, 1, 'NR', False, False, 0.0, 0]
                                TrailerTMPstrLST.append(self.makeTMPSTR(duration, chname, 0, 'Trailer', 'Trailer', GenreLiveID, LocalFLE, includeMeta=False))   
                        TrailerLST.extend(TrailerTMPstrLST)                                
                    except Exception,e:
                        self.log("getTrailerList failed! " + str(e), xbmc.LOGERROR)

        #Kodi Library
        # if TrailersType == '2':
            # self.log("getTrailerList, Kodi Library")
            # json_query = ('{"jsonrpc":"2.0","method":"VideoLibrary.GetMovies","params":{"properties":["genre","trailer","runtime"]}, "id": 1}')
            # json_detail = self.sendJSON(json_query)
            
            # if REAL_SETTINGS.getSetting('trailersgenre') == 'true' and GenreChtype == True:
                # JsonLST = ascii(json_detail.split("},{"))
                # match = [s for s in JsonLST if chname in s]
                
                # for i in range(len(match)):    
                    # self.setBackground("Initializing: Loading Channel " + str(self.settingChannel),string2="adding Library Genre Trailers")
                    # duration = 120
                    # json = (match[i])
                    # trailer = json.split(',"trailer":"',1)[-1]
                    # if ')"' in trailer:
                        # trailer = trailer.split(')"')[0]
                    # else:
                        # trailer = trailer[:-1]
                    
                    # if trailer != '' or trailer != None or trailer != '"}]}':
                        # if 'http://www.youtube.com/watch?hd=1&v=' in trailer:
                            # trailer = trailer.replace("http://www.youtube.com/watch?hd=1&v=", self.youtube_player).replace("http://www.youtube.com/watch?v=", self.youtube_player)
                        # JsonTrailer = (str(duration) + ',' + trailer)
                        # if JsonTrailer != '120,':
                            # JsonTrailerLST.append(JsonTrailer)
                # TrailerLST.extend(JsonTrailerLST)
            
            # if self.youtube_player != 'False':

                # try:
                    # self.log('getTrailerList, json_detail using cache')


                    # else:
                        # JsonLST = (json_detail.split("},{"))
                        # match = [s for s in JsonLST if 'trailer' in s]
                        # for i in range(len(match)):                  
                            # self.setBackground("Initializing: Loading Channel " + str(self.settingChannel),string2="adding Library Trailers")
                            # duration = 120
                            # json = (match[i])
                            # trailer = json.split(',"trailer":"',1)[-1]
                            # if ')"' in trailer:
                                # trailer = trailer.split(')"')[0]
                            # else:
                                # trailer = trailer[:-1]
                            # if trailer != '' or trailer != None or trailer != '"}]}':
                                # if 'http://www.youtube.com/watch?hd=1&v=' in trailer:
                                    # trailer = trailer.replace("http://www.youtube.com/watch?hd=1&v=", self.youtube_player).replace("http://www.youtube.com/watch?v=", self.youtube_player)
                                # JsonTrailer = (str(duration) + ',' + trailer)
                                # if JsonTrailer != '120,':
                                    # JsonTrailerLST.append(JsonTrailer)
                        # TrailerLST.extend(JsonTrailerLST)     
                # except Exception,e:
                    # self.log("getTrailerList failed! " + str(e), xbmc.LOGERROR)
                    
        # #Youtube
        # if TrailersType == '3':
            # self.log("getTrailerList, Youtube")
            # try:
                # YoutubeLST = self.createYoutubeFilelist(REAL_SETTINGS.getSetting('trailerschannel'), '2', '200', '2', '200')
                
                # for i in range(len(YoutubeLST)):    
                    # self.setBackground("Initializing: Loading Channel " + str(self.settingChannel),string2="adding Youtube Trailers")
                    # Youtube = YoutubeLST[i]
                    # duration = Youtube.split(',')[0]
                    # trailer = Youtube.split('\n', 1)[-1]
                    
                    # if trailer != '' or trailer != None:
                        # YoutubeTrailer = (str(duration) + ',' + trailer)
                        # YoutubeTrailerLST.append(YoutubeTrailer)
                # TrailerLST.extend(YoutubeTrailerLST)
            # except Exception,e:
                # self.log("getTrailerList failed! " + str(e), xbmc.LOGERROR)
                
        # #Internet
        # if TrailersType == '4':
            # self.log("getTrailerList, Internet")
            # try:   
                # self.setBackground("Initializing: Loading Channel " + str(self.settingChannel),string2="adding Internet Trailers")
                # TrailerLST = self.InternetTrailer()
            # except Exception,e:
                # self.log("getTrailerList failed! " + str(e), xbmc.LOGERROR)
        # cleanup   
        del LocalTrailerLST[:]
        del JsonTrailerLST[:]
        del YoutubeTrailerLST[:]
        return TrailerLST       


    def InternetTrailer(self, Cinema=False):
        self.log("InternetTrailer, Cinema = " + str(Cinema))
        TrailerLST = []
        duration = 0
        TrailersCount = 0
        
        if Cinema == 1:
            TRes = '720p'
            Ttype = 'coming_soon'
            Tlimit = 90
        elif Cinema == 2:
            TRes = '720p'
            Ttype = 'opening'
            Tlimit = 90
        else:
            TResNum = {}
            TResNum['0'] = '480p'
            TResNum['1'] = '720p'
            TResNum['2'] = '1080p'
            TRes = (TResNum[REAL_SETTINGS.getSetting('trailersResolution')])

            Ttypes = {}
            Ttypes['0'] = 'latest'
            Ttypes['1'] = 'most_watched'
            Ttypes['2'] = 'coming_soon'
            Ttype = (Ttypes[REAL_SETTINGS.getSetting('trailersHDnetType')])

            T_Limit = [15,30,90,180,270,360]
            Tlimit = T_Limit[int(REAL_SETTINGS.getSetting('trailersTitleLimit'))]
        
        try:
            InternetTrailersLST1 = []
            limit = Tlimit
            loop = int(limit/15)
            global page
            page = None
            movieLST = []
            source = Ttype
            resolution = TRes
            n = 0
            
            if source == 'latest':
                page = 1

                for i in range(loop):
                    movies, has_next_page = HDTrailers.get_latest(page=page)
                    if has_next_page:
                        page = page + 1

                        for i, movie in enumerate(movies):
                            movie_id = movie['id']
                            movieLST.append(movie_id)
                    else:
                        break

            elif source == 'most_watched':
                movies, has_next_page = HDTrailers.get_most_watched()
            elif source == 'coming_soon':
                movies, has_next_page = HDTrailers.get_coming_soon()
            elif source == 'opening':
                movies, has_next_page = HDTrailers.get_opening_this_week()

            if source != 'latest':
                for i, movie in enumerate(movies):
                    if n >= loop:
                        break
                    movie_id=movie['id']
                    movieLST.append(movie_id)
                    n += 1

            for i in range(len(movieLST)):
                movie, trailers, clips = HDTrailers.get_videos(movieLST[i])
                videos = []
                videos.extend(trailers)
                items = []

                for i, video in enumerate(videos):
                    if resolution in video.get('resolutions'):
                        source = video['source']
                        url = video['resolutions'][resolution]

                        if not 'http://www.hd-trailers.net/yahoo-redir.php' in url:
                            playable_url = HDTrailers.get_playable_url(source, url)
                            playable_url = playable_url.replace('plugin://plugin.video.youtube/?action=play_video&videoid=', self.youtube_player)
                            try:
                                tubeID = playable_url.split('videoid=')[1]
                                duration = self.getYoutubeDuration(tubeID)
                            except:
                                duration = 120
                            InternetTrailers = (str(duration) + ',' + str(playable_url))
                            TrailerLST.append(InternetTrailers)  
                            TrailersCount += 1
        except Exception,e:
            self.log("InternetTrailer failed! " + str(e))

        TrailerLST = sorted_nicely(TrailerLST)
        if TrailerLST and len(TrailerLST) > 0:
            random.shuffle(TrailerLST)
        return TrailerLST
    
    
    # Adapted from Ronie's screensaver.picture.slideshow * https://github.com/XBMC-Addons/screensaver.picture.slideshow/blob/master/resources/lib/utils.py    
    def walk(self, path, types=MEDIA_TYPES):     
        self.log("walk " + path + ' ,' + str(types))
        video = []
        folders = []
        # multipath support
        if path.startswith('multipath://'):
            # get all paths from the multipath
            paths = path[12:-1].split('/')
            for item in paths:
                folders.append(urllib.unquote_plus(item))
        else:
            folders.append(os.path.join(path,''))
        for folder in folders:
            if FileAccess.exists(xbmc.translatePath(folder)):
                # get all files and subfolders
                dirs,files = FileAccess.listdir(folder)
                print dirs, files
                # natural sort
                convert = lambda text: int(text) if text.isdigit() else text
                alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
                files.sort(key=alphanum_key)
                for item in files:
                    # filter out all video
                    if os.path.splitext(item)[1].lower() in types:
                        video.append(os.path.join(folder,item))
                for item in dirs:
                    # recursively scan all subfolders
                    video += self.walk(os.path.join(folder,item)) # make sure paths end with a slash
        # cleanup   
        del folders[:]
        return video
        
        
    #Parse Plugin, return essential information. Not tmpstr         
