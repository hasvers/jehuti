# -*- coding: utf-8 -*-
from gv_globals import *
from gv_resources import ResourceLibrary
import sfml
from multiprocessing import Process
#import scikits.audiolab as al #for array manipulation


class AudioLibrary(ResourceLibrary):
    '''Temporarily, only stocks the path to sounds.
    In the future, may stock the sounds themselves'''
    def load_defs(self,fname):
        for line in fopen(database['basepath']+fname):
            l=line.split()
            if len(l)>1:
                self.buffer[l[0]]=l[1]


sound_bank=AudioLibrary()
sound_bank.load_defs('sound_bank.ini')

class MixerSubstitute(object):
    '''Alternative to pygame's mixer in which the outgoing
    stream is made available '''
    debug_mode=0

    class OutgoingStream(sfml.audio.SoundStream):

        def onGetData(data):
            return 'yes'

    class SoundObject(object):
        '''Wrapper for SFML music object'''
        def __init__(self,src,typ='sound'):
            self.typ=typ
            if typ=='sound':
                self.buffer=src
                self.obj=sfml.Sound(src)
            elif typ=='music':
                self.buffer=self.obj=sfml.Music.from_file(src)
            self.fadein=0
            self.fadeout=0
            self.kill_in=None
        @property
        def volume(self):
            return self.obj.volume
        @volume.setter
        def volume(self,vol):
            self.obj.volume=vol
        def play(self):
            return self.obj.play()
        def pause(self):
            return self.obj.pause()
        def stop(self,fadeout=0):
            if not fadeout:
                return self.obj.stop()
            else:
                self.kill_in=fadeout
        @property
        def duration(self):
            return self.buffer.duration.milliseconds
        @property
        def sample_rate(self):
            return self.buffer.sample_rate
        @property
        def channel_count(self):
            return self.buffer.channel_count
        @property
        def status(self):
            return self.obj.status


    def __init__(self):
        self.stream=sfml.audio.SoundStream
        self.buffers={}
        #self.threads={}
        self.permanent=None

    def check_audio(self,audio):
        '''Check that an audio file has the right samplerate '''
        pass
            #samplerate=mutagen.File(path).info.bitrate
            #print mutagen.File(path).info.length
            #freq,form,chans=pg.mixer.get_init()
            #print samplerate,freq
            #if 0 and samplerate!= freq:
                #pg.mixer.quit()
                #pg.mixer.init(samplerate,form,chans)

    def play_sound(self,filename,**kwargs):
        # load a sound buffer from a wav file
        buff=self.buffers.get(filename,None)
        if buff is None:
            buff = sfml.SoundBuffer.from_file(filename)
            self.buffers[filename]=buff


        if self.debug_mode:
            # display sound informations
            print filename
            print("{0} milliseconds".format(buff.duration))
            print("{0} samples / sec".format(buff.sample_rate))
            print("{0} channels".format(buff.channel_count))

        # create a sound instance and play it
        sound = self.SoundObject(buff)
        sound.fadein=kwargs.get('fadein',0)
        sound.fadeout=kwargs.get('fadeout',0)

        p=sfml.Thread(self.thread,sound, kwargs['volume']*100,kwargs.get('loop',0))
        p.launch()

    def play_music(self,filename,**kwargs):
        # load an ogg music file
        music = self.SoundObject(filename,'music')
        music.fadein=kwargs.get('fadein',0)
        music.fadeout=kwargs.get('fadeout',0)

        if self.debug_mode:
            # display music informations
            print filename
            print("{0} milliseconds".format(music.duration))
            print("{0} samples / sec".format(music.sample_rate))
            print("{0} channels".format(music.channel_count))

        if self.permanent:
            perm=self.permanent
            self.permanent=music
            if not kwargs.get('queue',False):
                perm.stop()
            else:
                perm.fadeout=600
        else:
            self.permanent=music
            p=sfml.Thread(self.thread , music,kwargs['volume']*100)
            p.launch()

    def thread(self,sound,volume, loops=0):
        sound.play()
        sound.volume=rint(volume)
        # loop while the sound is playing
        time=0
        killtime=0
        deltat=10
        while sound.status in ( sfml.Sound.PLAYING,sfml.Sound.PAUSED) :
            # leave some CPU time for other processes
            sfml.sleep(sfml.milliseconds(deltat))
            time+=deltat
            if sound.fadein and time < sound.fadein:
                sound.volume=rint(volume *float(time)/sound.fadein )
            if sound.fadeout and time> sound.duration-sound.fadeout:
                sound.volume=rint(volume *float(time)/(rint(volume *float(time)/sound.fadein ) ))
            if not sound.kill_in is None:
                killtime +=deltat
                if killtime> sound.kill_in:
                    sound.stop()
                    sound.kill_in=None
                    break
                else:
                    sound.volume*= 1-float(killtime/sound.kill_in)
        if loops>0:
            self.thread(sound,volume,loops-1)
        if self.permanent==sound:
            self.thread(sound,volume)
        elif self.permanent and sound.typ=='music':
            self.thread(self.permanent,volume)

    def advance(self):
        #should be called at regular time intervals deltat to play the next chunk
        time=pg.time.get_ticks() - self.last_advance
        if not 0.9< float(time) / self.deltat < 1.1:
            #Check whether deltat is different from expected,
            #to load less or more at a time for the next iteration
            self.deltat=time

    def quit(self):
        if self.permanent:
            perm=self.permanent
            self.permanent=None
            perm.stop()


