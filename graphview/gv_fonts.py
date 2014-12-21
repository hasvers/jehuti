# -*- coding: utf-8 -*-
import pygame as pg

class FontMaster(object):
    class FontWrapper(object):
        def __init__(self,fname,size):
            try:
                self.font=pg.freetype.Font(fname,size)
            except:
                self.font=pg.font.Font(fname,size)

        @property
        def render(self):
            return self.font.render
        @property
        def size(self):
            try:
                return self.font.get_rect
            except:
                return self.font.size

        def get_linesize(self):
            try:
                return self.font.get_sized_height()
            except:
                return self.font.get_linesize()
        @property
        def strong(self):
            try:
                return self.font.strong
            except:
                return self.font.set_bold
        @property
        def oblique(self):
            try:
                return self.font.oblique
            except:
                return self.font.set_italic
        @property
        def underline(self):
            try:
                return self.font.underline
            except:
                return self.font.set_underline

        def style(self):
            try:
                return self.font.style()
            except:
                f=self.font
                return (f.get_italic(),f.get_bold(),f.get_underline())

    def __init__(self,database,resource_path):
        self.fonts={}
        self.database=database
        self.resource_path=resource_path
        self["base"]=(database['font'], database['font_default_size'])
        self["emote"]=( database['font'], database['font_emote_size'])


    def __setitem__(self,name,tup):
        self.fonts[name]=self.FontWrapper(
            self.resource_path( self.database['font_path']+tup[0]), tup[1])

    def __getitem__(self,name):
        try:
            return self.fonts[name]
        except:
            raise Exception('Font "{}" not found.'.format(name))