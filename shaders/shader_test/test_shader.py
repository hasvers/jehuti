from gam_shaders import ShaderManager    
import pygame as pg


screen = pg.display.set_mode( (800,600) )

clock = pg.time.Clock()
pg.display.set_caption('Graphview')
pg.init()
bg=pg.image.load('background.jpg')

bg2=pg.image.load('crossColor.jpg')
bg2=pg.image.load('perso2a.png')
bg2=pg.image.load('test.jpg')

bg2=pg.image.load('10113-diffuse.jpg')
bg2=pg.image.load('Crossbw2.png')
bg2=pg.image.load('compass.png')

scrsize=bg2.get_rect().size

screen = pg.display.set_mode(scrsize )

shader=ShaderManager('lightfs',screen,scrsize)
shader=ShaderManager('normallight',screen,scrsize,normals= 'perso2a_NORMALS.png')
shader=ShaderManager('normallight',screen,scrsize,normals= 'Crossbw2_NORMALS.png')
shader=ShaderManager('normallight',screen,scrsize,normals= 'test.jpg',specular= 'test.jpg') #FROZEN
shader=ShaderManager('normallight',screen,scrsize,normals= 'crossNRM.jpg',specular= 'cross_SPECULAR.png')
#shader=ShaderManager('normallight',screen,scrsize,normals= 'cross_NORMALS.png',specular= 'cross_SPECULAR.png')
shader=ShaderManager('normallight',screen,scrsize,normals= 'crossNRM_NORMALS.png',specular= 'crossNRM_SPECULAR.png')

shader=ShaderManager('normallight',screen,scrsize,normals= '10113.jpg',specular= '10113AO.jpg')
shader=ShaderManager('normallight',screen,scrsize,normals= 'Crossbw2_NORMALS.png',specular= 'Crossbw2_NORMALS.png')
shader=ShaderManager('normallight',screen,scrsize,normals= 'compass_NORMALS.png',specular='compass_SPECULAR.png')

#shader=ShaderManager('waterripple',screen,scrsize)

FPS=60

from ffmpegwriter import FFMPEG_VideoWriter
video=None
rec=0

quit=0
while not quit:
            screen.fill((100,100,100))
            #screen.blit(bg,(0,0))
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
                    
                if event.type==pg.KEYUP and ctrlmode and event.key==pg.K_s:
                    shader.shader.use_spec(1- shader.shader.using_spec)
                if event.type==pg.MOUSEBUTTONUP:
                    if event.button==1:
                        shader.on_click(pg.mouse.get_pos(),scrsize)
                    if event.button==5:
                        if ctrlmode:
                            shader.shader.lightcolor[3]= (shader.shader.lightcolor[3]-.05)%1.
                        else:
                            shader.shader.z*=1.1
                    if event.button==4:
                        if ctrlmode:
                            shader.shader.lightcolor[3]= (shader.shader.lightcolor[3]+.05)%1.
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

