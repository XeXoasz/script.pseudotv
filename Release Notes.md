![alt text](https://github.com/fnord12/script.pseudotv/blob/master/resources/images/Default.png?raw=true "PseudoTV Logo")

PseudoTV 2.5.0 update - fnord12 branch
======

Since Steveb has taken a break, i have been digging into the code, mainly trying to fix the known problem introduced in Kodi 17 and worsened in 18 where resuming a paused video results in the channel resetting.  So far i haven't been able to address that, but in digging through the code i've found where i coild make a number of other improvements and thought it merited a "release".

### BEHAVIOR UPDATES

* Start Channel. Kodi's default behavior is to start with channel 1 after a Forced Reset, but to otherwise remember the last channel you were on and continue playing from there.  The problem is that with the current Resume bug, it was always resetting your last channel when you came back in.  The Start Channel option allows you to circumvent the problem by always starting up on a channel where you don't care if it reset (e.g. a channel with music videos or cartoon shorts).  Then you can flip back to your movie in progress.  (Even without that bug it's a useful feature, ofc.)

* Improvement/Change to Changing Channel by Number Input. When changing a channel via inputting numbers and pressing enter/ok, i've been running into a problem where Kodi's built in function for seeking would occur, returning the current channel's video to virtually the beginning (i.e. to a number of seconds from the start equal to the channel # you've entered) before changing to the new channel.  This would give the appearance that the original channel had reset.  It seems impossible to disable Kodi's seek function, but i've changed the channel changing mechanism so that you only need to input a number of numbers equal to your maximum number of visible channels, and the channel will change automatically without hitting enter.  This means if you have less than 100 (visible) channels, input 05 to go to channel five, 50 to go to channel 50, etc..  If you have over 100 channels, input 005, 050, etc..  You can still press 5 and then Enter/OK if you prefer.

* Jump to previous channel.  A standard TV remote function, now available in PSTV!  This is mapped to your ACTION_PREV_PICTURE key, if you have one (it's normally used for Picture Slideshows in Kodi).  If not you can map it to any key by editing your Keymap in the GLOBAL section (NOT the FullscreenVideo section) like so (mapping to the Q button in my example, you can pick what you want):

```
<keymap>
    <global>
        <keyboard>
			<!-- leave other stuff already here -->
			
			<q>PreviousPicture</q>
		</keyboard>
    </global>
	
	<!-- leave other stuff already here -->
	
</keymap>
```

* Reset Watched. I've completely reworked this for a major performance improvement (and a working progress bar!).  Also fixed a bug where it wasn't resetting if you were hiding Season/Year info.

* Directory Channel Episode Plot. For directory channels, instead of just displaying the file path as the episode plots, i've introduced some boiler plate text.  By default it's "Join [Channel Name] for "File Name]" but you can customize it by editing values 30193 & 30194 in your language's strings.po file.  Note that the spaces are part of the string so that if you don't want one, you can remove it, e.g. "It's [Channel Name]'s special showing of [File Name]".  Values can also be blank (i.e. if you want to start with the channel name, set the first one to "").  Let me know if anyone misses seeing the file path; i just felt it took you out of the experience.

*Artist/Band name will now be listed for music videos.

### NEW SETTING PARAMETERS

* Added 1 second option for Changing Channel Info Duration.  Sometimes you just want to quickly see what's on the current channel without having the window lingering.

* Added setting to configure the Brightness value for the auto-created black & white watermarks versions of your channel logos.  Also added the ability to have color watermarks.  I've found that a Brightness value of 1 (which is unchanged from the original) results in much better looking watermarks for my custom logos.  Note that you'll have to delete the old channel bug under \Kodi\userdata\addon_data\script.pseudotv\cache\ChannelBug before you'll see the change.  I could also expose the ability to control the sharpness and/or constrast level, so let me know if there's interest in that.  Honestly, though, i think you are better off manually editing the images in your cache\ChannelBug folder if it comes to that.

* There is now the option for single show channels of displaying the episode name instead of the show name the EPG.  When every episode is from the same show, it seems silly to display the show title over and over again.  But if you disagree you can turn this option off.

* This one's a bit esoteric, but i've separated the Hiding of the Coming Up notification box DURING short videos vs. the hiding of notifications OF short videos.  The one setting used to do both (and hide Short Videos from the EPG).  Personally i didn't want to hide nofications OF short videos, but i did want to stop notifications DURING short videos (because they would appear like halfway through the video).  So i've spearated it out. 

* Hide Leading Zeroes.  This is to accommodate the change to channel changing via number inputs, as described above.  By default, the channel numbers will now display in the appropriate number of digits (2 if you have less than 100 channels, otherwise 3).  This is the way i prefer it; if you type 05 to change to channel 5, it should remain 05.  But i can see some people hating the leading zero, so you can turn it off.  The 0 will still display when you type it, of course, but it will disappear after the channel changes, and won't appear when surfing with the arrow buttons or EPG.

### PERFORMANCE TWEAKS

* Max Needed Channels. The highest number of allowed channels in PSTV is 999, and there are a few places in Kodi where that was hardcoded.  For example, to discover the maximum number of channels that you've configured, PSTV would iterate through all 999 possibilities.  I've paramatized that value so that if you are using significantly less than 999 channels (which i suspect is true of most of us), you can set it to something closer to your actual highest channel and PSTV will have less work to do.  It won't make a huge difference, but 999 seems excessive so i thought i might as well make it possible to reduce it.  This will also make the scroll bar area in the Channel Config more useful.  I'm defaulting it to 200, so IF YOU HAVE MORE CHANNELS THAN THAT (including channels marked as Don't Play because you are interleaving) make sure to increase the number.  Please be sure to leave at least one blank channel; it's necessary for some of the Channel Config functionality like Swap and Copy/Paste.  The performance gains here will be minor and to the extent that they'll be seen, it's about not having to go through 999 channels when you only need 200, not about the difference between 150 and 200.  So err on the side of giving yourself some breathing room.

* Delay Before and After Changing Channel. These two values were hardcoded, and i've turned them into parameters that you can set.  channelDelay determines how many miliseconds before actually changing channels when you've requested a channel change.  holdActions determines how long PSTV blocks you from doing anything (by ignoring your button presses) after changing a channel.  I've found that i could reduce these values with no ill effect, and with a major difference in performance feel.  I'm defaulting to the original values for now.  But i recommend playing with them and seeing if anything bad happens (e.g. too much of the "Working" pop-up, crashes, channels mysteriously restting, etc.) on your computer.  Let me know if reducing the values causes problems for you as i'm considering eventually lowering the default values.  I currently have channelDelay = 100 and holdActions = .25 and my PSTV experience feels so much faster.

* Skipped Videos. I've discovered that PSTV was skipping over a number of my videos due to the fact that it could not determine the duration.  This despite the fact that Kodi could play the video fine, VLC could play it fine, Windows Explorer could determine the duration, etc..  I'm not able to "fix" PSTV's parsing method, but i've done the following: PSTV will now always write the path of the files it is skipping to the main Kodi log.  You have the option of turning on an alert that will pop up if PSTV can't find a video's duration (if you're like me, you may find out that you have a lot and this will be annoying so you'll keep it off most of the time).  You also have the option to have PSTV try to assign a default duration.  This could cause problems in the Episode Guide if the default value doesn't match reality (and/or if the video really is corrupted), but for me at least, it's added many perfectly playable videos that were missing.  I've also found that just running a video through something like MKVToolNix will make it possible for PSTV to recognize it.

### OTHER
* The new settings necessitated a modest reorg of the Settings area.

* Also you may be interested in my script.openinfowindow and service.autosub, both of were created with PSTV in mind.

* This is not a new feature, but something that i think a lot of people aren't aware of.  If you are annoyed by the apparance of the seeker bar every time you change a channel, or if you find that sometimes instead of the PSTV Info screen you get the Kodi default/skin Info screen, or if you don't want to see the Seek numbers appear when you input numbers to change a channel, PSTV unfortunately has no control over these things.  But it's easy for you to put in a conditional visiblity for your skin.  The bottom of the readme has the instructions.  The only trick is if you are using the default Estuary skin, you first have to make a copy of it and put it in your userdata folder or (better) import it via Addons as a new skin.  If people need help with this let me know and i can put up more detailed instructions.

* Another "FYI" (triggered by issue #51 on SteveB's branch) - it's possible to backup your PSTV settings so that you can restore them if they get reset to defaults for some reason.  You can back up your settings by making a copy of \Kodi\userdata\addon_data\script.pseudotv\, and if PSTV should crash and revert, you can paste your files back into that folder.  The Backup program available in the Kodi repository backs these files up if you set it to include Addon Data, so you can schedule that to run on a regular basis if need be.  Or do a manual backup after you make changes in the Config area.
