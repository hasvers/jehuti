# -*- coding: utf-8 -*-
from gv_globals import *
#import mutagen #Non-fonctional

class SoundMaster(object):
    SMid=0
    defaultvol=.5
    mute=0
    #Receives signals from UI and makes sounds
    def __init__(self,parent,channel=0):
        self.parent=parent
        #self.channel=pgmixer.Channel(SoundMaster.SMid)
        self.channels={}
        #self.channel.set_volume(self.defaultvol)
        SoundMaster.SMid+=1
        if channel>pgmixer.get_num_channels():
            raise Exception('Not enough audio channels')
    def play(self,snd,vol=None, **kwargs):
        if self.mute:
            return
        loop=kwargs.get('loop',0)
        fadein=kwargs.get('fadein',0)
        try:
            if snd in self.channels:
                channel=self.channels[snd]
            else:
                channel=pg.mixer.find_channel()
                for i, j in tuple( self.channels.iteritems() ):
                    if j==channel:
                        #ended sound
                        del self.channels[i]
            if vol:
                channel.set_volume(vol)
            else:
                channel.set_volume(self.defaultvol)
            if channel.get_busy():
                channel.stop()
                #print 'Cutting short',channel
            channel.play(sound_bank[snd],loop,0,fadein)
            self.channels[snd]=channel
        except:
            pass

    def stop(self,snd, **kwargs):
        if snd in self.channels:
            fadeout=kwargs.get('fadeout',0)
            if fadeout:
                self.channels[snd].fadeout(fadeout)
            else:
                self.channels[snd].stop()
            del self.channels[snd]

    def set_volume(self,snd,vol):
        if snd in self.channels:
            self.channels[snd].set_volume(vol)

    def trigger(self):
        if not self.mute:
            pg.mixer.pause()
            self.mute=1
        else:
            pg.mixer.unpause()
            self.mute=0

class MusicMaster(object):
    defaultvol=.5
    mute=0
    def __init__(self):
        self.current=None
        self.current_time=0
        self.volume=self.defaultvol
        self.queue=[]
        self.mute=database['no_music']

    def play(self,music):
        if self.current==database['music_path']+music:
            return
        if self.mute:
            self.queue.append(music)
            return
        if self.current:
            self.add(music)
            pg.mixer.music.fadeout(600)
        else:
            path=database['music_path']+music
            #samplerate=mutagen.File(path).info.bitrate
            #print mutagen.File(path).info.length
            #freq,form,chans=pg.mixer.get_init()
            #print samplerate,freq
            #if 0 and samplerate!= freq:
                #pg.mixer.quit()
                #pg.mixer.init(samplerate,form,chans)
            try:
                pg.mixer.music.load(path)
                pg.mixer.music.set_volume(self.volume)
                pg.mixer.music.play(-1, self.current_time)
                self.current=path
            except:
                print "No music available."

    def stop(self):
        pg.mixer.music.fadeout(600)
        self.current=None


    def add(self,music):
        #pg.mixer.music.queue(database['music_path']+music) #wont work with infinite loops
        self.queue.append( music)
        pg.mixer.music.set_endevent(32)

    def event(self,event):
        if event.type==32 and self.queue:
            pg.mixer.music.set_endevent()
            pg.mixer.music.stop()
            self.current=None
            self.play(self.queue.pop(0))


    def trigger(self):
        if not self.mute:
            pg.mixer.music.pause()
            self.mute=1
        else:
            pg.mixer.music.unpause()
            if not self.current and self.queue:
                self.play(self.queue.pop(0))
            self.mute=0
