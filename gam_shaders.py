# -*- coding: utf-8 -*-
from __future__ import division

from gam_import import *
from math import cos,sqrt
import sfml



''' Example use
        #initialize
        from gam_shaders import ShaderManager
        shader=ShaderManager('waterripple',screen,screensize.size)

        #apply
        scr=user.screen
        shader.apply(scr,screensize.size)

        #on clicks
        shader.on_click(user.mouse_pos(),screensize.size )
'''

class ShaderManager():
    def __init__(self,shadername,screen,size):
        shader=LightFS()
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

    def apply(self,scr,size):
        falsewindow=self.falsewindow
        shader=self.shader
        texture=self.texture
        self.pg_to_sfml(scr,size,texture)
        shader.set_texture(texture)
        x,y=user.mouse_pos()/array(size,dtype='float')
        shader.update(pg.time.get_ticks()/1000., x, y,size)
        falsewindow.clear(sfml.Color.WHITE)
        falsewindow.draw(shader)
        falsewindow.hide()
        texture.update_from_window(falsewindow)
        falseimage=texture.to_image()
        #falseimage=pg.image.frombuffer(bytearray(falseimage.pixels.data), screensize.size, 'RGBA')
        #if shader.blend_mode=='add':
            #scr.blit(falseimage,(0,0),None,pg.BLEND_ADD )
        #else:
            #scr.blit(falseimage,(0,0) )
        ##user.screen=falseimage
        bff=scr.get_buffer()
        #todrop=str(falseimage.pixels.data)
        #todrop=pilImage.fromstring("RGBA",screensize.size,todrop).tostring("raw","RGB")
        #todrop=pilImage.fromstring("RGBA",screensize.size,str(falseimage.pixels.data),"raw")
        #b,g,r,a = todrop.split()
        #todrop = pilImage.merge("RGBA", (r, g, b,a))
        #print cvtColor(array(todrop), COLOR_RGB2BGR).shape

        #todrop = pilImage.fromarray( cvtColor(array(todrop), COLOR_RGB2BGR) )

        #bff.write(str(todrop.tostring("raw","RGBA") ),0)
        bff.write(str(falseimage.pixels.data),0)
        del bff


class Effect(sfml.Drawable):
    def __init__(self, name):
        sfml.Drawable.__init__(self)

        self.blend_mode='normal'
        self._name = name
        self.is_loaded = False

    def _get_name(self):
        return self._name

    def load(self,texture=None,screensize=None):
        self.is_loaded = sfml.Shader.is_available() and self.on_load(texture,screensize)

    def update(self, time, x, y,screensize):
        if self.is_loaded:
            self.on_update(time, x, y,screensize)

    def draw(self, target, states):
        if self.is_loaded:
            self.on_draw(target, states)
        else:
            raise Exception('Shader not supported')

    name = property(_get_name)

    def on_click(self,coords,screensize):
        return

    def on_draw(self, target, states):
        states.shader = self.shader
        target.draw(self.sprite, states)

class SphereMap(Effect):
    def __init__(self,texture=None):
        Effect.__init__(self, 'spheremap')
        #self.blend_mode='add'
        self.texture=texture
        self.centerlist=[]

    def set_texture(self,texture):
        if texture:
            self.texture = texture
            #texture.repeated=True
            if self.is_loaded:
                self.shader.set_parameter("texture")


    def on_load(self,texture=None,screensize=None):
        # load the texture and initialize the sprite
        self.set_texture(texture)
        self.sprite = sfml.Sprite(self.texture)

        # load the shader
        self.shader = sfml.Shader.from_file(fragment="shaders/spheremap.glsl")
        self.shader.set_parameter("texture")
        return True

    def on_update(self, time, x, y,screensize):
        self.shader.set_parameter("time",time+int(x*screensize[0])+int(y* screensize[1]))
        self.shader.set_vector2_paramater("resoluton", sfml.Vector2(screensize[0] , screensize[1] ))
        self.shader.set_vector2_paramater("mousepos", sfml.Vector2(x,y ))


    def on_click(self,coords,screensize):
        w,h=screensize
        x,y=coords
        self.centerlist.append( sfml.Vector2(x/float(w),1.0-y/float(h)))



