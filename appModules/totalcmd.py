#appModules/totalcmd.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2012 NVDA Contributors
#Copyright (C) 2020 Eugene Poplavsky <jawhien@gmail.com>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import appModuleHandler
import addonHandler
import NVDAObjects
from NVDAObjects.IAccessible import IAccessible
import speech
import controlTypes
import winsound
import ui
import winUser
from . import tcApi
import config

addonHandler.initTranslation()
tcApi = tcApi.tcApi()
manifest = addonHandler.getCodeAddon().manifest
oldActivePannel=0
activePannel=1

class AppModule(appModuleHandler.AppModule):
	scriptCategory = manifest['summary']

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if obj.windowClassName in ("TMyListBox", "TMyListBox.UnicodeClass")  and obj.parent.parent.parent.windowClassName == "TTOTAL_CMD":
			clsList.insert(0, TCList)
		if obj.windowClassName in ("ComboLBox", "ComboLBox.UnicodeClass"):
			clsList.insert(0, TCCombo)
		if obj.windowClassName in ("LCLListBox", "LCLListBox.UnicodeClass")  and obj.parent.parent.parent.windowClassName == "TTOTAL_CMD":
			clsList.insert(0, TCList8x)
		if obj.windowClassName in ("LCLListBox", "LCLListBox.UnicodeClass")  and obj.parent.parent.parent.windowClassName == "TCONNECT":
			clsList.insert(0, TCListConnect)
		if obj.windowClassName in ("TMyListBox", "TMyListBox.UnicodeClass") and obj.parent.parent.parent.windowClassName == "TCONNECT":
			clsList.insert(0, TCListConnect)

class TCList(IAccessible):
	scriptCategory = manifest['summary']
	lastPanel = 0
	activePanel = 1

	def event_gainFocus(self):
		global oldActivePannel
		global activePannel
		if oldActivePannel !=self.windowControlID:
			oldActivePannel=self.windowControlID
			obj=self
			while obj and obj.parent and obj.parent.windowClassName!="TTOTAL_CMD":
				obj=obj.parent
			counter=0
			while obj and obj.previous and obj.windowClassName!="TPanel":
				obj=obj.previous
				if obj.windowClassName!="TDrivePanel":
					counter+=1
			if self.parent.parent.parent.windowClassName=="TTOTAL_CMD":
				if counter==2:
					speech.speakMessage(_("Left"))
					activePannel = 1
				else:
					speech.speakMessage(_("Right"))
					activePannel = 2
		super(TCList,self).event_gainFocus()

	def _get_positionInfo(self):
		if tcApi.isApiSupported() and self.role == controlTypes.ROLE_LISTITEM:
			index= tcApi.getCurrentElementNum()
			totalCount= tcApi.getCountElements()
			return dict(indexInGroup=index,similarItemsInGroup=totalCount) 
		else:
			return None

	def reportFocus(self):
		global activePannel
		obj = self
		if obj.parent.parent.parent.windowClassName=="TTOTAL_CMD":
			if activePannel == 1:
				self.description = _("Left pannel")
			else:
				self.description = _("Right pannel")

		if self.name:
			speakList=[]
			if controlTypes.STATE_SELECTED in self.states:
				speakList.append(controlTypes.stateLabels[controlTypes.STATE_SELECTED])
			speakList.append(self.name.split("\\")[-1])

			if config.conf['presentation']['reportObjectPositionInformation'] == True and tcApi.isApiSupported():
				positionInfo = self.positionInfo
				template = _('{current} of {all}').format(current=positionInfo['indexInGroup'], all=positionInfo['similarItemsInGroup'])
				if self.name != '..':
					speakList.append(' ' + template)

			if self.hasFocus:
				speech.speakMessage(" ".join(speakList))
		else:
			super(TCList,self).reportFocus()

	def script_nextElement(self, gesture):
		gesture.send()
		if not self.next:
			winsound.PlaySound("default",1)

	def script_previousElement(self, gesture):
		gesture.send()
		if not self.previous:
			winsound.PlaySound("default",1)

	def initOverlayClass(self):
		for gesture in self.__nextElementGestures:
			self.bindGesture(gesture, "nextElement")
		for gesture in self.__previousElementGestures:
			self.bindGesture(gesture, "previousElement")
		for gesture in self.__selectedCommandsGestures:
			self.bindGesture(gesture, "selectedCommands")

	def script_selectedElementsInfo(self, gesture):
		if tcApi.isApiSupported():
			total = tcApi.getCountElements()
			selected = tcApi.getSelectedElements()
			if selected > total:
				selected = total
			template = _("Selected {selected} of {total} items").format(selected=selected, total=total)
			ui.message(template)
		else:
			ui.message(_('Not supported in this version of total commander'))
	script_selectedElementsInfo.__doc__ = _("Reports information about the number of selected elements")

	def script_selectedCommands(self, gesture):
		gesture.send()
		if tcApi.isApiSupported():
			selected = tcApi.getSelectedElements()
			if selected > 0:
				template = _("Selected {count} items").format(count=selected)
				ui.message(template)
			elif selected == 0:
				ui.message(_("Nothing selected"))
		else:
			ui.message(_("Not supported in this version of total commander"))

	def script_reportFileSize(self, gesture):
		if tcApi.isApiSupported():
			selected = tcApi.getSelectedElements()
			if selected > 0:
				hnd = tcApi.getSizeHandle()
				obj = NVDAObjects.IAccessible.getNVDAObjectFromEvent(hnd, winUser.OBJID_CLIENT, 0)
				text = obj.displayText
				size = ''
				for s in text:
					if s.isspace() == False and s.isdigit() == False:
						break
					if s.isdigit():
						size += s
				sizeKB = int(size)
				sizeMB = int((sizeKB / 1024) * 100) / 100
				template = _("{mb} MB, {kb} KB").format(mb=sizeMB, kb=sizeKB)
				ui.message(template)
			else:
				ui.message(_("Nothing selected"))
		else:
			ui.message(_("Not supported in this version of total commander"))
	script_reportFileSize.__doc__ = _("Reports to the size off selected files and folders")

	__nextElementGestures = {
		"kb:downArrow",
		"kb:rightArrow",
		"KB:PageDown",
		"KB:END"
	}

	__previousElementGestures = {
		"kb:upArrow",
		"kb:leftArrow",
		"KB:PageUp",
		"KB:HOME"
	}

	__selectedCommandsGestures = {
		"KB:CONTROL+A",
		"KB:CONTROL+numpadMinus"
	}

	__gestures={
		"KB:CONTROL+SHIFT+E":"selectedElementsInfo",
	"KB:CONTROL+SHIFT+R":"reportFileSize"
	}