myMixer=MixerSubstitute()

class SoundMaster(object):
    SMid=0
    defaultvol=.5
    mute=0
    #Receives signals from UI and makes sounds
    def __init__(self,parent,channel=0):
        self.mixer=myMixer
        self.parent=parent
        #self.channel=pgmixer.Channel(SoundMaster.SMid)
        self.channels={}
        #self.channel.set_volume(self.defaultvol)
        SoundMaster.SMid+=1
        #if channel>pg.mixer.get_num_channels():
            #raise Exception('Not enough audio channels')

    def play(self,snd,vol=None, **kwargs):
        if self.mute:
            return
        if not snd in sound_bank:
            return False
        kwargs.setdefault('volume',self.defaultvol)
        #self.mixer.play_sound(database['sound_path']+'{}.wav'.format(snd), **kwargs)
        self.mixer.play_sound(database['sound_path']+sound_bank[snd], **kwargs)
        return
        #PURE PYGAME IMPLEMENTATION
        #loop=kwargs.get('loop',0)
        #fadein=kwargs.get('fadein',0)
        #try:

            #if snd in self.channels:
                #channel=self.channels[snd]
            #else:
                #channel=pg.mixer.find_channel()
                #for i, j in tuple( self.channels.iteritems() ):
                    #if j==channel:
                        ##ended sound
                        #del self.channels[i]
            #if vol:
                #channel.set_volume(vol)
            #else:
                #channel.set_volume(self.defaultvol)
            #if channel.get_busy():
                #channel.stop()
                ##print 'Cutting short',channel
            #channel.play(sound_bank[snd],loop,0,fadein)
            #self.channels[snd]=channel
        #except:
            #pass

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
            self.mixer.pause()
            self.mute=1
        else:
            self.mixer.unpause()
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
        self.mixer=myMixer


    def play(self,music,**kwargs):
        if self.current==database['music_path']+music:
            return
        if not music in os.listdir(database['music_path']):
            print "Music unavailable: {}".format(music)
            return
        if self.mute:
            self.queue.append(music)
            return
        path=database['music_path']+music
        self.current=path
        kwargs.setdefault('volume',self.volume)
        self.mixer.play_music(path, **kwargs)

        #if self.current:
            #self.add(music)
            #pg.mixer.music.fadeout(600)
        #else:
            #path=database['music_path']+music

            #try:
                #pg.mixer.music.load(path)
                #pg.mixer.music.set_volume(self.volume)
                #pg.mixer.music.play(-1, self.current_time)
                #self.current=path
            #except:
                #print "No music available."

    def stop(self):
        #pg.mixer.music.fadeout(600)
        if self.mixer.permanent:
            self.mixer.permanent.stop(600)
        self.current=None

    #def add(self,music):
        ##pg.mixer.music.queue(database['music_path']+music) #wont work with infinite loops
        #self.queue.append( music)
        #music.set_endevent(32)
        #pg.mixer.music.set_endevent(32)

    #def event(self,event):
        #if event.type==32 and self.queue:
            #pg.mixer.music.set_endevent()
            #pg.mixer.music.stop()
            #self.current=None
            #self.play(self.queue.pop(0))

    def trigger(self):
        if not self.mute:
            if self.mixer.permanent:
                self.mixer.permanent.pause()
            self.mute=1
        else:
            if not self.current and self.queue:
                self.play(self.queue.pop(0))
            else:
                self.mixer.permanent.play()
            self.mute=0

