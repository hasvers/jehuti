from gam_shaders import ShaderManager    
import pygame as pg

scrsize=(400,521)

screen = pg.display.set_mode(scrsize )

clock = pg.time.Clock()
pg.display.set_caption('Graphview')
pg.init()
bg=pg.image.load('background.jpg')
bg2=pg.image.load('perso2a.png')


shader=ShaderManager('lightfs',screen,scrsize)
shader=ShaderManager('normallight',screen,scrsize,normals= 'perso2a_NORMALS.png')
#shader=ShaderManager('waterripple',screen,scrsize)

FPS=45

from ffmpegwriter import FFMPEG_VideoWriter
video=None
rec=0

quit=0
while not quit:
            screen.fill((0,0,0))
            screen.blit(bg,(0,0))
            screen.blit(bg2,(0,0))
            shader.apply(screen,pg.mouse.get_pos(),scrsize)
            clock.tick(FPS)
            pg.display.update()
            pg.display.set_caption('Shader test  %d fps' % clock.get_fps())
            for event in pg.event.get():
                if True in (tuple(pg.key.get_pressed()[i] 
                        for i in (pg.K_RCTRL,pg.K_LCTRL) )):
                    ctrlmode=True
                else:
                    ctrlmode=False
                if event.type==pg.KEYUP and ctrlmode and event.key==pg.K_r:
                    rec=1-rec
                    if rec:
                        print 'Start recording'
                        if not video:
                            video=FFMPEG_VideoWriter('video.mp4',scrsize,FPS,'libx264')
                    else:
                        print 'Stop recording'
                    
                if event.type==pg.MOUSEBUTTONUP:
                    if event.button==1:
                        shader.on_click(pg.mouse.get_pos(),scrsize)
                    if event.button==5:
                        if ctrlmode:
                            shader.shader.lightcolor[0]= (shader.shader.lightcolor[0]+.05)%1.
                        else:
                            shader.shader.z*=1.1
                    if event.button==4:
                        if ctrlmode:
                            shader.shader.lightcolor[0]= (shader.shader.lightcolor[0]-.05)%1.
                        else:
                            shader.shader.z/=1.1
                    
                if event.type == pg.QUIT:
                    if video:
                        video.close()
                    pg.quit()
                    quit=1
            if rec:
                pil_string_image = pg.image.tostring(screen, "RGB")
                video.write_frame(pil_string_image)

pg.quit()

