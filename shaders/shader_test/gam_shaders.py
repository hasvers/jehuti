# -*- coding: utf-8 -*-
from __future__ import division

from gam_shadtypes import *



''' Example use
        #initialize
        from gam_shaders import ShaderManager
        shader=ShaderManager('waterripple',screen,screensize.size)

        #apply
        scr=user.screen
        shader.apply(scr,user.mouse_pos(),screensize.size)

        #on clicks
        shader.on_click(user.mouse_pos(),screensize.size )
'''

class ShaderManager():
    shadtyp={'lightfs':LightFS,
    'waterripple':WaterRipple,
    'normallight':NormalLight,
    }

    def __init__(self,shadername,screen,size,**kwargs):
        shader=self.shadtyp[shadername](**kwargs)
        w,h=size
        falsewindow = sfml.RenderWindow(sfml.VideoMode(w,h), "pySFML - Shader")
        falsewindow.hide()
        #falsewindow.vertical_synchronization = True
        texture=sfml.graphics.Texture.create(w,h)
        self.pg_to_sfml(screen,(w,h),texture)
        shader.load(texture,size)
        self.falsewindow=falsewindow
        self.shader=shader
        self.texture=texture


    def pg_to_sfml(self,screen,screensize, texture):
        mtest=sfml.window.Pixels( )
        test=pg.image.tostring(screen,'RGBA')
        mtest.data,mtest.width, mtest.height=bytes(test),screensize[0],screensize[1]
        texture.update_from_pixels(mtest)

    def on_click(self,*args):
        self.shader.on_click(*args)

    def apply(self,scr,mousepos,size):
        falsewindow=self.falsewindow
        shader=self.shader
        texture=self.texture
        self.pg_to_sfml(scr,size,texture)
        
        shader.set_texture(texture) #pass the screen as texture to the sprite
        x,y=mousepos/array(size,dtype='float')
        shader.update(pg.time.get_ticks()/1000., x, y,size)
        
        falsewindow.clear(sfml.Color.WHITE)
        falsewindow.draw(shader)
        falsewindow.hide()
        texture.update_from_window(falsewindow)
        falseimage=texture.to_image()
        
        bff=scr.get_buffer()
        bff.write(str(falseimage.pixels.data),0)
        del bff


