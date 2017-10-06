# -*- coding: utf-8 -*-

from gv_resources import *
import cairo
import rsvg

class VectorLibrary(ResourceLibrary):
    def draw(self,name,surf,pos=(0,0),*args):
        if name in self.buffer:
            surf.blit(self.buffer[name],pos,*args)
            return True
        cr = cairo_create(resource_path(database['img_path']+name) )
        vec=self.load(name)
        size=surf.get_rect().size
        pixels = pgsurfarray.pixels2d(surf)

        # Set up a Cairo surface using the same memory block and the same pixel
        # format (Cairo's RGB24 format means that the pixels are stored as
        # 0x00rrggbb; i.e. only 24 bits are used and the upper 16 are 0).
        cairo_surface = cairo.ImageSurface.create_for_data(
            pixels.data, cairo.FORMAT_RGB24, size[0], size[1])

        # Draw a smaller black circle to the screen using Cairo.
        context = cairo.Context(cairo_surface)
        context.set_source_rgb(0, 0, 0)
        buf=svg.render_cairo(context)
        context.arc(size[0]/2, size[1]/2, min(size)/2*0.5, 0, 2*math.pi)
        context.fill()