class LightFS(Effect):
    def __init__(self,texture=None):
        Effect.__init__(self, 'lightfs')
        #self.blend_mode='add'
        self.texture=texture
        self.centerlist=[]

    def set_texture(self,texture):
        if texture:
            self.texture = texture
            if self.is_loaded:
                self.shader.set_parameter("texture")


    def on_load(self,texture=None,screensize=None):
        # load the texture and initialize the sprite
        self.set_texture(texture)
        self.sprite = sfml.Sprite(self.texture)

        # load the shader
        self.shader = sfml.Shader.from_file(fragment="shaders/lightfs.frag")
        self.shader.set_parameter("texture")
        return True

    def on_update(self, time, x, y,screensize):
        self.shader.set_vector3_paramater("lightColor", sfml.Vector3(100 , 100,200))
        self.shader.set_parameter("radius", rint( 500.*(1+cos(2* time) )) )
        self.shader.set_parameter("screenHeight", screensize[1] )
        self.shader.set_vector2_paramater("lightpos", sfml.Vector2(x*screensize[0] ,y* screensize[1] ))
        g=.1*(5.+cos(4* time))
        self.shader.set_vector3_paramater("lightAttenuation", sfml.Vector3(0.,0.,(.5+y)*g))

    def on_click(self,coords,screensize):
        w,h=screensize
        x,y=coords
        self.centerlist.append( sfml.Vector2(x/float(w),1.0-y/float(h)))


class StarNest(Effect):
    def __init__(self,texture=None):
        Effect.__init__(self, 'starnest')
        #self.blend_mode='add'
        self.texture=texture

    def set_texture(self,texture):
        if texture:
            self.texture = texture
            if self.is_loaded:
                self.shader.set_parameter("texture")


    def on_load(self,texture=None,screensize=None):
        # load the texture and initialize the sprite
        self.set_texture(texture)
        self.sprite = sfml.Sprite(self.texture)

        # load the shader
        self.shader = sfml.Shader.from_file(fragment="shaders/starnest.frag")
        self.shader.set_parameter("texture")
        return True

    def on_update(self, time, x, y,screensize):
        self.shader.set_parameter("time", time )
        self.shader.set_vector2_paramater("mouse", sfml.Vector2(*screensize ))#sfml.Vector2(x*screensize[0] ,y* screensize[1] ))
        self.shader.set_vector2_paramater("resolution", sfml.Vector2(*screensize ))


class WaterRipple(Effect):
    def __init__(self,texture=None):
        Effect.__init__(self, 'waterripple')
        self.texture=texture
        self.time=0


    def set_texture(self,texture):
        if texture:
            self.texture = texture
            self.texture.smooth=True
            if self.is_loaded:
                self.water_final.set_parameter("backgroundTex",self.texture)

    def on_load(self,texture=None,screensize=None):
        w,h=screensize
        self.set_texture(texture)
        self.buffer1=buffer1 = sfml.RenderTexture(w,h);
        self.buffer2=buffer2 = sfml.RenderTexture(w,h);

        buffer1.clear();
        buffer2.clear();

        #textures
        #background=sfml.Texture();

        self.water_map=water_map=sfml.Texture.from_file("shaders/gradient_map.png");
        water_map.repeated=True
        water_map.smooth=True

        #shaders
        self.water_raw=water_raw=sfml.Shader.from_file(fragment="shaders/water_raw.glsl");
        water_raw.set_parameter("textureSize",sfml.Vector2(w,h));

        self.water_final=water_final=sfml.Shader.from_file(fragment="shaders/water_final.glsl");
        water_final.set_vector2_paramater("textureSize",sfml.Vector2(w,h));
        water_final.set_vector2_paramater("moveVec",sfml.Vector2(0.1,0.4))
        water_final.set_parameter("backgroundTex",self.texture);
        water_final.set_parameter("wavesTex",water_map);
        water_final.set_vector3_paramater("lightVector",sfml.Vector3(0.43,0.86,0.71));
        self.sprite=sfml.Sprite(self.texture);
        return True


    def on_update(self, time, x, y,screensize):
        water_raw=self.water_raw
        buffer1=self.buffer1
        buffer2=self.buffer2
        self.time+= 0.01
        self.water_final.set_parameter("time",self.time);
        water_raw.set_parameter("textureTwoFramesAgo", buffer1.texture);
        water_raw.set_parameter("textureOneFrameAgo", buffer2.texture);
        buffer2.display();
        buffer1.display();
        self.sprite.texture=(buffer2.texture);

        states=sfml.RenderStates()
        states.shader=self.water_raw
        self.buffer1.draw(self.sprite,states);
        #buffer1.display();

    def on_draw(self, target, states):
        self.sprite.texture=(self.buffer2.texture);
        states=sfml.RenderStates()
        states.shader=self.water_final
        target.clear()
        target.draw(self.sprite,states);
        self.buffer1,self.buffer2 = self.buffer2,self.buffer1


    def on_click(self,coords,screensize):
        w,h=screensize
        x,y=coords
        self.water_raw.set_vector2_paramater("mousePosition",sfml.Vector2(x/float(w),1.0-y/float(h)));
        lx,ly,lz=x/float(w)-.5,y/float(h)-.5,1
        norm=sqrt(lx*lx+ly*ly+lz*lz)
        lx,ly,lz=lx/norm,ly/norm,lz/norm
        self.water_final.set_vector3_paramater("lightVector",sfml.Vector3(lx,ly,lz))