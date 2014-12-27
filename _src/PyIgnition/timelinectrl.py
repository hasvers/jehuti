### EXESOFT OBSIDIAN ###
# Copyright David Barker 2010
#
# Timeline control

import wx


class Timeline(wx.Panel):
    def __init__(self, parent, id, numframes = 300, keyedframes = []):
        wx.Panel.__init__(self, parent, id, style = wx.NO_BORDER)
        self.parent = parent
        self.SetSize((200, 80))
        self.SetBackgroundColour(self.parent.GetBackgroundColour())
        self.SetForegroundColour(self.parent.GetForegroundColour())

        # Number of frames and current frame
        self.max = numframes
        self.curframe = 0

        # Position, size and padding
        self.drawpos = (0, 0)
        self.size = (0, 0)
        self.sidepadding = 5
        
        self.mousetolerance = 5  # Distance away from the slider the mouse can be to click on it
        self.dragging = False

        # Load images - current frame pointer, keyframe location pointer        
        self.pointerimg = wx.Image("framepointer.png", wx.BITMAP_TYPE_PNG)
        self.pointerbmp = wx.BitmapFromImage(self.pointerimg)
        self.keypointerimg = wx.Image("keyframepointer.png", wx.BITMAP_TYPE_PNG)
        self.keypointerbmp = wx.BitmapFromImage(self.keypointerimg)
        
        self.keyedframes = keyedframes  # The frames which hold keyframes

        # Bind events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self.Bind(wx.EVT_LEFT_UP, self.OnRelease)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_CLOSE, self.Kill)

    def SetMax(self, newmax):
        self.max = newmax

    def SetCurframe(self, newcurframe):
        self.curframe = newcurframe

    def OnClick(self, event):
        p = event.GetPosition()

        # Check to see if the user has clicked inside a keyframe location pointer
        foundFrameTarget = False
        for frame in self.keyedframes:  # For each keyframe...
            # Calculate its pointer's draw position...
            drawpos = (self.drawpos[0] + int((float(frame) / float(self.max)) * float(self.size[0])), self.drawpos[1] - (self.keypointerbmp.GetHeight()))
            # And check to see if the mouse is inside the box defined by its position and size
            if p[1] > (drawpos[1]) and \
               p[1] < (drawpos[1]+ self.keypointerimg.GetHeight()) and \
               p[0] > (drawpos[0]) and \
               p[0] < (drawpos[0] + self.keypointerbmp.GetWidth()):
                # Set the current frame and indicate that a keyframe indicator has been clicked
                self.curframe = frame
                foundFrameTarget = True
                
        if foundFrameTarget:        
            self.SendSliderEvent()  # Send an event indicating that the slider position has changed

        # If the click wasn't on a keyframe pointer but was within the bounds of the slider itself
        if (not foundFrameTarget) and \
           p[1] > (self.drawpos[1] - self.mousetolerance) and \
           p[1] < (self.drawpos[1] + self.size[1] + self.pointerbmp.GetHeight()) and \
           p[0] > (self.drawpos[0] - self.mousetolerance) and \
           p[0] < (self.drawpos[0] + self.size[0] + self.mousetolerance):
            # Start dragging the slider
            self.dragging = True
            self.CaptureMouse()
            self.OnMouseMotion(event)

        self.DoPaint()
        event.Skip()

    def OnRelease(self, event):
        if self.HasCapture():  # If dragging, stop dragging
            self.ReleaseMouse()
            self.dragging = False

        event.Skip()

    def OnMouseMotion(self, event):
        if self.dragging:
            # Get its x-position relative to the left-hand side of the slider
            posx = event.GetPosition()[0] - self.drawpos[0]
            # Clip the slider position to its upper and lower bounds
            if posx >= self.size[0]:
                self.curframe = self.max
            elif posx <= 0:
                self.curframe = 0
            # If all is well on that front, set the current frame
            # (curframe / maxframes = posx / sizex)
            else:
                self.curframe = int(float(posx) / float(self.size[0]) * float(self.max))
            self.SendSliderEvent()  # Send a 'slider has changed' event

        self.DoPaint()
        event.Skip()

    def SendSliderEvent(self):
        # Create a wx.EVT_SLIDER event, give the current frame as its value and send it to be processed
        event = wx.CommandEvent(wx.EVT_SLIDER.typeId, self.GetId())
        event.SetInt(self.curframe)
        self.GetEventHandler().ProcessEvent(event)

    def OnResize(self, event):
        self.DoPaint()
        event.Skip()

    def OnPaint(self, event):
        self.DoPaint()
        event.Skip()

    def DoPaint(self):
        windc = wx.ClientDC(self)
        dc = wx.BufferedDC(windc)
        w, h = self.GetSize()

        # Background fill
        dc.SetBrush(windc.GetBackground())
        dc.DrawRectangle(0, 0, w, h)

        # Slider bar pos/size calculations
        self.drawpos = (self.sidepadding, self.keypointerbmp.GetHeight() + self.sidepadding)
        self.size = (w - (self.sidepadding * 2), 4)

        # Slider bar
        dc.SetPen(wx.Pen('#000000'))
        dc.SetBrush(wx.Brush('#FFFFFF'))
        dc.DrawRectangle(self.drawpos[0], self.drawpos[1], self.size[0], self.size[1])

        # Curframe pointer
        pointerpos = ((self.drawpos[0] + int((float(self.size[0]) * (float(self.curframe) / float(self.max))))) - (self.pointerbmp.GetWidth() / 2), self.drawpos[1])
        dc.DrawBitmap(self.pointerbmp, pointerpos[0], pointerpos[1])
        
        # Keyframe location pointers
        for frame in self.keyedframes:
            drawpos = (self.drawpos[0] + int((float(frame) / float(self.max)) * float(self.size[0])), self.drawpos[1] - (self.keypointerbmp.GetHeight()))
            dc.DrawBitmap(self.keypointerbmp, drawpos[0], drawpos[1])

        # Current frame text
        dc.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        dc.SetTextForeground(self.GetForegroundColour())
        string = "Current frame: %i" % self.curframe
        stringwidth, stringheight = dc.GetTextExtent(string)
        # Put it in the bottom-right corner, 'self.sidepadding' pixels from the edges
        dc.DrawText(string, w - (self.sidepadding + stringwidth), h - (self.sidepadding + stringheight))

    def Kill(self, event):
        self.Destroy()


class TestFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1)
        
        self.panel = wx.Panel(self, -1)
        self.timeline = Timeline(self.panel, -1, numframes = 100, keyedframes = [0, 50, 75, 88, 94, 97, 98, 99, 100])

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.timeline, 0, flag = wx.EXPAND)

        self.panel.SetSizer(self.sizer)
        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.Exit)
        self.Bind(wx.EVT_SLIDER, self.Slider)

    def Exit(self, event):
        self.timeline.Destroy()
        self.Destroy()

    def Slider(self, event):
        pass#print "Frame = %i" % event.GetInt())


if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = TestFrame(None)
    frame.SetTitle("ExeSoft Obsidian - timeline widget test")
    frame.Show()
    app.SetTopWindow(frame)
    app.MainLoop()
