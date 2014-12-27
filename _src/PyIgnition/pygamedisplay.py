### EXESOFT OBSIDIAN ###
# Copyright David Barker 2010
#
# A series of Pygame display classes for wxPython and PyIgnition, designed for use in Obsidian

import wx, sys, os, math, pygame, PyIgnition


SOURCE_DRAWSIZE = 100
GRAVITY_DRAWSIZE = 100
DELETEBOX_DRAWSIZE = 10
DELETEBOX_PADDING = 5

SOURCE_CENTRE_COLOUR = (100, 150, 100)
SOURCE_DIRECTION_COLOUR = (150, 150, 150)
SOURCE_DIRECTIONBOUNDS_COLOUR = (100, 100, 100)


class PygameDisplay(wx.Window):
    def __init__(self, parent, ID):
        wx.Window.__init__(self, parent, ID)
        self.parent = parent
        self.hwnd = self.GetHandle()
       
        self.size = self.GetSizeTuple()
        self.size_dirty = True
       
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_TIMER, self.Update, self.timer)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CLOSE, self.Kill)
        
        self.fps = 30.0
        self.timespacing = 1000.0 / self.fps
        self.timer.Start(self.timespacing, False)

    def Update(self, event):
        pass

    def Redraw(self):
        if self.size_dirty:
            self.screen = pygame.Surface(self.size, 0, 32)
            self.size_dirty = False

        self.screen.fill((0, 0, 0))
        self.DrawPygame(self.screen)

        s = pygame.image.tostring(self.screen, 'RGB')  # Convert the surface to an RGB string
        img = wx.ImageFromData(self.size[0], self.size[1], s)  # Load this string into a wx image
        bmp = wx.BitmapFromImage(img)  # Get the image in bitmap form
        dc = wx.ClientDC(self)  # Device context for drawing the bitmap
        dc.DrawBitmap(bmp, 0, 0, False)  # Blit the bitmap image to the display
        del dc

    def DrawPygame(self, display):
        pass
 
    def OnPaint(self, event):
        self.Redraw()
        event.Skip()  # Make sure the parent frame gets told to redraw as well
 
    def OnSize(self, event):
        self.size = self.GetSizeTuple()
        self.size_dirty = True
 
    def Kill(self, event):
        # Make sure Pygame can't be asked to redraw /before/ quitting by unbinding all methods which
        # call the Redraw() method
        # (Otherwise wx seems to call Draw between quitting Pygame and destroying the frame)
        # This may or may not be necessary now that Pygame is just drawing to surfaces
        self.Unbind(event = wx.EVT_PAINT, handler = self.OnPaint)
        self.Unbind(event = wx.EVT_TIMER, handler = self.Update, source = self.timer)
        self.Destroy()


class PyIgnitionDisplay(PygameDisplay):
    def __init__(self, parent, ID):
        PygameDisplay.__init__(self, parent, ID)

        self.InitEffect()

    def InitEffect(self):
        self.effect = PyIgnition.ParticleEffect(display = None, pos = (0, 0))

    def DrawPygame(self, display):
        self.effect.display = display
        self.effect.Redraw()

    def Update(self, event):
        self.effect.Update()
        self.Redraw()


class ObsidianPreviewDisplay(PyIgnitionDisplay):
    def __init__(self, parent, ID, effect):
        PyIgnitionDisplay.__init__(self, parent, ID)
        
        self.effect = effect
        
        
