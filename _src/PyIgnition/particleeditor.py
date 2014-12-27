### EXESOFT OBSIDIAN ###
# Copyright David Barker 2010
# 
# Particle editor window

import wx, pygame, PyIgnition, interpolate, keyframes, sys, timelinectrl, pygamedisplay
import wx.lib.imagebrowser as imagebrowser


class ParticleEditor(wx.Frame):
    def __init__(self, parent, numframes, keyframes, drawtype, imagepath = None):
        wx.Frame.__init__(self, parent, -1, "ExeSoft Obsidian particle editor", style = wx.DEFAULT_FRAME_STYLE, size = (640, 520))
        self.SetMinSize((650, 520))
        self.numframes = numframes
        self.keyframes = keyframes
        self.drawtype = drawtype
        self.imagepath = imagepath
        self.image = None

        self.panel = wx.Panel(self, -1)
        self.panel.SetBackgroundColour((50, 50, 50))
        self.panel.SetForegroundColour('white')
        # The particle display
        self.display = pygamedisplay.ObsidianParticlePreviewDisplay(self.panel, -1, numframes, keyframes, drawtype)

        # The keyframe timeline
        keyedframes = self.GetKeyedFrames()
        self.timeline = timelinectrl.Timeline(self.panel, -1, self.numframes, keyedframes)
        self.curframe = self.timeline.curframe

        # The drawtype selector
        self.drawtypelabel = wx.StaticText(self.panel, -1, "Drawtype:")
        self.drawtypedropdown = wx.Choice(self.panel, -1, choices = ["Point", "Circle", "Line", "Scaling line", "Bubble", "Image"])
        self.drawtypedropdown.SetSelection(self.drawtype - PyIgnition.DRAWTYPE_POINT)

        # The colour selector
        self.colourlabel = wx.StaticText(self.panel, -1, "Colour:")
        self.colourbutton = wx.Button(self.panel, -1, "", size = (0, 70))

        ## The variable panels
        self.varpanels = []

        # The 'radius' panel
        self.radiuspanel = wx.Panel(self.panel, -1, style = wx.NO_BORDER)
        self.radiuspanel.SetForegroundColour(self.panel.GetForegroundColour())
        self.radiuslabel = wx.StaticText(self.radiuspanel, -1, "Radius:")
        self.radiusbox = wx.SpinCtrl(self.radiuspanel, -1, style = wx.SP_ARROW_KEYS, min = 1, max = 500, initial = 5)
        self.radiuspanelsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.radiuspanelsizer.Add(self.radiuslabel, 2, flag = wx.RIGHT, border = 5)
        self.radiuspanelsizer.Add(self.radiusbox, 3, flag = wx.ALIGN_RIGHT | wx.LEFT, border = 5)
        self.radiuspanel.SetSizer(self.radiuspanelsizer)
        self.varpanels.append(self.radiuspanel)

        # The 'length' panel
        self.lengthpanel = wx.Panel(self.panel, -1, style = wx.NO_BORDER)
        self.lengthpanel.SetForegroundColour(self.panel.GetForegroundColour())
        self.lengthlabel = wx.StaticText(self.lengthpanel, -1, "Length:")
        self.lengthbox = wx.SpinCtrl(self.lengthpanel, -1, style = wx.SP_ARROW_KEYS, min = 1, max = 500, initial = 5)
        self.lengthpanelsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.lengthpanelsizer.Add(self.lengthlabel, 2, flag = wx.RIGHT, border = 5)
        self.lengthpanelsizer.Add(self.lengthbox, 3, flag = wx.ALIGN_RIGHT | wx.LEFT, border = 5)
        self.lengthpanel.SetSizer(self.lengthpanelsizer)
        self.varpanels.append(self.lengthpanel)

        # The 'image' panel
        self.imagepanel = wx.Panel(self.panel, -1, style = wx.NO_BORDER)
        self.imagepanel.SetForegroundColour(self.panel.GetForegroundColour())
        self.imagelabel = wx.StaticText(self.imagepanel, -1, "Image:")
        self.imagebox = wx.Button(self.imagepanel, -1, "No image loaded", size = (175, 100))
        self.imagepanelsizer = wx.BoxSizer(wx.VERTICAL)
        self.imagepanelsizer.Add(self.imagelabel, 0, flag = wx.BOTTOM, border = 5)
        self.imagepanelsizer.Add(self.imagebox, 0, flag = wx.CENTRE | wx.TOP, border = 5)
        self.imagepanel.SetSizer(self.imagepanelsizer)
        self.varpanels.append(self.imagepanel)
        self.UpdateImageBox()

        ## End variable panels

        # The 'done' button
        self.donebutton = wx.Button(self.panel, -1, "Done")

        # Set up the sizers
        # Layout:
        #|---------------------------------------------|
        #|self.mainsizer (vertical)                    |
        #||-------------------------------------------||
        #||self.topsizer (horizontal)                 ||
        #|||-------------------| |-------------------|||
        #|||self.topleftsizer  | |self.toprightsizer |||
        #|||(vertical)         | |(vertical)         |||
        #|||                   | |(several           |||
        #|||                   | |subsizers go       |||
        #|||                   | |   here)           |||
        #|||-------------------| |-------------------|||
        #||-------------------------------------------||
        #|                                             |
        #|(unsized space)                              |
        #|                                             |
        #|---------------------------------------------|

        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.topsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.topleftsizer = wx.BoxSizer(wx.VERTICAL)
        self.toprightsizer = wx.BoxSizer(wx.VERTICAL)
        self.mainsizer.Add(self.topsizer, 1, flag = wx.EXPAND)
        self.mainsizer.Add(self.timeline, 0, flag = wx.EXPAND)
        self.topsizer.Add(self.topleftsizer, 2, flag = wx.EXPAND)
        self.topsizer.Add(self.toprightsizer, 1, flag = wx.EXPAND)

        self.topleftsizer.Add(self.display, 1, flag = wx.EXPAND)
        self.topleftsizer.Add((0, 50), 0, flag = wx.EXPAND)
        
        self.drawtypesizer = wx.BoxSizer(wx.HORIZONTAL)
        self.toprightsizer.Add(self.drawtypesizer, 0, flag = wx.EXPAND)        
        self.drawtypesizer.Add(self.drawtypelabel, 2, flag = wx.ALL, border = 5)
        self.drawtypesizer.Add(self.drawtypedropdown, 3, flag = wx.ALIGN_RIGHT | wx.ALL, border = 5)
        
        self.toprightsizer.Add((0, 20), 0, flag = wx.EXPAND)
        
        self.toprightsizer.Add(self.colourlabel, 0, flag = wx.ALL, border = 5)
        self.toprightsizer.Add(self.colourbutton, 0, flag = wx.EXPAND | wx.ALL, border = 5)
        
        self.toprightsizer.Add((0, 20), 0, flag = wx.EXPAND)

        self.donebuttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.donebuttonsizer.Add((0, 0), 3, flag = wx.EXPAND)
        self.donebuttonsizer.Add(self.donebutton, 2, flag = wx.EXPAND | wx.ALL, border = 5)
        self.toprightsizer.Add((0, 20), 1, flag = wx.EXPAND)
        self.toprightsizer.Add(self.donebuttonsizer, 0, flag = wx.EXPAND)
        self.toprightsizer.Add((0, 20), 0, flag = wx.EXPAND)
        
        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.mainsizer)
        self.panel.Layout()

        self.UpdateCurframeValues()
        self.ShowAppropriateVarPanel()
        
        self.Bind(wx.EVT_SLIDER, self.OnTimelineChange, self.timeline)
        self.Bind(wx.EVT_CHOICE, self.OnDrawtypeChange, self.drawtypedropdown)
        self.Bind(wx.EVT_BUTTON, self.OnChooseColour, self.colourbutton)
        self.Bind(wx.EVT_SPINCTRL, self.OnRadiusChange, self.radiusbox)
        self.Bind(wx.EVT_SPINCTRL, self.OnLengthChange, self.lengthbox)
        self.Bind(wx.EVT_BUTTON, self.OnChooseImage, self.imagebox)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
    
    def GetKeyedFrames(self):
        keyedframes = []
        for frame in self.keyframes:
            keyedframes.append(frame.frame)
        return keyedframes

    def GetCurframeValues(self):
        newvars = interpolate.InterpolateKeyframes(self.curframe, {'colour_r':0, 'colour_g':0, 'colour_b':0, 'radius':0.0, 'length':0.0}, self.keyframes)

        return newvars

    def GetCurframeColour(self):
        newvars = self.GetCurframeValues()
        r = newvars['colour_r']
        g = newvars['colour_g']
        b = newvars['colour_b']
        
        return (r, g, b)
    
    def CreateKeyframe(self, variables):
        newframe = keyframes.CreateKeyframe(self.keyframes, self.curframe, variables)
        self.display.source.particlekeyframes = self.keyframes
        self.display.source.PreCalculateParticles()
        self.timeline.keyedframes = self.GetKeyedFrames()
        self.timeline.DoPaint()
        self.UpdateCurframeValues()
        #self.PropogateNewKeyframes()
    
    #def PropogateNewKeyframes(self):
    #    event = wx.CommandEvent(wx.EVT_NULL, self.GetId())
    #    event.SetClientData(self.keyframes)
    #    self.GetEventHandler().ProcessEvent(event)

    def ShowAppropriateVarPanel(self):
        # Prevent updates during this (looks messy...)
        self.Freeze()
        
        # Remove the done button and the spacers around it (to be re-attached later)
        length = len(self.toprightsizer.GetChildren())
        self.toprightsizer.Detach(length - 1)
        self.toprightsizer.Detach(length - 2)
        self.toprightsizer.Detach(length - 3)
        
        for panel in self.varpanels:
            self.toprightsizer.Detach(panel)
            panel.Hide()
        if self.drawtype == PyIgnition.DRAWTYPE_CIRCLE or self.drawtype == PyIgnition.DRAWTYPE_BUBBLE:
            self.radiuspanel.Show()
            self.toprightsizer.Add(self.radiuspanel, 0, flag = wx.EXPAND | wx.ALL, border = 5)
        elif self.drawtype == PyIgnition.DRAWTYPE_LINE:
            self.lengthpanel.Show()
            self.toprightsizer.Add(self.lengthpanel, 0, flag = wx.EXPAND | wx.ALL, border = 5)
        elif self.drawtype == PyIgnition.DRAWTYPE_IMAGE:
            self.imagepanel.Show()
            self.toprightsizer.Add(self.imagepanel, 0, flag = wx.EXPAND | wx.ALL, border = 5)

        # Re-attach the 'done' button sizer
        self.toprightsizer.Add((0, 20), 1, flag = wx.EXPAND)
        self.toprightsizer.Add(self.donebuttonsizer, 0, flag = wx.EXPAND)
        self.toprightsizer.Add((0, 20), 0, flag = wx.EXPAND)
        
        self.toprightsizer.Layout()
        self.Thaw()

    def UpdateCurframeValues(self):
        self.colourbutton.SetBackgroundColour(self.GetCurframeColour())
        self.radiusbox.SetValue(self.GetCurframeValues()['radius'])
        self.lengthbox.SetValue(self.GetCurframeValues()['length'])

    def UpdateImageBox(self):
        buttonimgpadding = 5
        if self.imagepath:
            try:
                rawimage = wx.Image(self.imagepath, wx.BITMAP_TYPE_ANY)
            except:
                print "Could not load image: %s" % self.imagepath
                return

            # Get the maximum size for the image
            maxsize = self.imagebox.GetSizeTuple()
            maxsize = [maxsize[0] - buttonimgpadding * 2, maxsize[1] - buttonimgpadding * 2]

            # Fit width inside button
            imgwidth, imgheight = rawimage.GetSize()
            if imgwidth > maxsize[0]:
                rawimage = rawimage.Rescale(maxsize[0], imgheight * (float(maxsize[0]) / float(imgwidth)))

            # Fit height inside button
            imgwidth, imgheight = rawimage.GetSize()
            if imgheight > maxsize[1]:
                rawimage = rawimage.Rescale(imgwidth * (float(maxsize[1]) / float(imgheight)), maxsize[1])

            self.image = rawimage.ConvertToBitmap()

            self.imagebox.Destroy()
            self.imagebox = wx.BitmapButton(self.imagepanel, -1, self.image, size = (175, 100))
            self.imagepanelsizer.Add(self.imagebox, 0, flag = wx.CENTRE | wx.TOP, border = 5)
            self.imagepanelsizer.Layout()
            self.Bind(wx.EVT_BUTTON, self.OnChooseImage, self.imagebox)

    def OnTimelineChange(self, event):
        self.curframe = self.timeline.curframe
        self.UpdateCurframeValues()

    def OnDrawtypeChange(self, event):
        self.drawtype = self.drawtypedropdown.GetSelection() + PyIgnition.DRAWTYPE_POINT
        self.display.source.drawtype = self.drawtype
        self.ShowAppropriateVarPanel()

    def OnChooseColour(self, event):
        data = wx.ColourData()  # Colour data for the dialog
        
        # Modify the data to show the full dialog and use the current colour
        data.SetChooseFull(True)
        data.SetColour(self.colourbutton.GetBackgroundColour())

        # Create and show the dialog
        dialog = wx.ColourDialog(self, data)
        dialog.SetBackgroundColour(self.panel.GetBackgroundColour())
        dialog.SetTitle("Colour selector")
        if dialog.ShowModal() == wx.ID_OK:
            newcolour = dialog.GetColourData().GetColour().Get()
            self.CreateKeyframe(variables = {'colour_r':newcolour[0], 'colour_g':newcolour[1], 'colour_b':newcolour[2], 'radius':None, 'length':None, 'interpolationtype':PyIgnition.INTERPOLATIONTYPE_LINEAR})
        dialog.Destroy()
    
    def OnRadiusChange(self, event):
        newradius = self.radiusbox.GetValue()
        self.CreateKeyframe(variables = {'colour_r':None, 'colour_g':None, 'colour_b':None, 'radius':newradius, 'length':None, 'interpolationtype':PyIgnition.INTERPOLATIONTYPE_LINEAR})
    
    def OnLengthChange(self, event):
        newlength = self.lengthbox.GetValue()
        self.CreateKeyframe(variables = {'colour_r':None, 'colour_g':None, 'colour_b':None, 'radius':None, 'length':newlength, 'interpolationtype':PyIgnition.INTERPOLATIONTYPE_LINEAR})
        pass

    def OnChooseImage(self, event):
        dialog = imagebrowser.ImageDialog(self)
        dialog.SetBackgroundColour(self.panel.GetBackgroundColour())
        
        if dialog.ShowModal() == wx.ID_OK:
            self.imagepath = dialog.GetFile()
        
        dialog.Destroy()
        self.UpdateImageBox()
        
        self.display.source.imagepath = self.imagepath
        self.display.source.image = pygame.image.load(self.imagepath)

    def OnClose(self, event):
        self.timeline.Kill(event)
        self.display.Kill(event)
        self.Destroy()


class Frame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Generic parent frame!", size = (800, 600))
        
        self.effect = PyIgnition.ParticleEffect(None)
        self.effect.LoadFromFile("Fire.ppe")
        self.source = self.effect.sources[0]
        
    def ShowParticleEditor(self):
        self.editor = ParticleEditor(self, self.source.particlelife, self.source.particlekeyframes, self.source.drawtype)
        self.editor.Show()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnWinDestroy, self.editor)
    
    def OnWinDestroy(self, event):
        win = event.GetWindow()
        try:
            print win.keyframes  # Only works for the actual frame, not its subitems. Will need to deal with this more cleanly
        except:
            pass


if __name__ == "__main__":    
    app = wx.App()
    mainframe = Frame()
    app.SetTopWindow(mainframe)
    mainframe.Show()
    mainframe.ShowParticleEditor()
    app.MainLoop()
