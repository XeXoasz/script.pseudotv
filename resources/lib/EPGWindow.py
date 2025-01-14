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
import datetime, traceback

from Playlist import Playlist
from Globals import *
from Channel import Channel
from ChannelList import ChannelList
from FileAccess import FileAccess



class EPGWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.focusRow = 0
        self.focusIndex = 0
        self.focusTime = 0
        self.focusEndTime = 0
        self.shownTime = 0
        self.centerChannel = 0
        self.rowCount = ROWCOUNT
        self.channelButtons = [None] * self.rowCount
        self.buttonCache = []
        self.actionSemaphore = threading.BoundedSemaphore()
        self.lastActionTime = time.time()
        self.channelLogos = ''
        self.textcolor = "FFFFFFFF"
        self.focusedcolor = "FF7d7d7d"
        self.clockMode = 0
        self.textfont  = "font13"
        self.hideTitleBlockSize = int(ADDON.getSetting("hideTitleBlockSize"))
        self.longBlockChannel = ADDON.getSetting('longBlockChannel').split(",")
        self.minimumBlockSize = int(ADDON.getSetting("minimumBlockSize"))
        self.infoOffset = 0
        self.altcolorchannels1 = ADDON.getSetting('altcolorchannels1').split(",")
        self.altcolorchannels2 = ADDON.getSetting('altcolorchannels2').split(",")
        self.altcolorchannels3 = ADDON.getSetting('altcolorchannels3').split(",")
        
        # Set media path.
        if os.path.exists(xbmc.translatePath(os.path.join(CWD, 'resources', 'skins', xbmc.getSkinDir(), 'media'))):
            self.mediaPath = xbmc.translatePath(os.path.join(CWD, 'resources', 'skins', xbmc.getSkinDir(), 'media' + '/'))
        else:
            self.mediaPath = xbmc.translatePath(os.path.join(CWD, 'resources', 'skins', 'default', 'media' + '/'))

        self.log('Media Path is ' + self.mediaPath)

        # Use the given focus and non-focus textures if they exist.  Otherwise use the defaults.
        if xbmc.skinHasImage(self.mediaPath + BUTTON_FOCUS):
            self.textureButtonFocus = self.mediaPath + BUTTON_FOCUS
        else:
            self.textureButtonFocus = 'pstvButtonFocus.png'

        if xbmc.skinHasImage(self.mediaPath + BUTTON_FOCUS_SHORT):
            self.textureButtonFocusShort = self.mediaPath + BUTTON_FOCUS_SHORT
        else:
            self.textureButtonFocusShort = 'pstvButtonFocus.png'
        
        if xbmc.skinHasImage(self.mediaPath + BUTTON_NO_FOCUS):
            self.textureButtonNoFocus = self.mediaPath + BUTTON_NO_FOCUS
        else:
            self.textureButtonNoFocus = 'pstvButtonNoFocus'
            
        if xbmc.skinHasImage(self.mediaPath + BUTTON_NO_FOCUS_SHORT):
            self.textureButtonNoFocusShort = self.mediaPath + BUTTON_NO_FOCUS_SHORT
        else:
            self.textureButtonNoFocusShort = 'pstvButtonNoFocus'
        
        if xbmc.skinHasImage(self.mediaPath + BUTTON_NO_FOCUS_ALT1):
            self.textureButtonNoFocusAlt1 = self.mediaPath + BUTTON_NO_FOCUS_ALT1
        else:
            self.textureButtonNoFocusAlt1 = 'pstvButtonNoFocus'   
                 
        if xbmc.skinHasImage(self.mediaPath + BUTTON_NO_FOCUS_ALT2):
            self.textureButtonNoFocusAlt2 = self.mediaPath + BUTTON_NO_FOCUS_ALT2
        else:
            self.textureButtonNoFocusAlt2 = 'pstvButtonNoFocus'

        if xbmc.skinHasImage(self.mediaPath + BUTTON_NO_FOCUS_ALT3):
            self.textureButtonNoFocusAlt3 = self.mediaPath + BUTTON_NO_FOCUS_ALT3
        else:
            self.textureButtonNoFocusAlt3 = 'pstvButtonNoFocus'       

        if xbmc.skinHasImage(self.mediaPath + BUTTON_NO_FOCUS_ALT1_SHORT):
            self.textureButtonNoFocusAlt1Short = self.mediaPath + BUTTON_NO_FOCUS_ALT1_SHORT
        else:
            self.textureButtonNoFocusAlt1Short = 'pstvButtonNoFocus'

        if xbmc.skinHasImage(self.mediaPath + BUTTON_NO_FOCUS_ALT2_SHORT):
            self.textureButtonNoFocusAlt2Short = self.mediaPath + BUTTON_NO_FOCUS_ALT2_SHORT
        else:
            self.textureButtonNoFocusAlt2Short = 'pstvButtonNoFocus'
        
        if xbmc.skinHasImage(self.mediaPath + BUTTON_NO_FOCUS_ALT3_SHORT):
            self.textureButtonNoFocusAlt3Short = self.mediaPath + BUTTON_NO_FOCUS_ALT3_SHORT
        else:
            self.textureButtonNoFocusAlt3Short = 'pstvButtonNoFocus'

        for i in range(self.rowCount):
            self.channelButtons[i] = []

        self.clockMode = ADDON_SETTINGS.getSetting("ClockMode")
        self.toRemove = []


    def onFocus(self, controlid):
        #self.getControl(500).setLabel(self.getControl(controlid).getLabel())
        pass


    # set the time labels
    def setTimeLabels(self, thetime):
        self.log('setTimeLabels')
        now = datetime.datetime.fromtimestamp(thetime)
        self.getControl(104).setLabel(now.strftime('%A, %d %B %Y').lstrip("0").replace(" 0", " "))
        delta = datetime.timedelta(minutes=30)

        for i in range(3):
            if self.clockMode == "0":
                self.getControl(101 + i).setLabel(now.strftime("%I:%M %p").lstrip("0").replace(" 0", " "))
            else:
                self.getControl(101 + i).setLabel(now.strftime("%H:%M"))

            now = now + delta

        self.log('setTimeLabels return')


    def log(self, msg, level = xbmc.LOGDEBUG):
        log('EPGWindow: ' + msg, level)


    def onInit(self):
        self.log('onInit')
        timex, timey = self.getControl(120).getPosition()
        timew = self.getControl(120).getWidth()
        timeh = self.getControl(120).getHeight()
        self.currentTimeBar = xbmcgui.ControlImage(timex, timey, timew, timeh, self.mediaPath + TIME_BAR)
        
        self.addControl(self.currentTimeBar)

        try:
            textcolor = int(self.getControl(100).getLabel(), 16)
            focusedcolor = int(self.getControl(100).getLabel2(), 16)
            self.textfont =  self.getControl(105).getLabel()

            if textcolor > 0:
                self.textcolor = hex(textcolor)[2:]

            if focusedcolor > 0:
                self.focusedcolor = hex(focusedcolor)[2:]
        except:
            pass

        try:
            if self.setChannelButtons(time.time(), self.MyOverlayWindow.currentChannel) == False:
                self.log('Unable to add channel buttons')
                return

            curtime = time.time()
            self.focusIndex = -1
            basex, basey = self.getControl(113).getPosition()
            baseh = self.getControl(113).getHeight()
            basew = self.getControl(113).getWidth()

            # set the button that corresponds to the currently playing show
            for i in range(len(self.channelButtons[2])):
                left, top = self.channelButtons[2][i].getPosition()
                width = self.channelButtons[2][i].getWidth()
                left = left - basex
                starttime = self.shownTime + (left / (basew / 5400.0))
                endtime = starttime + (width / (basew / 5400.0))

                if curtime >= starttime and curtime <= endtime:
                    self.focusIndex = i
                    self.setFocus(self.channelButtons[2][i])
                    self.focusTime = int(time.time())
                    self.focusEndTime = endtime
                    break

            # If nothing was highlighted, just select the first button
            if self.focusIndex == -1:
                self.focusIndex = 0
                self.setFocus(self.channelButtons[2][0])
                left, top = self.channelButtons[2][0].getPosition()
                width = self.channelButtons[2][0].getWidth()
                left = left - basex
                starttime = self.shownTime + (left / (basew / 5400.0))
                endtime = starttime + (width / (basew / 5400.0))
                self.focusTime = int(starttime + 30)
                self.focusEndTime = endtime

            self.focusRow = 2
            self.setShowInfo()
        except:
            self.log("Unknown EPG Initialization Exception", xbmc.LOGERROR)
            self.log(traceback.format_exc(), xbmc.LOGERROR)

            try:
                self.close()
            except:
                self.log("Error closing", xbmc.LOGERROR)

            self.MyOverlayWindow.sleepTimeValue = 1
            self.MyOverlayWindow.startSleepTimer()
            return

        self.log('onInit return')


    # setup all channel buttons for a given time
    def setChannelButtons(self, starttime, curchannel, singlerow = -1):
        self.log('setChannelButtons ' + str(starttime) + ', ' + str(curchannel))
        self.centerChannel = self.MyOverlayWindow.fixChannel(curchannel)

        # # todo filter epg, controlid 6000
            # EPG_CHTYPE_FILTER = [8]
            # while self.MyOverlayWindow.getChtype(curchannel) in EPG_CHTYPE_FILTER:
                # curchannel = self.MyOverlayWindow.fixChannel(curchannel + 1, False)
            
            # This is done twice to guarantee we go back 2 channels.  If the previous 2 channels
            # aren't valid, then doing a fix on curchannel - 2 may result in going back only
            # a single valid channel.
        
        # This is done twice to guarantee we go back 2 channels.  If the previous 2 channels
        # aren't valid, then doing a fix on curchannel - 2 may result in going back only
        # a single valid channel.
        curchannel = self.MyOverlayWindow.fixChannel(curchannel - 1, False)
        curchannel = self.MyOverlayWindow.fixChannel(curchannel - 1, False)
        starttime = self.roundToHalfHour(int(starttime))
        self.setTimeLabels(starttime)
        self.shownTime = starttime
        basex, basey = self.getControl(111).getPosition()
        basew = self.getControl(111).getWidth()
        tmpx, tmpy =  self.getControl(110 + self.rowCount).getPosition()
        timex, timey = self.getControl(120).getPosition()
        timew = self.getControl(120).getWidth()
        timeh = self.getControl(120).getHeight()
        basecur = curchannel
        self.toRemove.append(self.currentTimeBar)
        EpgLogo = ADDON.getSetting('ShowEpgLogo')
        myadds = []

        for i in range(self.rowCount):
            if singlerow == -1 or singlerow == i:
                self.setButtons(starttime, basecur, i)
                myadds.extend(self.channelButtons[i])

            basecur = self.MyOverlayWindow.fixChannel(basecur + 1)

        basecur = curchannel

        for i in range(self.rowCount):
            self.getControl(301 + i).setLabel(self.MyOverlayWindow.channels[basecur - 1].name)
            basecur = self.MyOverlayWindow.fixChannel(basecur + 1)

        for i in range(self.rowCount):
            try:
                self.getControl(311 + i).setLabel(str(curchannel))
            except:
                pass

            try:
                if (EpgLogo == 'true'):
                    self.getControl(321 + i).setImage(self.channelLogos + ascii(self.MyOverlayWindow.channels[curchannel - 1].name) + ".png")
                    if not FileAccess.exists(self.channelLogos + ascii(self.MyOverlayWindow.channels[curchannel - 1].name) + ".png"):
                        self.getControl(321 + i).setImage(IMAGES_LOC + "Default.png")
            except:
                pass

            curchannel = self.MyOverlayWindow.fixChannel(curchannel + 1)

        if time.time() >= starttime and time.time() < starttime + 5400:
            dif = int((starttime + 5400 - time.time()))
            self.currentTimeBar.setPosition(int((basex + basew - (timew / 2)) - (dif * (basew / 5400.0))), timey)
        else:
            if time.time() < starttime:
                self.currentTimeBar.setPosition(basex, timey)
            else:
                 self.currentTimeBar.setPosition(basex + basew - timew, timey)

        myadds.append(self.currentTimeBar)

        try:
            self.removeControls(self.toRemove)
        except:
            for cntrl in self.toRemove:
                try:
                    self.removeControl(cntrl)
                except:
                    pass

        self.addControls(myadds)
        self.toRemove = []
        self.log('setChannelButtons return')


    # round the given time down to the nearest half hour
    def roundToHalfHour(self, thetime):
        n = datetime.datetime.fromtimestamp(thetime)
        delta = datetime.timedelta(minutes=30)

        if n.minute > 29:
            n = n.replace(minute=30, second=0, microsecond=0)
        else:
            n = n.replace(minute=0, second=0, microsecond=0)

        return time.mktime(n.timetuple())


    # create the buttons for the specified channel in the given row
    def setButtons(self, starttime, curchannel, row):
        self.log('setButtons ' + str(starttime) + ", " + str(curchannel) + ", " + str(row))

        try:
            curchannel = self.MyOverlayWindow.fixChannel(curchannel)
            basex, basey = self.getControl(111 + row).getPosition()
            baseh = self.getControl(111 + row).getHeight()
            basew = self.getControl(111 + row).getWidth()

            if xbmc.Player().isPlaying() == False:
                self.log('No video is playing, not adding buttons')
                self.closeEPG()
                return False

            # Backup all of the buttons to an array
            self.toRemove.extend(self.channelButtons[row])
            self.toRemove.extend(self.channelTags[row]) 
            del self.channelButtons[row][:]
            del self.channelTags[row][:]

            # todo filter epg
            playlistpos = int(xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition())
            self.log('setButtons, playlistpos = ' + str(playlistpos))
            
            # if the channel is paused, then only 1 button needed
            if self.MyOverlayWindow.channels[curchannel - 1].isPaused:
                if str(curchannel) in self.altcolorchannels1:
                    self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.channels[curchannel - 1].getCurrentTitle() + " (paused)", focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocusAlt1, alignment=4, font=self.textfont, textColor=self.textcolor, shadowColor='0xAA000000', focusedColor=self.focusedcolor))
                
                elif str(curchannel) in self.altcolorchannels2:
                    self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.channels[curchannel - 1].getCurrentTitle() + " (paused)", focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocusAlt2, alignment=4, font=self.textfont, textColor=self.textcolor, shadowColor='0xAA000000', focusedColor=self.focusedcolor))
                
                elif str(curchannel) in self.altcolorchannels3:
                    self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.channels[curchannel - 1].getCurrentTitle() + " (paused)", focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocusAlt3, alignment=4, font=self.textfont, textColor=self.textcolor, shadowColor='0xAA000000', focusedColor=self.focusedcolor))
                
                else:
                    self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.channels[curchannel - 1].getCurrentTitle() + " (paused)", focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, font=self.textfont, textColor=self.textcolor, shadowColor='0xAA000000', focusedColor=self.focusedcolor))
            # if the channel is paused, then only 1 button needed
                if self.MyOverlayWindow.channels[curchannel - 1].isPaused:
                    self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.channels[curchannel - 1].getCurrentTitle() + " (paused)", focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, shadowColor=self.shadowColor, textColor=self.textcolor, focusedColor=self.focusedcolor))
                # if the channel is not local and duration is under BYPASS_EPG_SECONDS, then only 1 button needed
                elif chtype >= 10 and self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos) < BYPASS_EPG_SECONDS:    
                    self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.getChname(curchannel), focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, shadowColor=self.shadowColor, textColor=self.textcolor, focusedColor=self.focusedcolor))               
                else:            
                    # Find the show that was running at the given time for the current channel.
                    if curchannel == self.MyOverlayWindow.currentChannel:
                        if chtype == 8 and len(self.MyOverlayWindow.channels[curchannel - 1].getItemtimestamp(playlistpos)) > 0:
                            epochBeginDate = datetime_to_epoch(self.MyOverlayWindow.channels[curchannel - 1].getItemtimestamp(playlistpos))
                            videotime = time.time() - epochBeginDate
                            reftime = time.time()
                        else:                        
                            videotime = self.getPlayerTime()
                            reftime = time.time()        
                    else:
                        if chtype == 8 and len(self.MyOverlayWindow.channels[curchannel - 1].getItemtimestamp(playlistpos)) > 0:
                            playlistpos = self.MyOverlayWindow.channels[curchannel - 1].playlistPosition
                            epochBeginDate = datetime_to_epoch(self.MyOverlayWindow.channels[curchannel - 1].getItemtimestamp(playlistpos))
                            #loop to ensure we get the current show in the playlist
                            while epochBeginDate + self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos) <  time.time():
                                epochBeginDate += self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos)
                                playlistpos = self.MyOverlayWindow.channels[curchannel - 1].fixPlaylistIndex(playlistpos + 1)
                            videotime = time.time() - epochBeginDate
                            reftime = time.time()
                        else:
                            playlistpos = self.MyOverlayWindow.channels[curchannel - 1].playlistPosition
                            videotime = self.MyOverlayWindow.channels[curchannel - 1].showTimeOffset
                            reftime = self.MyOverlayWindow.channels[curchannel - 1].lastAccessTime

                    # normalize reftime to the beginning of the video
                    reftime -= videotime

                while reftime > starttime:
                    playlistpos -= 1
                    # No need to check bounds on the playlistpos, the duration function makes sure it is correct
                    reftime -= self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos)

                while reftime + self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos) < starttime:
                    reftime += self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos)
                    playlistpos += 1

                # create a button for each show that runs in the next hour and a half
                endtime = starttime + 5400
                totaltime = 0
                totalloops = 0

                while reftime < endtime and totalloops < 1000:
                    xpos = int(basex + (totaltime * (basew / 5400.0)))
                    tmpdur = self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos)
                    shouldskip = False

                    # this should only happen the first time through this loop
                    # it shows the small portion of the show before the current one
                    if reftime < starttime:
                        tmpdur -= starttime - reftime
                        reftime = starttime

                        if tmpdur < 60 * 3:
                            shouldskip = True

                    # Don't show very short videos or bct types
                        if shouldskip == False:
                            if chtype <= 7 and self.MyOverlayWindow.hideShortItems and self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos) < self.MyOverlayWindow.shortItemLength:
                                shouldskip = True
                                tmpdur = 0
                            elif chtype <= 7 and (self.MyOverlayWindow.channels[curchannel - 1].getItemgenre(playlistpos)).lower() in BCT_TYPES:
                                shouldskip = True
                                tmpdur = 0
                            elif chtype == 8 and datetime_to_epoch(self.MyOverlayWindow.channels[curchannel - 1].getItemtimestamp(playlistpos)) + self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos) < time.time():
                                ADDON_SETTINGS.setSetting('Channel_' + str(curchannel) + '_changed', "True")
                                shouldskip = True
                                tmpdur = LIVETV_MAXPARSE
                            elif chtype not in IGNORE_SEEKTIME_CHTYPE:
                                nextlen = self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos + 1)
                                prevlen = self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos - 1)

                                if nextlen < 60:
                                    tmpdur += nextlen / 2

                                if prevlen < 60:
                                    tmpdur += prevlen / 2

                        width = int((basew / 5400.0) * tmpdur)
                        if width < 30 and shouldskip == False:
                            width = 30
                            tmpdur = int(30.0 / (basew / 5400.0))

                        if width + xpos > basex + basew:
                            width = basex + basew - xpos

                        if shouldskip == False and width >= 30:
                            mylabel = self.MyOverlayWindow.channels[curchannel - 1].getItemTitle(playlistpos)
                            timestamp = self.MyOverlayWindow.channels[curchannel - 1].getItemtimestamp(playlistpos)
                            myLiveID = self.MyOverlayWindow.channels[curchannel - 1].getItemLiveID(playlistpos)
                            LiveID = self.chanlist.unpackLiveID(myLiveID)
                            type = LiveID[0]
                            rating = LiveID[5]
                            hd = LiveID[6] == 'True'
                            cc = LiveID[7] == 'True'
                            stars = LiveID[8]
                            rec = self.MyOverlayWindow.isRecord(str(chtype), str(curchannel), timestamp, pType='EPG')
                            sch = self.MyOverlayWindow.isReminder(str(chtype), str(curchannel), timestamp, pType='EPG')
                            EPGtags = {'REC': rec, 'SCH': sch, 'RATING': rating, 'HD': hd, 'CC': cc, 'STARS': stars} 
                                
                            if REAL_SETTINGS.getSetting('EPGcolor_enabled') == '1':
                                if type == 'movie' and REAL_SETTINGS.getSetting('EPGcolor_MovieGenre') == "false":
                                    self.textureButtonNoFocus = self.getEPGtype('Movie')
                                else:
                                    mygenre = self.MyOverlayWindow.channels[curchannel - 1].getItemgenre(playlistpos)
                                    self.textureButtonNoFocus = self.getEPGtype(mygenre) 
                            elif REAL_SETTINGS.getSetting('EPGcolor_enabled') == '2':
                                self.textureButtonNoFocus = self.getEPGtype(str(chtype))
                            elif REAL_SETTINGS.getSetting('EPGcolor_enabled') == '3':
                                self.textureButtonNoFocus = self.getEPGtype(rating)
                            else:   
                                self.textureButtonNoFocus = MEDIA_LOC + BUTTON_NO_FOCUS

                            #Create Control array
                            self.channelButtons[row].append(xbmcgui.ControlButton(xpos, basey, width, baseh, mylabel, focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, shadowColor=self.shadowColor, font=self.textfont, textColor=self.textcolor, focusedColor=self.focusedcolor))
                            self.addButtonTags(row, xpos, basey, width, baseh, mylabel, EPGtags)
                            #todo set epg tag icon (addButtonTags)for ondemand
                            
                    totaltime += tmpdur
                    reftime += tmpdur
                    playlistpos += 1
                    totalloops += 1

                if totalloops >= 1000:
                    self.log("Broken big loop, too many loops, reftime is " + str(reftime) + ", endtime is " + str(endtime))

                # If there were no buttons added, show some default button
                if len(self.channelButtons[row]) == 0:
                    self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.channels[curchannel - 1].name, focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, font=self.textfont, textColor=self.textcolor, shadowColor='0xAA000000', focusedColor=self.focusedcolor))
        except:
            self.log("Exception in setButtons", xbmc.LOGERROR)
            self.log(traceback.format_exc(), xbmc.LOGERROR)

        self.log('setButtons return')
        return True


    def onAction(self, act):
        self.log('onAction ' + str(act.getId()))

        if self.actionSemaphore.acquire(False) == False:
            self.log('Unable to get semaphore')
            return

        action = act.getId()

        try:
            if action in ACTION_PREVIOUS_MENU:
                self.closeEPG()
            elif action == ACTION_MOVE_DOWN:
                self.GoDown()
            elif action == ACTION_MOVE_UP:
                self.GoUp()
            elif action == ACTION_PAGEDOWN: 
                self.GoPgDown()  
            elif action == ACTION_PAGEUP: 
                self.GoPgUp()  
            elif action == ACTION_MOVE_LEFT:
                self.GoLeft()
            elif action == ACTION_MOVE_RIGHT:
                self.GoRight()
            elif action == ACTION_STOP:
                self.closeEPG()
            elif action == ACTION_SELECT_ITEM:
                lastaction = time.time() - self.lastActionTime

                if lastaction >= 2:
                    self.selectShow()
                    self.closeEPG()
                    self.lastActionTime = time.time()
            elif action == ACTION_NEXT_PICTURE:
                self.closeEPG()
                global ROWCOUNT
                self.log('EPG pre ROWCOUNT = ' + str(ROWCOUNT))
                if ROWCOUNT == 3:
                    ROWCOUNT = 6
                elif ROWCOUNT == 6:
                    ROWCOUNT = 9
                elif ROWCOUNT == 9:
                    ROWCOUNT = 3
                self.log('EPG post ROWCOUNT = ' + str(ROWCOUNT))    
                                
                self.myEPG = EPGWindow("script.pseudotv.EPG" + str(ROWCOUNT) + ".xml", CWD, "default")
                self.myEPG.channelLogos = self.channelLogos
                self.myEPG.MyOverlayWindow = self.MyOverlayWindow 
                self.myEPG.doModal()
                    
        except:
            self.log("Unknown EPG Exception OnAction", xbmc.LOGERROR)
            self.log(traceback.format_exc(), xbmc.LOGERROR)

            try:
                self.close()
            except:
                self.log("Error closing", xbmc.LOGERROR)

            self.MyOverlayWindow.sleepTimeValue = 1
            self.MyOverlayWindow.startSleepTimer()
            return

        self.actionSemaphore.release()
        self.log('onAction return')


    def closeEPG(self):
        self.log('closeEPG')

        try:
            self.removeControl(self.currentTimeBar)
            self.MyOverlayWindow.startSleepTimer()
        except:
            pass

        self.close()


    def onControl(self, control):
        self.log('onControl')


    # Run when a show is selected, so close the epg and run the show
    def onClick(self, controlid):
        self.log('onClick')

        if self.actionSemaphore.acquire(False) == False:
            self.log('Unable to get semaphore')
            return

        lastaction = time.time() - self.lastActionTime

        if lastaction >= 2:
            try:
                selectedbutton = self.getControl(controlid)
            except:
                self.actionSemaphore.release()
                self.log('onClick unknown controlid ' + str(controlid))
                return

            for i in range(self.rowCount):
                for x in range(len(self.channelButtons[i])):
                    mycontrol = 0
                    mycontrol = self.channelButtons[i][x]

                    if selectedbutton == mycontrol:
                        self.focusRow = i
                        self.focusIndex = x
                        self.selectShow()
                        self.closeEPG()
                        self.lastActionTime = time.time()
                        self.actionSemaphore.release()
                        self.log('onClick found button return')
                        return

            self.lastActionTime = time.time()
            self.closeEPG()

        self.actionSemaphore.release()
        self.log('onClick return')


    def GoDown(self):
        self.log('goDown')

        # change controls to display the proper junks
        if self.focusRow == self.rowCount - 1:
            self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(self.centerChannel + 1))
            self.focusRow = self.rowCount - 2

        self.setProperButton(self.focusRow + 1)
        self.log('goDown return')


    def GoUp(self):
        self.log('goUp')

        # same as godown
        # change controls to display the proper junks
        if self.focusRow == 0:
            self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(self.centerChannel - 1, False))
            self.focusRow = 1

        self.setProperButton(self.focusRow - 1)
        self.log('goUp return')


    def GoPgUp(self):
        self.log('GoPgUp')
        newchannel = self.centerChannel
        for x in range(0, self.rowCount):
            newchannel = self.MyOverlayWindow.fixChannel(newchannel - 1, False)
        self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(newchannel))
        self.setProperButton(0)
        self.log('GoPgUp return')

    def GoPgDown(self):
        self.log('GoPgDown')
        newchannel = self.centerChannel
        for x in range(0, self.rowCount):
            newchannel = self.MyOverlayWindow.fixChannel(newchannel + 1)
        self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(newchannel))
        self.setProperButton(0)
        self.log('GoPgDown return') 

        
    def GoLeft(self):
        self.log('goLeft')
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        basew = self.getControl(111 + self.focusRow).getWidth()

        # change controls to display the proper junks
        if self.focusIndex == 0:
            left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
            width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            self.setChannelButtons(self.shownTime - 1800, self.centerChannel)
            curbutidx = self.findButtonAtTime(self.focusRow, starttime + 30)

            if(curbutidx - 1) >= 0:
                self.focusIndex = curbutidx - 1
            else:
                self.focusIndex = 0
        else:
            self.focusIndex -= 1

        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex
        starttime = self.shownTime + (left / (basew / 5400.0))
        endtime = starttime + (width / (basew / 5400.0))
        self.setFocus(self.channelButtons[self.focusRow][self.focusIndex])
        self.setShowInfo()
        self.focusEndTime = endtime
        self.focusTime = starttime + 30
        self.log('goLeft return')


    def GoRight(self):
        self.log('goRight')
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        basew = self.getControl(111 + self.focusRow).getWidth()

        # change controls to display the proper junks
        if self.focusIndex == len(self.channelButtons[self.focusRow]) - 1:
            left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
            width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            self.setChannelButtons(self.shownTime + 1800, self.centerChannel)
            curbutidx = self.findButtonAtTime(self.focusRow, starttime + 30)

            if(curbutidx + 1) < len(self.channelButtons[self.focusRow]):
                self.focusIndex = curbutidx + 1
            else:
                self.focusIndex = len(self.channelButtons[self.focusRow]) - 1
        else:
            self.focusIndex += 1

        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex
        starttime = self.shownTime + (left / (basew / 5400.0))
        endtime = starttime + (width / (basew / 5400.0))
        self.setFocus(self.channelButtons[self.focusRow][self.focusIndex])
        self.setShowInfo()
        self.focusEndTime = endtime
        self.focusTime = starttime + 30
        self.log('goRight return')


    def findButtonAtTime(self, row, selectedtime):
        self.log('findButtonAtTime ' + str(row))
        basex, basey = self.getControl(111 + row).getPosition()
        baseh = self.getControl(111 + row).getHeight()
        basew = self.getControl(111 + row).getWidth()

        for i in range(len(self.channelButtons[row])):
            left, top = self.channelButtons[row][i].getPosition()
            width = self.channelButtons[row][i].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            endtime = starttime + (width / (basew / 5400.0))

            if selectedtime >= starttime and selectedtime <= endtime:
                return i

        return -1


    # based on the current focus row and index, find the appropriate button in
    # the new row to set focus to
    def setProperButton(self, newrow, resetfocustime = False):
        self.log('setProperButton ' + str(newrow))
        self.focusRow = newrow
        basex, basey = self.getControl(111 + newrow).getPosition()
        baseh = self.getControl(111 + newrow).getHeight()
        basew = self.getControl(111 + newrow).getWidth()

        for i in range(len(self.channelButtons[newrow])):
            left, top = self.channelButtons[newrow][i].getPosition()
            width = self.channelButtons[newrow][i].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            endtime = starttime + (width / (basew / 5400.0))

            if self.focusTime >= starttime and self.focusTime <= endtime:
                self.focusIndex = i
                self.setFocus(self.channelButtons[newrow][i])
                self.setShowInfo()
                self.focusEndTime = endtime

                if resetfocustime:
                    self.focusTime = starttime + 30

                self.log('setProperButton found button return')
                return

        self.focusIndex = 0
        self.setFocus(self.channelButtons[newrow][0])
        left, top = self.channelButtons[newrow][0].getPosition()
        width = self.channelButtons[newrow][0].getWidth()
        left = left - basex
        starttime = self.shownTime + (left / (basew / 5400.0))
        endtime = starttime + (width / (basew / 5400.0))
        self.focusEndTime = endtime

        if resetfocustime:
            self.focusTime = starttime + 30

        self.setShowInfo()
        self.log('setProperButton return')


    def setShowInfo(self):
        self.log('setShowInfo')
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        baseh = self.getControl(111 + self.focusRow).getHeight()
        basew = self.getControl(111 + self.focusRow).getWidth()
        # use the selected time to set the video
        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        left = float(left)
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex + (width / 2)
        starttime = self.shownTime + (left / (basew / 5400.0))
        chnoffset = self.focusRow - 2
        newchan = self.centerChannel
        
        while chnoffset != 0:
            if chnoffset > 0:
                newchan = self.MyOverlayWindow.fixChannel(newchan + 1, True)
                chnoffset -= 1
            else:
                newchan = self.MyOverlayWindow.fixChannel(newchan - 1, False)
                chnoffset += 1
        
        plpos = self.determinePlaylistPosAtTime(starttime, newchan)

        if plpos == -1:
            self.log('Unable to find the proper playlist to set from EPG')
            return
        
        shouldskip = False
        
        if self.MyOverlayWindow.hideShortItemsEPG:
            ItemDuration = self.MyOverlayWindow.channels[newchan - 1].getItemDuration(plpos)
            if ItemDuration <= self.MyOverlayWindow.shortItemLength:
                self.infoOffset = 1
                plpos = plpos + self.infoOffset
                self.log('self.infoOffset = ' + str(self.infoOffset))
        #comment out the line below (shouldskip = False) to try to hide info box for small videos (it doesn't work well)
        #need to get info onFocus (see commented line there) but the control button only has the 1 label string
        #shouldskip = False
        
        if str(newchan) in self.longBlockChannel:
            self.getControl(500).setLabel("")
            self.getControl(501).setLabel("")
            self.getControl(502).setText("")
            self.getControl(503).setImage(self.channelLogos + ascii(self.MyOverlayWindow.channels[newchan - 1].name) + '.png')
            if not FileAccess.exists(self.channelLogos + ascii(self.MyOverlayWindow.channels[newchan - 1].name) + '.png'):
                self.getControl(503).setImage(IMAGES_LOC + 'Default.png')
        elif shouldskip == False:       
            self.getControl(500).setLabel(self.MyOverlayWindow.channels[newchan - 1].getItemTitle(plpos))
            self.getControl(501).setLabel(self.MyOverlayWindow.channels[newchan - 1].getItemEpisodeTitle(plpos))
            self.getControl(502).setText(self.MyOverlayWindow.channels[newchan - 1].getItemDescription(plpos))
            self.getControl(503).setImage(self.channelLogos + ascii(self.MyOverlayWindow.channels[newchan - 1].name) + '.png')
            if not FileAccess.exists(self.channelLogos + ascii(self.MyOverlayWindow.channels[newchan - 1].name) + '.png'):
                self.getControl(503).setImage(IMAGES_LOC + 'Default.png')
        
        self.log('setShowInfo return')
       

    # using the currently selected button, play the proper shows
    def selectShow(self):
        self.log('selectShow')
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        baseh = self.getControl(111 + self.focusRow).getHeight()
        basew = self.getControl(111 + self.focusRow).getWidth()
        # use the selected time to set the video
        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex + (width / 2)
        starttime = self.shownTime + (left / (basew / 5400.0))
        chnoffset = self.focusRow - 2
        newchan = self.centerChannel

        while chnoffset != 0:
            if chnoffset > 0:
                newchan = self.MyOverlayWindow.fixChannel(newchan + 1, True)
                chnoffset -= 1
            else:
                newchan = self.MyOverlayWindow.fixChannel(newchan - 1, False)
                chnoffset += 1

        plpos = self.determinePlaylistPosAtTime(starttime, newchan)

        if plpos == -1:
            self.log('Unable to find the proper playlist to set from EPG', xbmc.LOGERROR)
            return

        timedif = (time.time() - self.MyOverlayWindow.channels[newchan - 1].lastAccessTime)
        pos = self.MyOverlayWindow.channels[newchan - 1].playlistPosition
        showoffset = self.MyOverlayWindow.channels[newchan - 1].showTimeOffset

        # adjust the show and time offsets to properly position inside the playlist
        while showoffset + timedif > self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos):
            timedif -= self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos) - showoffset
            pos = self.MyOverlayWindow.channels[newchan - 1].fixPlaylistIndex(pos + 1)
            showoffset = 0

        if self.MyOverlayWindow.currentChannel == newchan:
            if plpos == xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition():
                self.log('selectShow return current show')
                return

        if pos != plpos:
            self.MyOverlayWindow.channels[newchan - 1].setShowPosition(plpos)
            self.MyOverlayWindow.channels[newchan - 1].setShowTime(0)
            self.MyOverlayWindow.channels[newchan - 1].setAccessTime(time.time())

        self.MyOverlayWindow.newChannel = newchan
        self.log('selectShow return')


    def determinePlaylistPosAtTime(self, starttime, channel):
        self.log('determinePlaylistPosAtTime ' + str(starttime) + ', ' + str(channel))
        channel = self.MyOverlayWindow.fixChannel(channel)

        # if the channel is paused, then it's just the current item
        if self.MyOverlayWindow.channels[channel - 1].isPaused:
            self.log('determinePlaylistPosAtTime paused return')
            return self.MyOverlayWindow.channels[channel - 1].playlistPosition
        else:
            # Find the show that was running at the given time
            # Use the current time and show offset to calculate it
            # At timedif time, channelShowPosition was playing at channelTimes
            # The only way this isn't true is if the current channel is curchannel since
            # it could have been fast forwarded or rewinded (rewound)?
            if channel == self.MyOverlayWindow.currentChannel:
                playlistpos = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
                videotime = xbmc.Player().getTime()
                reftime = time.time()
            else:
                playlistpos = self.MyOverlayWindow.channels[channel - 1].playlistPosition
                videotime = self.MyOverlayWindow.channels[channel - 1].showTimeOffset
                reftime = self.MyOverlayWindow.channels[channel - 1].lastAccessTime

            # normalize reftime to the beginning of the video
            reftime -= videotime

            while reftime > starttime:
                playlistpos -= 1
                reftime -= self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos)

            while reftime + self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos) < starttime:
                reftime += self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos)
                playlistpos += 1

            self.log('determinePlaylistPosAtTime return' + str(self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(playlistpos)))
            return self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(playlistpos)
        
        def determinePlaylistPosAtTime(self, starttime, channel):
            self.log('determinePlaylistPosAtTime ' + str(starttime) + ', ' + str(channel))
            channel = self.MyOverlayWindow.fixChannel(channel)
            chtype = self.MyOverlayWindow.getChtype(channel)

            try:
                # if the channel is paused, then it's just the current item
                if self.MyOverlayWindow.channels[channel - 1].isPaused:
                    self.log('determinePlaylistPosAtTime paused return')
                    return self.MyOverlayWindow.channels[channel - 1].playlistPosition
                else:
                    # Find the show that was running at the given time
                    # Use the current time and show offset to calculate it
                    # At timedif time, channelShowPosition was playing at channelTimes
                    # The only way this isn't true is if the current channel is curchannel since
                    # it could have been fast forwarded or rewinded (rewound)?
                    if channel == self.MyOverlayWindow.currentChannel:
                        playlistpos = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
                        if chtype == 8 and len(self.MyOverlayWindow.channels[channel - 1].getItemtimestamp(playlistpos)) > 0:
                            tmpDate = self.MyOverlayWindow.channels[channel - 1].getItemtimestamp(playlistpos)
                            epochBeginDate = datetime_to_epoch(tmpDate)
                            videotime = time.time() - epochBeginDate
                            reftime = time.time()
                        else:
                            videotime = xbmc.Player().getTime()
                            reftime = time.time()
                    else:
                        playlistpos = self.MyOverlayWindow.channels[channel - 1].playlistPosition
                        if chtype == 8 and len(self.MyOverlayWindow.channels[channel - 1].getItemtimestamp(playlistpos)) > 0:
                            tmpDate = self.MyOverlayWindow.channels[channel - 1].getItemtimestamp(playlistpos)
                            epochBeginDate = datetime_to_epoch(tmpDate)
                            while epochBeginDate + self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos) <  time.time():
                                epochBeginDate += self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos)
                                playlistpos = self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(playlistpos + 1)
                            videotime = time.time() - epochBeginDate
                            reftime = time.time()
                        else:
                            videotime = self.MyOverlayWindow.channels[channel - 1].showTimeOffset
                            reftime = self.MyOverlayWindow.channels[channel - 1].lastAccessTime

                    # normalize reftime to the beginning of the video
                    reftime -= videotime

                    while reftime > starttime:
                        playlistpos -= 1
                        reftime -= self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos)

                    while reftime + self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos) < starttime:
                        reftime += self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos)
                        playlistpos += 1

                    self.log('determinePlaylistPosAtTime return' + str(self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(playlistpos)))
                    return self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(playlistpos)
            except:
                pass