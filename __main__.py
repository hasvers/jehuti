# -*- coding: utf-8 -*-
import sys,site,os
database={}
database['basepath']=os.path.normpath('./Jeu/')
from gam_winfields import *
from gam_canvasicons import *
from gam_canvas import *
from gam_gui import *


pgdisplayflags={'full':pg.FULLSCREEN|pg.DOUBLEBUF|pg.HWSURFACE,'window':0}
if database['resizable_window']:
    pgdisplayflags['window'] |=pg.RESIZABLE

def windowed_size():
    w,h=graphic_chart['screen_size']
    wmax,hmax=pg.display.list_modes()[0]
    if wmax<w:
        w=wmax
    if hmax<h:
        h=hmax
    return (w,h)

def toggle_fullscreen():
    try:
        screen = pg.display.get_surface()
        tmp = screen.convert()
        caption = pg.display.get_caption()
        cursor = pg.mouse.get_cursor()  # Duoas 16-04-2007

        #w,h = screen.get_width(),screen.get_height()
        flags = screen.get_flags()
        bits = screen.get_bitsize()


        pg.display.quit()
        pg.display.init()
        if flags & pg.FULLSCREEN:
            w,h=windowed_size()
            screen = pg.display.set_mode((w,h),pgdisplayflags['window'],bits)
            screen.fill((0,0,0))
        else:
            w,h=pg.display.list_modes()[0]
            screen = pg.display.set_mode((w,h), pgdisplayflags['full'],bits)
            screen.fill((0,0,0))
        screen.blit(tmp,(0,0))
        pg.display.set_caption(*caption)
        pg.key.set_mods(0) #HACK: workaround for a SDL bug??
        pg.mouse.set_cursor( *cursor )
        return screen
    except Exception as e:
        fout=open('error.dat','w')
        fout.write(str(e))
        fout.close()
        user.ui.make_balloon("Error: Your system does not allow fullscreen toggling.")
        pg.display.init()
        screen = pg.display.set_mode(user.screen.get_rect().size)
    return screen

def prolog(fname):
    stats=[[i.code ,i.totaltime,i.inlinetime,i.callcount,i.reccallcount] for i in profiler.getstats()]
    stats=sorted(stats,key=lambda e:e[1],reverse=1)

    with fopen(fname,'w') as prolog:
        for i in stats:
            if not i:
                continue
            st=' '.join([str(z) for z in  i])
            prolog.write(st+'\n')

def execute(e):
    print '>>', e
    exec(e)

def keymap(event):
    pres=pg.key.get_pressed()
    if database['edit_mode']:
        if event.type== pg.KEYUP and event.key==pg.K_x and (pres[pg.K_LCTRL] and pres[pg.K_LALT]):
            user.ui.input_menu('input',execute)
        if event.type== pg.KEYUP and event.key==pg.K_d and (pres[pg.K_LCTRL] and pres[pg.K_LALT]):
            lst=(user.focused_on, )
            hov=user.ui.hovering
            while hov:
                lst+= (hov,)
                try:
                    hov=hov.hovering
                except:
                    hov=None
            lst+= tuple(z.hovering  for l in user.ui.layers if hasattr(l,'view') and l.view!=l  for z in (l.view,)+tuple(l.view.children) )
            lst+= tuple(l.hovering  for l in user.ui.layers if hasattr(l,'hovering'))
            struct=tuple(( str(i),lambda tgt=i: user.debug(tgt) ) for i in lst if i!=None)
            if struct:
                user.ui.float_menu(struct)

def main():
        pg.display.init()
        user.music=MusicMaster()
        screen=pg.display.set_mode(windowed_size(),pgdisplayflags['window'] )
        screensize=uscreensize=screen.get_rect()
        user.screen= screen.copy()
        pg.display.set_caption(database['title'])
        pg.init()
        pg.scrap.init()
        user.set_ui(StartMenuUI(None))
        scale_vec=user.scale_vec

        pg.key.set_repeat(200,30)
        pg.time.set_timer(30,int(round(1000/ergonomy['animation_fps'])))# Animation pulse: event type 30
        while 1:
            if pgevent.peek(pg.QUIT):
                pg.display.quit()
                return 1
            evts=pgevent.get()
            for event in evts:
                if user.screen_scale!=1 and hasattr(event,'pos'):
                    updict={}
                    updict['pos']=scale_vec(event.pos-user.screen_trans)
                    if hasattr(event,'rel'):
                        updict['rel']= scale_vec(event.rel)
                        updict['buttons']=event.buttons
                    else:
                        updict['button']=event.button
                    #print event.type
                    nevent=pg.event.Event(event.type,updict)
                    #print  nevent.pos,event.pos,user.screen_trans
                    event=nevent
                #screen.fill((200,200,200,255))
                if user.ui.event(event) or event.type==30:
                    user.ui.update()
                    if user.recording :#and pg.time.get_ticks()%100<10:
                        if user.last_recorded%10==0:
                            pg.image.save(user.ui.screen,'video/{}.png'.format(user.last_recorded/10) )
                        user.last_recorded+=1
                if event.type==32:
                    user.music.event(event)
                if database['resizable_window'] and event.type==pg.VIDEORESIZE:
                    screensize= event
                    user.screen_scale= min( screensize.size[i]/float(uscreensize.size[i]) for i in (0,1) )
                    user.screen_trans=(array(screensize.size,dtype='int')-scale_vec(uscreensize.size,0))/2
                try:
                    pres=pg.key.get_pressed()
                    if event.type== pg.KEYUP and event.key==pg.K_RETURN and (pres[pg.K_LALT] or pres[pg.K_RALT]):
                        screen=toggle_fullscreen()
                        screensize=screen.get_rect()
                        user.screen_scale= min( screensize.size[i]/float(uscreensize.size[i]) for i in (0,1) )
                        user.screen_trans=(array(screensize.size,dtype='int')-scale_vec(uscreensize.size,0))/2
                    else:
                        keymap(event)
                    if event.type== pg.KEYUP and event.key==pg.K_F4 and (pres[pg.K_LALT] or pres[pg.K_RALT]):
                        pg.quit()
                        return 1
                except:
                    pass
            if evts:
                user.ui.paint()
                if user.screen_scale!=1:
                    screen.fill( (0,0,0))
                    screen.blit(pg.transform.smoothscale(user.screen,scale_vec(uscreensize.size,0)),user.screen_trans)
                else:
                    screen.blit(user.screen,(0,0))
            clock.tick(140)
            pg.display.update()
            if database['edit_mode']:
                pg.display.set_caption(database['title']+'  %d fps' % clock.get_fps())

'''    except :
        print traceback.print_tb(sys.exc_info()[2])
        print sys.exc_info()
    finally :
        pg.quit()
        return 0
        '''
#cProfile.run('main()',None,1)

#profiler.runcall(main)
main()
#prolog('prolog.dat')
print 'Quitting...',[pgmixer.Channel(x).get_busy() for x in range(pgmixer.get_num_channels() )]
[pgmixer.Channel(x).stop()  for x in range(pgmixer.get_num_channels() )]
print 'Done.',[pgmixer.Channel(x).get_busy() for x in range(pgmixer.get_num_channels() )]
pg.quit()
