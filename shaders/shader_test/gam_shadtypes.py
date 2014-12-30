
from gam_globals import *
from math import cos,sqrt
import sfml
import colorsys

class Effect(sfml.Drawable):
    def __init__(self, name):
        sfml.Drawable.__init__(self)

        self.blend_mode='normal'
        self._name = name
        self.is_loaded = False

    def load_shader(self,fname,attr='shader'):
        shader=sfml.Shader.from_file(fragment=resource_path(fname,filetype='shader'))
        setattr(self,attr,shader)
        return shader

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
        
    def set_texture(self,scrtexture):
        if scrtexture:
            if self.is_loaded:
                self.shader.set_parameter("texture")


class SphereMap(Effect):
    def __init__(self):
        Effect.__init__(self, 'spheremap')
        #self.blend_mode='add'
        self.centerlist=[]

    def set_texture(self,scrtexture,repeated=False):
        if scrtexture:
            if repeated:
                scrtexture.repeated=True
            if self.is_loaded:
                self.shader.set_parameter("texture")


    def on_load(self,scrtexture=None,screensize=None):
        # load the texture and initialize the sprite
        self.sprite = sfml.Sprite(scrtexture)

        # load the shader
        self.load_shader("spheremap.glsl")
        return True

    def on_update(self, time, x, y,screensize):
        self.shader.set_parameter("time",time+int(x*screensize[0])+int(y* screensize[1]))
        self.shader.set_vector2_paramater("resoluton", sfml.Vector2(screensize[0] , screensize[1] ))
        self.shader.set_vector2_paramater("mousepos", sfml.Vector2(x,y ))


    def on_click(self,coords,screensize):
        w,h=screensize
        x,y=coords
        self.centerlist.append( sfml.Vector2(x/float(w),1.0-y/float(h)))




class NormalLight(Effect):
    using_spec=True
    
    def __init__(self,basetext=None,normals=None,specular=None,z=.1):
        Effect.__init__(self, 'normallight')
        self.normals=normals
        self.specular=specular
        if specular is None:
            self.using_spec = False
        self.z=z
        self.lightcolor=[1.,0.3,1.,.75]
        self.ambientcolor=[0.5,0.7,0.4,1.]
        self.attenuation=[.1,.0,0.5]

    def set_texture(self,scrtexture):
        if scrtexture:
            if self.is_loaded:
                self.shader.set_parameter("texture")

    def use_spec(self,val=True):
        if self.specular is None and val==True:
            return False
        self.using_spec=val
        if not self.using_spec:
            self.load_shader("normallight.frag")
        else:
            self.load_shader("normalspec.frag")
            self.spectext=spec=sfml.Texture.from_file(self.specular)
            self.shader.set_texture_parameter("specular",spec)
            
    def on_load(self,scrtexture=None,screensize=None):
        # load the shader
        self.sprite = sfml.Sprite(scrtexture)
        self.use_spec(self.using_spec)
        self.normaltext=norm=sfml.Texture.from_file(self.normals)
        self.shader.set_texture_parameter("normals",norm)
        return True

    def on_update(self, time, x, y,screensize):
        g=(5.+cos(4* time))*.2
        lightcol= array(list( colorsys.hsv_to_rgb(*self.lightcolor[:3]))+[self.lightcolor[3]])*255
        self.shader.set_color_parameter("LightColor", sfml.Color(*lightcol))
        ambcol= array(list( colorsys.hsv_to_rgb(*self.ambientcolor[:3]))+[self.ambientcolor[3]])*255
        self.shader.set_color_parameter("AmbientColor", sfml.Color(*ambcol))
        self.shader.set_parameter("Resolution", screensize )
        self.shader.set_texture_parameter("normals",self.normaltext)
        if self.using_spec:
            self.shader.set_texture_parameter("specular",self.spectext)
            self.shader.set_vector3_paramater("eyeDirection", sfml.Vector3(0.,0.,1.))
        self.shader.set_vector3_paramater("LightPos", sfml.Vector3(x ,1.-y ,self.z))
        self.shader.set_vector3_paramater("Falloff", sfml.Vector3(*self.attenuation))#(.5+y)*g)

    def on_click(self,coords,screensize):
        w,h=screensize
        x,y=coords
        

        
class Immersion(Effect):
    '''Transition between two textures that uses a depth map to tell which part
    of the layer below pokes through the layer above. 
    The texture contained is the one that should poke through.'''
    mode='in'
    def __init__(self,tex=None,depth=None):
        Effect.__init__(self, 'immersion')
        #self.blend_mode='add'
        self.texname=tex
        self.depth=depth
    def on_load(self,texture=None,screensize=None):
        # load the texture and initialize the sprite
        self.sprite = sfml.Sprite(texture)

        # load the shader
        self.load_shader("immersion.frag")
        self.tex=tex=sfml.Texture.from_file(self.texname)
        self.shader.set_texture_parameter("poke",tex)
        self.depthtex=tex=sfml.Texture.from_file(self.depth)
        self.shader.set_texture_parameter("depth",tex)

        return True

    def on_update(self, time, x, y,screensize):
        self.shader.set_parameter("z",-float(time/4.-2.)) 
        
class LightFS(Effect):
    def __init__(self):
        Effect.__init__(self, 'lightfs')
        #self.blend_mode='add'
        self.centerlist=[]

    def set_texture(self,scrtexture):
        if scrtexture:
            if self.is_loaded:
                self.shader.set_parameter("texture")


    def on_load(self,texture=None,screensize=None):
        # load the texture and initialize the sprite
        self.sprite = sfml.Sprite(texture)

        # load the shader
        self.load_shader("lightfs.frag")
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
    def __init__(self):
        Effect.__init__(self, 'starnest')
        #self.blend_mode='add'

    def set_texture(self,scrtexture):
        if scrtexture:
            if self.is_loaded:
                self.shader.set_parameter("texture")


    def on_load(self,scrtexture=None,screensize=None):
        # load the texture and initialize the sprite
        self.set_texture(scrtexture)
        # load the shader
        self.load_shader("starnest.frag")
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
            #self.texture.smooth=True
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

        self.water_map=water_map=sfml.Texture.from_file("gradient_map.png");
        water_map.repeated=True
        water_map.smooth=True

        #shaders
        water_raw=self.load_shader("water_raw.glsl",'water_raw');
        water_raw.set_parameter("textureSize",sfml.Vector2(w,h));

        water_final=self.load_shader("water_final.glsl",'water_final');
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