class ObsidianMainDisplay(PyIgnitionDisplay):
    def __init__(self, parent, ID):
        PyIgnitionDisplay.__init__(self, parent, ID)
        
        self.curframe = 0
    
    def Update(self, event):
        self.effect.PropogateCurframe(self.curframe)
        PyIgnitionDisplay.Update(self, event)
    
    def DrawPygame(self, display):
        for source in self.effect.sources:
            self.DrawSource(source, display)
            
            if source.selected:
                self.DrawSelectBox(display, source.pos, (SOURCE_DRAWSIZE, SOURCE_DRAWSIZE))
        
        for gravity in self.effect.gravities:
            if gravity.type == "point":
                self.DrawPointGravity(gravity, display)
            elif gravity.type == "directed":
                self.DrawDirectedGravity(gravity, display)
            elif gravity.type == "vortex":
                self.DrawVortexGravity(gravity, display)
            
            if gravity.type == "point" or gravity.type == "vortex":
                if gravity.selected:
                    self.DrawSelectBox(display, gravity.pos, (GRAVITY_DRAWSIZE, GRAVITY_DRAWSIZE))
        
        for obstacle in self.effect.obstacles:
            obstacle.Draw(display)
            
            if obstacle.selected:
                self.DrawSelectBox(display, obstacle.pos, (obstacle.maxdist * 2.0, obstacle.maxdist * 2.0))
    
    def DrawSelectBox(self, display, pos, size):
        pygame.draw.rect(display, (255, 255, 255), pygame.Rect((pos[0] - (size[0] / 2), pos[1] - (size[1] / 2)), size), 1)
        self.DrawDeleteBox(display, ((pos[0] + (size[0] / 2)) - (DELETEBOX_DRAWSIZE + DELETEBOX_PADDING), (pos[1] - (size[1] / 2)) + DELETEBOX_PADDING), (DELETEBOX_DRAWSIZE, DELETEBOX_DRAWSIZE))
    
    def DrawDeleteBox(self, display, pos, size):
        pygame.draw.rect(display, (255, 0, 0), pygame.Rect(pos, size))
        pygame.draw.line(display, (255, 255, 255), (pos[0] + 2, pos[1] + 2), ((pos[0] + size[0]) - 4, (pos[1] + size[1]) - 4), 2)
        pygame.draw.line(display, (255, 255, 255), (pos[0] + 2, (pos[1] + size[1]) - 4), ((pos[0] + size[0]) - 4, pos[1] + 2), 2)
    
    def DrawSource(self, source, display):
        radius = float(SOURCE_DRAWSIZE) / 2.0
        
        # Calculate the vectors for lines pointing in the directions of the particle direction and the upper and lower random range bounds thereof
        # (Length is equal to radius, radius being half the width of the source drawsize such that this radius fills the box)
        directionlinex = radius * math.sin(source.initdirection)
        directionliney = radius * math.cos(source.initdirection)
        directionlowerboundlinex = radius * math.sin(source.initdirection - source.initdirectionrandrange)
        directionlowerboundliney = radius * math.cos(source.initdirection - source.initdirectionrandrange)
        directionupperboundlinex = radius * math.sin(source.initdirection + source.initdirectionrandrange)
        directionupperboundliney = radius * math.cos(source.initdirection + source.initdirectionrandrange)
        
        # Draw the lines in the appropriate colours (order of drawing is the same as order of calculation)
        pygame.draw.aaline(display, SOURCE_DIRECTION_COLOUR, source.pos, (source.pos[0] + directionlinex, source.pos[1] + directionliney))
        pygame.draw.aaline(display, SOURCE_DIRECTIONBOUNDS_COLOUR, source.pos, (source.pos[0] + directionlowerboundlinex, source.pos[1] + directionlowerboundliney))
        pygame.draw.aaline(display, SOURCE_DIRECTIONBOUNDS_COLOUR, source.pos, (source.pos[0] + directionupperboundlinex, source.pos[1] + directionupperboundliney))
        
        # Draw the position of the source as a point
        pygame.draw.circle(display, SOURCE_CENTRE_COLOUR, source.pos, 5)
    
    def DrawPointGravity(self, gravity, display):
        pass
    
    def DrawDirectedGravity(self, gravity, display):
        pass
    
    def DrawVortexGravity(self, gravity, display):
        pass
    
    def AddSource(self, source):
        self.effect.sources.append(source)
    
    def AddGravity(self, gravity):
        self.effect.gravities.append(gravity)
    
    def AddObstacle(self, obstacle):
        self.effect.obstacles.append(obstacle)


class ObsidianParticlePreviewDisplay(PyIgnitionDisplay):
    def __init__(self, parent, ID, numframes, keyframes, drawtype = PyIgnition.DRAWTYPE_POINT):
        PyIgnitionDisplay.__init__(self, parent, ID)
        
        self.source = self.effect.CreateSource(pos = (0, self.size[1]), initspeed = 5.0,
            initdirection = 1.0, initspeedrandrange = 0.2, initdirectionrandrange = 0.2,
            particlesperframe = 10, particlelife = numframes, drawtype = drawtype)
        self.source.particlekeyframes = keyframes
        self.source.PreCalculateParticles()
        
        self.gravity = self.effect.CreateDirectedGravity(strength = 0.05, direction = [0, 1])
    
    def CalculateSpeedAndDirection(self):
        tempsizex = self.size[0]
        tempsizey = self.size[1]
        
        try:
            angle = math.atan(float(tempsizex) / (2.0 * float(tempsizey)))
        except ZeroDivisionError:
            angle = 0.5
        
        self.source.SetInitDirection(angle)
        
        try:
            self.source.SetInitSpeed(math.sqrt((float(tempsizey) * self.gravity.strength) / math.pow(math.cos(angle), 2.0)))
        except ZeroDivisionError:
            self.source.SetInitSpeed(5.0)
    
    def OnSize(self, event):
        PyIgnitionDisplay.OnSize(self, event)
        
        self.source.SetPos((0, self.size[1]))
        self.CalculateSpeedAndDirection()


class Frame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, size = (600, 600))
       
        self.display = PyIgnitionDisplay(self, -1)
        
        self.Bind(wx.EVT_CLOSE, self.Kill)
       
        self.SetTitle("PyIgnition embedded in wxPython")
 
    def Kill(self, event):
        self.display.Kill(event)
        self.Destroy()
 
class App(wx.App):
    def OnInit(self):
        self.frame = Frame(parent = None)
        self.frame.Show()
        self.SetTopWindow(self.frame)
       
        return True
 
if __name__ == "__main__":
    app = App()
    app.MainLoop()
