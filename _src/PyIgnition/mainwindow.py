### EXESOFT OBSIDIAN ###
# Copyright David Barker 2010
# 
# Main window

import wx, pygame, webbrowser, PyIgnition, interpolate, keyframes, sys, timelinectrl, pygamedisplay


class MainWindow(wx.Frame):
	def __init__(self, parent):
		wx.Frame.__init__(self, parent, -1, "ExeSoft Obsidian", style = wx.DEFAULT_FRAME_STYLE, size = (800, 600))
		
		self.curframe = 0
		
		self.savepath = None
		self.unsavedchanges = True
		
		self.panel = wx.Panel(self, -1)
		self.panel.SetBackgroundColour((50, 50, 50))
		self.panel.SetForegroundColour('white')
		
		self.InitMenuBar()
		self.InitStatusBar()
		
		self.BindEvents()
	
	def InitMenuBar(self):
		## Create the menus
		self.menubar = wx.MenuBar()
		
		# File
		self.filemenu = wx.Menu()
		self.filenew = self.filemenu.Append(-1, "New\tCtrl-N", "Create a new effect")
		self.fileopen = self.filemenu.Append(-1, "Open...\tCtrl-O", "Open an effect for editing")
		self.filesave = self.filemenu.Append(-1, "Save\tCtrl-S", "Save the current effect")
		self.filesaveas = self.filemenu.Append(-1, "Save as...\tCtrl-Shift-S", "Save the current effect to a new file")
		self.filemenu.AppendSeparator()
		self.filepreview = self.filemenu.Append(-1, "Preview\tCtrl-P", "Preview the current effect")
		self.fileproperties = self.filemenu.Append(-1, "Properties", "Edit properties for the current effect")
		self.filemenu.AppendSeparator()
		self.filepreferences = self.filemenu.Append(-1, "Preferences", "Configure how Obsidian works")
		self.fileexit = self.filemenu.Append(-1, "Exit\tCtrl-Q", "Exit Obsidian")
		self.menubar.Append(self.filemenu, "&File")
		
		# Add
		self.addmenu = wx.Menu()
		self.addsource = self.addmenu.Append(-1, "Source", "Add a new particle source")
		self.addgravitymenu = wx.Menu()
		self.addgravitypoint = self.addgravitymenu.Append(-1, "Point", "Add a new point gravity")
		self.addgravitydirected = self.addgravitymenu.Append(-1, "Directed", "Add a new directed gravity")
		self.addgravityvortex = self.addgravitymenu.Append(-1, "Vortex", "Add a new vortex gravity")
		self.addmenu.AppendMenu(-1, "Gravity", self.addgravitymenu)
		self.addobstaclemenu = wx.Menu()
		self.addobstaclecircle = self.addobstaclemenu.Append(-1, "Circle", "Add a new circular obstacle")
		self.addobstaclerectangle = self.addobstaclemenu.Append(-1, "Rectangle", "Add a new rectangular obstacle")
		self.addobstacleboundaryline = self.addobstaclemenu.Append(-1, "Boundary line", "Add a new boundary line obstacle")
		self.addmenu.AppendMenu(-1, "Obstacle", self.addobstaclemenu)
		self.menubar.Append(self.addmenu, "&Add")
		
		# Help
		self.helpmenu = wx.Menu()
		self.helpinstructions = self.helpmenu.Append(-1, "Instruction manual", "View the Obsidian instruction manual")
		self.helpmenu.AppendSeparator()
		self.helpobsidianweb = self.helpmenu.Append(-1, "Obsidian website", "Go to the Obsidian website")
		self.helppyignitionweb = self.helpmenu.Append(-1, "PyIgnition website", "Go to the PyIgnition website")
		self.helpexesoftweb = self.helpmenu.Append(-1, "ExeSoft website", "Go to the ExeSoft website")
		self.helpmenu.AppendSeparator()
		self.helpabout = self.helpmenu.Append(-1, "About...", "View information about this version of Obsidian")
		self.menubar.Append(self.helpmenu, "&Help")
		
		self.SetMenuBar(self.menubar)
		
		## Register event handlers
		# File
		self.Bind(wx.EVT_MENU, self.FileNew, self.filenew)
		self.Bind(wx.EVT_MENU, self.FileOpen, self.fileopen)
		self.Bind(wx.EVT_MENU, self.FileSave, self.filesave)
		self.Bind(wx.EVT_MENU, self.FileSaveAs, self.filesaveas)
		self.Bind(wx.EVT_MENU, self.FilePreview, self.filepreview)
		self.Bind(wx.EVT_MENU, self.FileProperties, self.fileproperties)
		self.Bind(wx.EVT_MENU, self.FilePreferences, self.filepreferences)
		self.Bind(wx.EVT_MENU, self.FileExit, self.fileexit)
		
		# Add
		self.Bind(wx.EVT_MENU, self.AddSource, self.addsource)
		self.Bind(wx.EVT_MENU, self.AddPointGravity, self.addgravitypoint)
		self.Bind(wx.EVT_MENU, self.AddDirectedGravity, self.addgravitydirected)
		self.Bind(wx.EVT_MENU, self.AddVortexGravity, self.addgravityvortex)
		self.Bind(wx.EVT_MENU, self.AddCircle, self.addobstaclecircle)
		self.Bind(wx.EVT_MENU, self.AddRectangle, self.addobstaclerectangle)
		self.Bind(wx.EVT_MENU, self.AddBoundaryLine, self.addobstacleboundaryline)
		
		# Help
		self.Bind(wx.EVT_MENU, self.HelpInstructions, self.helpinstructions)
		self.Bind(wx.EVT_MENU, self.HelpObsidianWeb, self.helpobsidianweb)
		self.Bind(wx.EVT_MENU, self.HelpPyIgnitionWeb, self.helppyignitionweb)
		self.Bind(wx.EVT_MENU, self.HelpExeSoftWeb, self.helpexesoftweb)
		self.Bind(wx.EVT_MENU, self.HelpAbout, self.helpabout)
	
	def InitStatusBar(self):
		self.statusbar = self.CreateStatusBar()
		self.statusbar.SetFieldsCount(3)
		self.statusbar.SetStatusWidths([-3, -2, 100])
		
		## TEST CODE
		self.statusbar.SetStatusText("Currently selected: vortex gravity", 1)
		self.statusbar.SetStatusText("Frame 37", 2)
		## END TEST CODE
	
	def BindEvents(self):
		self.Bind(wx.EVT_CLOSE, self.OnExit)
	
	def FileNew(self, event):
		if self.unsavedchanges:
			dialog = wx.MessageDialog(self, "Are you sure you want to open a new file? You have unsaved changes.", "Are you sure?", style = wx.YES | wx.NO | wx.ICON_EXCLAMATION)
			if dialog.ShowModal() == wx.ID_NO:
				return
		print "New! (Not implemented)"
		self.unsavedchanges = True
	
	def FileOpen(self, event):
		if self.unsavedchanges:
			dialog = wx.MessageDialog(self, "Are you sure you want to open another file? You have unsaved changes.", "Are you sure?", style = wx.YES | wx.NO | wx.ICON_EXCLAMATION)
			if dialog.ShowModal() == wx.ID_NO:
				return
		
		print "Open! (Not implemented)"
		self.unsavedchanges = False
	
	def FileSave(self, event):
		print "Save! (Not implemented)"
		self.unsavedchanges = False
	
	def FileSaveAs(self, event):
		print "Save as! (Not implemented)"
		self.unsavedchanges = False
	
	def FilePreview(self, event):
		print "Preview! (Not implemented)"
	
	def FileProperties(self, event):
		print "Properties! (Not implemented)"
	
	def FilePreferences(self, event):
		print "Preferences! (Not implemented)"
	
	def FileExit(self, event):
		self.Close()
	
	def AddSource(self, event):
		print "Add source! (Not implemented)"
	
	def AddPointGravity(self, event):
		print "Add point gravity! (Not implemented)"
	
	def AddDirectedGravity(self, event):
		print "Add directed gravity! (Not implemented)"
	
	def AddVortexGravity(self, event):
		print "Add vortex gravity! (Not implemented)"
	
	def AddCircle(self, event):
		print "Add circle! (Not implemented)"
	
	def AddRectangle(self, event):
		print "Add rectangle! (Not implemented)"
	
	def AddBoundaryLine(self, event):
		print "Add boundary line! (Not implemented)"
	
	def HelpInstructions(self, event):
		print "Instructions! (Not implemented)"
	
	def HelpObsidianWeb(self, event):
		webbrowser.open("http://launchpad.net/obsidian")
	
	def HelpPyIgnitionWeb(self, event):
		webbrowser.open("http://launchpad.net/pyignition")
	
	def HelpExeSoftWeb(self, event):
		webbrowser.open("http://exesoft.co.nr")
	
	def HelpAbout(self, event):
		info = wx.AboutDialogInfo()
		info.Name = "ExeSoft Obsidian"
		info.Version = "Pre-alpha"
		info.Copyright = "(C) 2010 David Barker"
		info.Description = "\
This version of Obsidian is incomplete, and many features\n\
have not yet been implemented. However, you are free to\n\
test it and mess around with the (largely skeletal at\n\
present) code as you wish. If you find any bugs, please\n\
report them at the website listed below:"
		info.WebSite = ("http://launchpad.net/obsidian", "Obsidian website")
		info.Developers = ["Designed and programmed by David Barker"]
		info.License = "License has not yet been decided upon."
		
		wx.AboutBox(info)
	
	def OnExit(self, event):
		if self.unsavedchanges:
			dialog = wx.MessageDialog(self, "Are you sure you want to quit? You have unsaved changes.", "Are you sure?", style = wx.YES | wx.NO | wx.ICON_EXCLAMATION)
			if dialog.ShowModal() == wx.ID_YES:
				self.Destroy()
			else:
				event.Veto()
		else:
			self.Destroy()


if __name__ == "__main__":
	app = wx.PySimpleApp()
	frame = MainWindow(None)
	frame.Show()
	app.MainLoop()