class TCCombo(IAccessible):

	def event_gainFocus(self):
		description = self.displayText
		if description:
			self.name = description[0:1] + " (" + description[2:] + ")"
		super(TCCombo,self).event_gainFocus()

class TCList8x(IAccessible):
	scriptCategory = manifest['summary']

	def event_gainFocus(self):
		global oldActivePannel
		global activePannel
		if oldActivePannel !=self.windowControlID:
			oldActivePannel=self.windowControlID
			obj=self
			while obj and obj.parent and obj.parent.windowClassName!="TTOTAL_CMD":
				obj=obj.parent
			if self.parent.parent.parent.windowClassName == "TTOTAL_CMD":
				if obj.previous and obj.next and obj.previous.windowClassName == "LCLListBox" and obj.next.windowClassName == "Window":
					speech.speakMessage(_("Left"))
					activePannel = 1
				elif obj.previous and obj.next and obj.previous.windowClassName == "Window" and obj.next.windowClassName == "LCLListBox":
					speech.speakMessage(_("Right"))
					activePannel = 2
		super(TCList8x,self).event_gainFocus()

	def _get_positionInfo(self):
		if tcApi.isApiSupported() and self.role == controlTypes.ROLE_LISTITEM:
			index= tcApi.getCurrentElementNum()
			totalCount= tcApi.getCountElements()
			return dict(indexInGroup=index,similarItemsInGroup=totalCount) 
		else:
			return None

	def reportFocus(self):
		global activePannel
		obj = self
		if obj.parent.parent.parent.windowClassName=="TTOTAL_CMD":
			if activePannel == 1:
				self.description = _("Left pannel")
			else:
				self.description = _("Right pannel")

		if self.name:
			speakList=[]
			if controlTypes.STATE_SELECTED in self.states:
				speakList.append(controlTypes.stateLabels[controlTypes.STATE_SELECTED])
			speakList.append(self.name.split("\\")[-1])
			if config.conf['presentation']['reportObjectPositionInformation'] == True and tcApi.isApiSupported():
				positionInfo = self.positionInfo
				template = _('{current} of {all}').format(current=positionInfo['indexInGroup'], all=positionInfo['similarItemsInGroup'])
				if self.name != '..':
					speakList.append(' ' + template)
			if self.hasFocus:
				speech.speakMessage(" ".join(speakList))
		else:
			super(TCList8x,self).reportFocus()

	def script_nextElement(self, gesture):
		gesture.send()
		if not self.next:
			winsound.PlaySound("default",1)

	def script_previousElement(self, gesture):
		gesture.send()
		if not self.previous:
			winsound.PlaySound("default",1)

	def initOverlayClass(self):
		for gesture in self.__nextElementGestures:
			self.bindGesture(gesture, "nextElement")
		for gesture in self.__previousElementGestures:
			self.bindGesture(gesture, "previousElement")
		for gesture in self.__selectedCommandsGestures:
			self.bindGesture(gesture, "selectedCommands")

	def script_selectedElementsInfo(self, gesture):
		if tcApi.isApiSupported():
			total = tcApi.getCountElements()
			selected = tcApi.getSelectedElements()
			if selected > total:
				selected = total
			template = _("Selected {selected} of {total} items").format(selected=selected, total=total)
			ui.message(template)
		else:
			ui.message(_('Not supported in this version of total commander'))
	script_selectedElementsInfo.__doc__ = _("Reports information about the number of selected elements")

	def script_selectedCommands(self, gesture):
		gesture.send()
		if tcApi.isApiSupported():
			selected = tcApi.getSelectedElements()
			if selected > 0:
				template = _("Selected {count} items").format(count=selected)
				ui.message(template)
			elif selected == 0:
				ui.message(_("Nothing selected"))
		else:
			ui.message(_("Not supported in this version of total commander"))

	def script_reportFileSize(self, gesture):
		if tcApi.isApiSupported():
			selected = tcApi.getSelectedElements()
			if selected > 0:
				hnd = tcApi.getSizeHandle()
				obj = NVDAObjects.IAccessible.getNVDAObjectFromEvent(hnd, winUser.OBJID_CLIENT, 0)
				text = obj.displayText
				size = ''
				for s in text:
					if s.isspace() == False and s.isdigit() == False:
						break
					if s.isdigit():
						size += s
				sizeKB = int(size)
				sizeMB = int((sizeKB / 1024) * 100) / 100
				template = _("{mb} MB, {kb} KB").format(mb=sizeMB, kb=sizeKB)
				ui.message(template)
			else:
				ui.message(_("Nothing selected"))
		else:
			ui.message(_("Not supported in this version of total commander"))
	script_reportFileSize.__doc__ = _("Reports to the size off selected files and folders")

	__nextElementGestures = {
		"kb:downArrow",
		"kb:rightArrow",
		"KB:PageDown",
		"KB:END"
	}

	__previousElementGestures = {
		"kb:upArrow",
		"kb:leftArrow",
		"KB:PageUp",
		"KB:HOME"
	}

	__selectedCommandsGestures = {
		"KB:CONTROL+A",
		"KB:CONTROL+numpadMinus"
	}

	__gestures={
		"KB:CONTROL+SHIFT+E":"selectedElementsInfo",
	"KB:CONTROL+SHIFT+R":"reportFileSize"
	}

class TCListConnect(IAccessible):

	def script_nextElement(self, gesture):
		gesture.send()
		if not self.next:
			winsound.PlaySound("default",1)

	def script_previousElement(self, gesture):
		gesture.send()
		if not self.previous:
			winsound.PlaySound("default",1)

	def initOverlayClass(self):
		for gesture in self.__nextElementGestures:
			self.bindGesture(gesture, "nextElement")
		for gesture in self.__previousElementGestures:
			self.bindGesture(gesture, "previousElement")

	__nextElementGestures = {
		"kb:downArrow",
		"kb:rightArrow",
		"KB:PageDown",
		"KB:END"
	}

	__previousElementGestures = {
		"kb:upArrow",
		"kb:leftArrow",
		"KB:PageUp",
		"KB:HOME"
	}

