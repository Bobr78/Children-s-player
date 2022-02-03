
import wx								#используем для проприсовки фрейма
import imageio 								#используем для заполнения карты событий
import io
import chardet
import os
import codecs
# https://mutagen.readthedocs.io/en/latest/user/gettingstarted.html
from mutagen.mp3 import MP3
from PIL import Image, ImageDraw, ImageFont
from glob import glob
import pygame
pygame.init()		
pygame.mixer.init() 	
import ctypes  # An included library with Python install.
#https: // qastack.ru/programming/2963263/how-can-i-create-a-simple-message-box-in-python

class Form_player(wx.Frame):

# долго думал и решил что в папке есть файл ini.txt
# в которым сохраняем список ключей - просто передавать их при инициализации долго и чревато ошибками. 
# при выборе нового скина - передаем при формировании класса название ini файла в котором прописываем параметры

# ПРАВИЛА ДЛЯ ФОРМИРОВАНИЯ КАРТЫ СОБЫТИЙ (event_map) - учитывается только цвет в канале R !!!
# 0 значение по умолчанию, НЕ ИСПОЛЬЗОВАТЬ В КАРТЕ СОБЫТИЙ!!
# значения с 1 по 255 - любые, привязка событий в управляющем классе
#______________________Инициация переменных класса

	def __init__(self, filename='ini.txt', **kwargs):
		wx.Frame.__init__(self, None, -1, "Shaped Window", style = wx.FRAME_SHAPED | wx.SIMPLE_BORDER )
		

#прикручина передача имени инициирующего файла и если нет то по умолчанию брать ini.txt
		__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) 

# конструкция os.path.join(__location__, filename) и переменная __location__ 
# позволяет читать файл из текущего катклога
# https://qastack.ru/programming/4060221/how-to-reliably-open-a-file-in-the-same-directory-as-a-python-script
# bytes и т.д. перекодирует файл чтобы небыло всяких маркеров типа BOM символа

		self.test=1

		bytes = min(32, os.path.getsize(os.path.join(__location__, filename)))
		raw = open(os.path.join(__location__, filename), 'rb').read(bytes)

		if raw.startswith(codecs.BOM_UTF8):
			encoding = 'utf-8-sig'
		else:
			result = chardet.detect(raw)
			encoding = result['encoding']

		with open(os.path.join(__location__, filename), 'r', encoding=encoding) as file:								#Читаем файл
			lines = file.read().split()	#не читаем комментарии (начинаются с символа #)
			self.dic = {}								# Создаем пустой словарь

		for line in lines:							# Проходимся по каждой строчке
				if line[0]!='#':
					key,value = line.split(':')					# Разделяем каждую строку по двоеточию
					self.dic.update({key:value})
#======================================================================================================================================
		# словарь переменных для отслеживания изменений параметров кнопок
		self.EVENT_Form_player = {}
		self.EVENT_Form_player.update({'B_Play_Pause':'Null'})
		self.EVENT_Form_player.update({'B_Stop': 0})
		self.EVENT_Form_player.update({'B_Forward': 1})
		self.EVENT_Form_player.update({'B_Back': 1})
#______________________Делаем форму окна в виде картинки
		
		self.hasShape = False
		self.delta = wx.Point(0,0)
		# загружаем полностью картинку со всеми кнопками и т.п.
		self.bmp = wx.Image(os.path.join(
			__location__, self.dic['IMAGE_PATH_BG']), wx.BITMAP_TYPE_ANY).ConvertToBitmap()	 # загружаем полностью картинку
		self.transparentColour = wx.Colour(int(self.dic['R']), int(self.dic['G']), int(self.dic['B']), alpha=wx.ALPHA_OPAQUE)
#______________________Загружаем карту событий
		# запись картинки для карты событий по каналу R - 
		# сделать инициализацию ивсех масок и карт из одного файла используя - wx.Image.__init__ (self, size, data)
		# !!!!
		self.mask_event_path = os.path.join(__location__, self.dic['IMAGE_PATH_M'])
		self.event_map = imageio.imread(self.mask_event_path)
		self.bmp_form = wx.Image(self.mask_event_path, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
		self.SetClientSize(self.bmp_form.GetWidth(), self.bmp_form.GetHeight())
#______________________Инициируем Скин 
		self.DC_B=wx.MemoryDC()										#выделяем холст в памяти
		self.DC_B.SelectObject(wx.Bitmap(self.bmp.GetWidth(), self.bmp.GetHeight()))		#связываем холст с размерами
		self.DC_B.DrawBitmap(self.bmp, 0,0, False)		#переносим все обои на холст в памяти
		self.dc = wx.ClientDC(self)				# рисует картинку в окне. ВАЖНО! если перехватываем событие wx.EVT_PAINT то
												# используем wx.PaintDC(self) в других случаях wx.ClientDC(self)
												# http://python-lab.blogspot.com/2012/10/wxpython-in-action-12.html
#______________________связываем события формы с функциями
	
		self.SetWindowShape()
		self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
		self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
		self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
		self.Bind(wx.EVT_MOTION, self.OnMouseMove)
		self.Bind(wx.EVT_RIGHT_UP, self.OnExit)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_WINDOW_CREATE, self.SetWindowShape)
#_______________________инициализация флагов и т.п.

		self.add = os.getcwdb()
		self.catalog_number=0
		self.hint=0
#_____________________________________________________________________________методы класса_____________________________________________________________________________________


#	def Mbox(self, title, text, style): #выводжит сообщения о ошибке
#		return ctypes.windll.user32.MessageBoxW(0, text, title, style)

	def Show_album(self, add=None, catalog_number=0):
		Len_font = 25
		self.catalog_number = self.catalog_number+catalog_number
		if add!=None: self.add=add
		files = []
		dirs = []
		dir_root = []
		dir_root=os.listdir(self.add)
		for q in dir_root:
			if os.path.isdir(self.add+q):
				dirs.append(self.add+q)

		if dirs==[]: 
  #			self.Mbox('', 'В папке отсутствуют каталоги с книгами.', 0)
			image = Image.new('RGB', (int(self.dic['Width_image']), int(
				self.dic['Height_image'])), color=self.dic['rgb_image'])
			sub_text_2 = ['В выбранной', 'папке', 'нет книг']
			s=0
			drawer = ImageDraw.Draw(image)
			font = ImageFont.truetype("arial.ttf", Len_font)
			for i in sub_text_2:
				drawer.text((10, s), i, font=font, fill='black')
				s = s+Len_font
			
			width, height = image.size
			PIL2wx = wx.Bitmap.FromBuffer(width, height, image.tobytes())
			DC_Album = wx.MemoryDC()
			DC_Album.SelectObject(wx.Bitmap(PIL2wx.GetWidth(), PIL2wx.GetHeight()))
			DC_Album.DrawBitmap(PIL2wx, 0, 0, False)
			self.DC_B.Blit(int(self.dic['X_image']), int(self.dic['Y_image']), PIL2wx.GetWidth(), PIL2wx.GetHeight(),
                	            DC_Album, 0, 0)
			dc = wx.ClientDC(self)
			dc.Blit(0, 0, self.bmp_form.GetWidth(), self.bmp_form.GetHeight(), self.DC_B, 0, 0)
			return
		if self.catalog_number > (len(dirs)-1):self.catalog_number=0
		if self.catalog_number < 0:	self.catalog_number = len(dirs)-1
		root = dirs[self.catalog_number]+"\\"
		dir_root = os.listdir(dirs[self.catalog_number]+"\\")
		for q in dir_root:
				if os.path.isfile(root+q):
					files.append(root+q)
		
		global as_there_Form_player
		as_there_Form_player = "root_album"+"**" + str(dirs[self.catalog_number]+"\\")

# рисуем абложку альбома, если картинки нет то пишем название папки
		Flag_Album_png_found = 0
		for i in files:
			if (os.path.splitext(i)[1]) == '.png':
				addr=i
				bmp_Album = wx.Image(addr, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
				DC_Album = wx.MemoryDC()  # выделяем холст в памяти
				# связываем холст с размерами
		#		DC_Album.SelectObject(wx.Bitmap(bmp_Album.GetWidth(), bmp_Album.GetHeight()))
				DC_Album.SelectObject(wx.Bitmap(int(self.dic['Width_image']), int(self.dic['Height_image'])))
				DC_Album.DrawBitmap(bmp_Album, 0, 0, False)
				self.DC_B.Blit(int(self.dic['X_image']), int(self.dic['Y_image']), bmp_Album.GetWidth(), bmp_Album.GetHeight(),
		                           DC_Album, 0, 0)
				Flag_Album_png_found=1
		if Flag_Album_png_found == 0:
				image = Image.new('RGB', (int(self.dic['Width_image']), int(self.dic['Height_image'])), color=self.dic['rgb_image'])
				font = ImageFont.truetype("arial.ttf", Len_font)
				drawer = ImageDraw.Draw(image)
				#text = str(os.path.dirname(addr))
				text = q
				sub_text_2 = []
				sub_text = text.split(' ')
				j = 0
				for i in sub_text:
					if len(i) > int(int(self.dic['Width_image'])/Len_font):
						while j < int(len(i)/(int(self.dic['Width_image'])/Len_font)):
							d = i[(j)*int((int(self.dic['Width_image'])/Len_font)): (j+1)*int((int(self.dic['Width_image'])/Len_font))]
							sub_text_2.append(str(d+"-"))
							j = j+1
					else:
						sub_text_2.append(i)
				s = 0
				for i in sub_text_2:
					drawer.text((10, s), i, font=font, fill='black')
					s = s+Len_font

				width, height = image.size
				PIL2wx = wx.Bitmap.FromBuffer(width, height, image.tobytes())
				DC_Album = wx.MemoryDC()
				DC_Album.SelectObject(wx.Bitmap(PIL2wx.GetWidth(), PIL2wx.GetHeight()))
				DC_Album.DrawBitmap(PIL2wx, 0, 0, False)
				self.DC_B.Blit(int(self.dic['X_image']), int(self.dic['Y_image']), PIL2wx.GetWidth(), PIL2wx.GetHeight(),
                	            DC_Album, 0, 0)
	
		dc = wx.ClientDC(self)
		dc.Blit(0, 0, self.bmp_form.GetWidth(), self.bmp_form.GetHeight(), self.DC_B, 0, 0)
		#передаем в управление адрес выбранного каталога
#_______________________________________________метод вызова класса как функции

#______________________________________________метод рисования окна												
	def SetWindowShape(self, evt=None):
		r = wx.Region(self.bmp_form, self.transparentColour)
		self.hasShape = self.SetShape(r)
#_______________________________________________метод при двойном щелчке мышкой
	def OnDoubleClick(self, evt):
		pass
#_________________________________________________перерисовка окна из холстя в памяти на экран
	def OnPaint(self, evt):
		dc = wx.PaintDC(self)
		dc.Blit(0, 0, self.bmp_form.GetWidth(), self.bmp_form.GetHeight(), self.DC_B, 0, 0)
#________________________________________________закрытие окна
	def OnExit(self, evt):
		self.Close()
#____________________________________________метод при перемещении мыши
	def OnMouseMove(self, evt):
		if evt.Dragging() and evt.LeftIsDown():
			pos = self.ClientToScreen(evt.GetPosition())
			newPos = (pos.x - self.delta.x, pos.y - self.delta.y)
			self.Move(newPos)
#_______________________________________________изменение движка Shift -  !!! ПРИКРУТИЛ ПЕРЕМЕЩЕНИЕ К ПЕРЕМЕЩЕНИЮ МЫШИ !!!____________________________________________________________
	
#		absol=(wx.Point(self.ClientToScreen(evt.GetPosition()).x - self.GetPosition().x, self.ClientToScreen(evt.GetPosition()).y - self.GetPosition().y))
#		self.EVENT_Form_player.update({X2,absol.x-1})
#		self.EVENT_Form_player.update({Y2,absol.y-1})
#
#		if self.EVENT_Form_player[Flag]==self.dic[Shift1_Key]:
#
#			#считаем что перемещение только по X
#			self.EVENT_Form_player[Y2]=self.dic[Shift1_Ymin] # в nin файле Shift1_Ymin=Shift1_Ymax
#			#нормируем граници перемещения по X
#
#			#щелчок мыши может быть на крае движка с лева(меньше меньшего), поэтому ограничиваем минимум
#			if self.EVENT_Form_player[X1]<self.dic[Shift1_Xmin]:self.EVENT_Form_player[X1]=self.dic[Shift1_Xmin]	#возможно X1 и нафиг не нужен
#			if self.EVENT_Form_player[X1]>self.dic[Shift1_Xmax]:self.EVENT_Form_player[X1]=self.dic[Shift1_Xmax]	#возможно X1 и нафиг не нужен
#
#			if self.EVENT_Form_player[X2]<self.dic[Shift1_Xmin]:self.EVENT_Form_player[X2]=self.dic[Shift1_Xmin]
#			if self.EVENT_Form_player[X2]>self.dic[Shift1_Xmax]:self.EVENT_Form_player[X2]=self.dic[Shift1_Xmax]
#
#
#			#  Shift_XScreen, Shift_YScreen - кооринаты отображения движка в памяти которая потом будет блинкать на экран. (попробовать блинкать внутри памяти чтобы не плодить холсты в памяти)   		# рисуем часть экрана 
#			DC_B.Blit(self.dic[Shift1_XScreen], self.dic[Shift1_YScreen], self.dic[Shift1_Width], self.dic[Shift1_Height], self.DC_Mem, self.dic[Shift1_XMem], self.dic[Shift1_YMem], logicalFunc=wx.COPY)
#			# рисуем движок на части экрана
#			DC_B.Blit(self.dic[Shift1_XScreen_Pull], self.dic[Shift1_YScreen_Pull], self.dic[Shift1_Width_Pull], self.dic[Shift1_Height_Pull], self.DC_Mem, self.EVENT_Form_player[X2], self.EVENT_Form_player[Y2], logicalFunc=wx.COPY)
#			# перемещение части экрана с движком на рабочий экран
#			dc.Blit(self.dic[Shift1_XMem], self.dic[Shift1_YMem], self.dic[Shift1_Width], self.dic[Shift1_Height], self.DC_B, self.dic[Shift1_X], self.dic[Shift1_Y], logicalFunc=wx.COPY)
#_________________________________________________________________________________________________________________________________________________________________________________________
		
#____________________________________________метод при отпускании левой клавиши мыши
		
	def OnLeftUp(self, evt):
		if self.HasCapture(): 
			self.ReleaseMouse()

		if self.hint == 0: #стираем подсказки с плеера
			self.ButtonPaint("Initiation")
			dc = wx.ClientDC(self)
			dc.Blit(0, 0, self.bmp_form.GetWidth(),self.bmp_form.GetHeight(), self.DC_B, 0, 0)
			self.hint=1


		pos = self.ClientToScreen(evt.GetPosition())
		origin = self.GetPosition()

		self.delta = wx.Point(pos.x - origin.x, pos.y - origin.y)
		self.EVENT_Form_player.update({'X2': self.delta.x-1})
		self.EVENT_Form_player.update({'Y2': self.delta.y-1})
		# для более понятной записи разбил выбор флага на два этапа
		arr = self.event_map[self.EVENT_Form_player['Y2'], self.EVENT_Form_player['X2']]

		# работаем с картой событий по нажатию кнопок (канал R)
		if arr[0] == self.EVENT_Form_player['Flag']: #проверяем не изменилось ли место события сравнивая его 
			# с флагом установленным в OnLeftDown. В принципе можно убрать проверку

			if int(arr[0]) == int(self.dic['B_Play_Pause_Key']):
				if self.EVENT_Form_player['B_Play_Pause'] != 'Null':
					self.ButtonPaint("B_Stop_OFF")
					self.EVENT_Form_player['B_Stop'] = 0
					if self.EVENT_Form_player['B_Play_Pause']=='1':
						self.EVENT_Form_player['B_Play_Pause'] = '0'
						self.ButtonPaint("B_Pause")
				
					else:
						self.EVENT_Form_player['B_Play_Pause'] = '1'
						self.ButtonPaint("B_Play")

				if self.EVENT_Form_player['B_Play_Pause']== 'Null':
					self.ButtonPaint("B_Stop_OFF")
					self.EVENT_Form_player['B_Stop'] = 0
					self.EVENT_Form_player['B_Play_Pause'] = "1"
					self.ButtonPaint("B_Play")

			if int(arr[0]) == int(self.dic['B_Stop_Key']) and self.EVENT_Form_player['B_Play_Pause'] != 'Null':
				self.ButtonPaint("B_Play_Null")
				self.EVENT_Form_player['B_Play_Pause'] = 'Null'
				if int(self.EVENT_Form_player['B_Stop']):
					self.EVENT_Form_player['B_Stop'] = 0
					self.ButtonPaint("B_Stop_OFF")
				else:
					self.ButtonPaint("B_Stop_ON")
					self.EVENT_Form_player['B_Stop'] = 1

			if int(arr[0]) == int(self.dic['B_Forward_Key']):
				# кнопка используются для переходу по альбомам - часть функционала выключаем 
				self.ButtonPaint("B_Play_Null")
				self.EVENT_Form_player['B_Play_Pause'] = 'Null'
				self.ButtonPaint("B_Stop_OFF")
				self.EVENT_Form_player['B_Stop'] = 0
				self.ButtonPaint("B_Forward_ON")
				self.Show_album(catalog_number=1)

			if int(arr[0]) == int(self.dic['B_Back_Key']):
				# кнопка используются для переходу по альбомам - часть функционала выключаем
				self.ButtonPaint("B_Play_Null")
				self.EVENT_Form_player['B_Play_Pause'] = 'Null'
				self.ButtonPaint("B_Stop_OFF")
				self.EVENT_Form_player['B_Stop'] = 0
				self.ButtonPaint("B_Back_ON")
				self.Show_album(catalog_number=-1)


			if int(arr[0]) == int(self.dic['Menu_key']): #графическая составляющая иконки не меняется
														# - передаем только ключ 
					self.ButtonPaint("Menu_ON")


			dc = wx.ClientDC(self) 
			# рисует картинку в окне. ВАЖНО! если перехватываем событие wx.EVT_PAINT то 															
			# # используем wx.PaintDC(self) в других случаях wx.ClientDC(self)
			# http://python-lab.blogspot.com/2012/10/wxpython-in-action-12.html
			dc.Blit(0, 0, self.bmp_form.GetWidth(),
			        self.bmp_form.GetHeight(), self.DC_B, 0, 0)

#____________________________________________метод при нажатии левой клавиши мыши

	def OnLeftDown(self, evt):									
		self.CaptureMouse()
		#--------------------------------------------------------------
		# кусок кода чтобы перемещение окна было плавным
		pos = self.ClientToScreen(evt.GetPosition())
		origin = self.GetPosition()
		self.delta = wx.Point(pos.x - origin.x, pos.y - origin.y)
		#--------------------------------------------------------------
#	#__ сохраняем событие и координаты
		self.EVENT_Form_player.update({'X1': self.delta.x-1})
		self.EVENT_Form_player.update({'Y1': self.delta.y-1})
		#для удобства назначаем флаг а не определяем его каждый раз (да и быстрее будет...наверное ?)
		# для более понятной записи разбил выбор флага на два этапа
		arr = self.event_map[self.EVENT_Form_player['Y1'], self.EVENT_Form_player['X1']]
		self.EVENT_Form_player.update({'Flag':arr[0]})	

#########добавляем обработк клавиш которые меняются при нажатии клавиши (не при отпускании!!!) #######
		if int(arr[0]) == int(self.dic['B_Back_Key']):
			print("нажата назад офф")
			self.ButtonPaint("B_Back_OFF") #уменбшаем клавишу

		if int(arr[0]) == int(self.dic['B_Forward_Key']):
			print("нажата вперед офф")
			self.ButtonPaint("B_Forward_OFF")  # уменбшаем клавишу

		dc = wx.ClientDC(self)
		dc.Blit(0, 0, self.bmp_form.GetWidth(),
                    self.bmp_form.GetHeight(), self.DC_B, 0, 0)
#____________________________________________перерисовка кнопок которые двигаются и оставлют после себя "шлейф"

	def ButtonPaint(self, key, addr=None):	#перенос кнопок и т.д. на холст в память 
								#пример вызова 		self.ButtonPaint("B_Pause")	

		#КУДА.Blit(в_какое_место_xdest, в_какое_место_ydest, width_картинки,
		#height_картинки, откуда_source=self.DC_B1, смещение_в_self.DC_B1_xsrc,
		#смещение_в_self.DC_B1_ysrc, logicalFunc=wx.COPY, #useMask=False,
		#чтото_про_маску_xsrcMask=-1, ysrcMask=-1)

		global as_there_Form_player
		as_there_Form_player = key  # передача в управляющий класс что нажата клавиша key,
									# далее идет визуализация а логика отработки телодвижений отдается в управление
									# класс  MyApp,
									# да я в курсе что есть ключ Form - пока это игнорируем, т.к. это будет 
									# использоваться в прорисовке движков громкости и т.п. изменяющих после себя
									# фон

		# прорисовка рабочей области
		if key == "Initiation":
			self.DC_B.Blit(0, 0, self.bmp_form.GetWidth(), self.bmp_form.GetHeight(), self.DC_B, 0, 
                            self.bmp_form.GetHeight())
			self.ButtonPaint("B_Play_Null")
			self.ButtonPaint("B_Stop_OFF")
			self.ButtonPaint("B_Forward_ON")
			self.ButtonPaint("B_Back_ON")

		#прорисовка кнопок
		if key=="B_Pause":
			self.DC_B.Blit(int(self.dic['B_Play_Pause_XScreen']), int(self.dic['B_Play_Pause_YScreen']),
                 int(self.dic['B_Play_Pause_Width']), int(self.dic['B_Play_Pause_Height']),
                 self.DC_B, int(self.dic['B_Play_Pause_XMem_ON']), int(self.dic['B_Play_Pause_YMem_ON']))

		if key == "B_Play":
			self.DC_B.Blit(int(self.dic['B_Play_Pause_XScreen']), int(self.dic['B_Play_Pause_YScreen']),
                 int(self.dic['B_Play_Pause_Width']), int(self.dic['B_Play_Pause_Height']),
                 self.DC_B, int(self.dic['B_Play_Pause_XMem_OFF']), int(self.dic['B_Play_Pause_YMem_OFF']))
		
		if key == "B_Play_Null":
			self.DC_B.Blit(int(self.dic['B_Play_Pause_XScreen']), int(self.dic['B_Play_Pause_YScreen']),
                 int(self.dic['B_Play_Pause_Width']), int(self.dic['B_Play_Pause_Height']),
                 self.DC_B, int(self.dic['B_Play_Null_X']), int(self.dic['B_Play_Null_Y']))

		if key == "B_Stop_ON":
			self.DC_B.Blit(int(self.dic['B_Stop_XScreen']), int(self.dic['B_Stop_YScreen']),
                 int(self.dic['B_Stop_Width']), int(self.dic['B_Stop_Height']),
                 self.DC_B, int(self.dic['B_Stop_XMem_ON']), int(self.dic['B_Stop_YMem_ON']))

		if key == "B_Stop_OFF":
			self.DC_B.Blit(int(self.dic['B_Stop_XScreen']), int(self.dic['B_Stop_YScreen']),
                 int(self.dic['B_Stop_Width']), int(self.dic['B_Stop_Height']),
                 self.DC_B, int(self.dic['B_Stop_XMem_OFF']), int(self.dic['B_Stop_YMem_OFF']))

		if key == "B_Forward_ON":
			self.DC_B.Blit(int(self.dic['B_Forward_XScreen']), int(self.dic['B_Forward_YScreen']),
                 int(self.dic['B_Forward_Width']), int(self.dic['B_Forward_Height']),
                 self.DC_B, int(self.dic['B_Forward_XMem_ON']), int(self.dic['B_Forward_YMem_ON']))
			print("печатаю кнопку вперед он")

		if key == "B_Forward_OFF":
			self.DC_B.Blit(int(self.dic['B_Forward_XScreen']), int(self.dic['B_Forward_YScreen']),
                 int(self.dic['B_Forward_Width']), int(self.dic['B_Forward_Height']),
                 self.DC_B, int(self.dic['B_Forward_XMem_OFF']), int(self.dic['B_Forward_YMem_OFF']))
			print("печатаю кнопку вперед офф")
		if key == "B_Back_ON":
			self.DC_B.Blit(int(self.dic['B_Back_XScreen']), int(self.dic['B_Back_YScreen']),
                 int(self.dic['B_Back_Width']), int(self.dic['B_Back_Height']),
                 self.DC_B, int(self.dic['B_Back_XMem_ON']), int(self.dic['B_Back_YMem_ON']))
			print("печатаю кнопку назад он")
		if key == "B_Back_OFF":
			self.DC_B.Blit(int(self.dic['B_Back_XScreen']), int(self.dic['B_Back_YScreen']),
                 int(self.dic['B_Back_Width']), int(self.dic['B_Back_Height']),
                 self.DC_B, int(self.dic['B_Back_XMem_OFF']), int(self.dic['B_Back_YMem_OFF']))
			print("печатаю кнопку назад офф")
	
	def onContext(self):
		self.Bind(wx.EVT_MENU, self.Root_dir, id=1)
		self.Bind(wx.EVT_MENU, self.onPopup, id=2)

		menu = wx.Menu()
		itemOne = menu.Append(1, "Выбрать библиотеку")
		itemTwo = menu.Append(2, "Найти книгу")
		itemThree = menu.Append(3, "...")

		self.PopupMenu(menu)
		menu.Destroy()

	def onPopup(self, idd):  # диалог выбора каталога
			global as_there_Form_player
			as_there_Form_player = "root"+"**"+ "еще одно меню"

	def Root_dir(self, idd):  # диалог выбора каталога
		dialog = wx.DirDialog(None, "Choose a directory:",
		                      style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
		if dialog.ShowModal() == wx.ID_OK:
			global as_there_Form_player
			as_there_Form_player = "root"+"**" + dialog.GetPath()+"\\"

#############################################################################################################


class Book:

	def __init__(self, add):  # инициализация
		self.root_dir = add  # инициализация каталога с книгой, пока считаем что вложенных папок нет
		self.flag = 1  # флаг для работы с паузой
		# указатель на текущую позицию воспроизведения файла - возможно нафиг ненужен
		self.list_mp3_target = []
		self.i = 0  # номер проигрываемого файла из списка
		self.j = 0  # номер проигрываемой позиции в файле
		self.v = 0.5  # громкость 50%
		self.list_mp3 = []  # создаем пустой список в формате имя файла/время воспроизведения
		folder = []

        # Получаем список файлов и параметров файла
        # получаем список подкаталогов и файлов каталога, возможно этот и следующий цикл можно объеденить

		print(self.root_dir)
		for i in os.walk(self.root_dir):
			folder.append(i)
		for address, dirs, files in folder:
			for file in files:
				if os.path.splitext(address+file)[1] == '.mp3':
					audio = MP3(address+file)
                    # составляет список файлов mp3
					self.list_mp3.append((address+file, audio.info.length, 0))
		#возможно тудаже закидываем навазние песни и т.п.->
		#audio["title"]-дает название титла,
		#еще ключевые слова: album, artist...
		#mutagen.File(audio)- весь список свойств файла
		if self.list_mp3 == []:
			print("Ай яй яй, в каталоге нет mp3 книг,")  
			print("возможно они подкаталоге или другой формат,")
			print("надо сделать защиту!!!!")

		self.list_mp3.sort()  # сортируем список файлов чтобы озвучивать в правильном порядке
		self.len = len(self.list_mp3)  # длинна списка

	def unload(self):
		pygame.mixer.music.unload

	def play(self, i=0, j=0):
		self.i = i
		self.j = j
        # устанавливает номер файла в списке который нужно проигрывать - список даст его адрес.
		pygame.mixer.music.load(self.list_mp3[int(self.i)][0])
#		pygame.mixer.music.set_pos(self.j)			#устанавливает позицию прослушивания - mp3 не поддерживает установку позиции!!!!
        # теоретически должен стартовать нужный файл с указанной позиции
		global as_there_Book  # глобальная переменная для передачи состояния в управляющий класс
		as_there_Book = "начали чегото воспроизводить"
		pygame.mixer.music.play()


	#возвращает позицию воспроизведения текущего фрагмента ввиде списка первое значение номер файла, второе позиция в нем (ну должен по крайней мере вернуть)
	def get_pos(self):
		return(self.i, self.j)

	def pause(self):
		if self.flag == 1:
			pygame.mixer.music.pause()
			self.flag = 0
		else:
			pygame.mixer.music.unpause()
			self.flag = 1
#		return(self.flag)

	def stop(self):
		pygame.mixer.music.stop()

    # подразумевается что врядли кто будет устанавливать звук отрицательным...
	def volume(self, v):
		if self.v > 1: 
			self.v = 1.0
		pygame.mixer.music.set_volume(self.v)

	def next(self, i):  # загружает в очередь следующий файл - возможно уже ненужная функция
		pygame.mixer.music.queue(self.list_mp3[i][0])

#конец описания класса

#САМЫЙ ГЛАВНЫЙ КЛАСС - УПРАВЛЕНИЕ
class MyApp(wx.App):
	def MainLoop(self):

		evtloop = wx.GUIEventLoop()
		old = wx.EventLoop.GetActive()
		wx.EventLoop.SetActive(evtloop)
		
		play_pause = 0
		play_load=0
		load_unload=0
		root = None

		while self.keepGoing:
			global as_there_Form_player
			if as_there_Form_player!=None: # пришло сообщение от Form_player (на чтото нажали)
			# значение ответа (часть обрабатывать не требуется, использемые пометим "*"):
			#	*			B_Pause
			#	*			B_Play
			#	*			B_Stop_ON
			#				B_Stop_OFF
			#	*			B_Forward_ON
			#				B_Forward_OFF
			#	*			B_Back_ON
			#				B_Back_OFF
			#	*			Menu_ON	
				Key_Value=as_there_Form_player.split('**')
				as_there_Form_player = None #обнуляем чтобы принимать значения от внешних функций, даже елси они 
				#изменились при выполнении (типа вызов меню -> выбор каталога) 	
				#print("ключ: "+Key_Value[0])
				print("*перемменные в начале опроса*")
				print(str(Key_Value))
				print("play_pause =" + str(play_pause))
				print("play_load =" + str(play_load))
				print("***************")

				if Key_Value[0] == 'Menu_ON':  # вызывает меню выбора всякого разного
					print("выбрано меню")
					self.frame.onContext() #вызов всплывающего меню
				
				#обработка подменю "выбор каталога с книгами"
				if Key_Value[0] == 'root':
					print("выбран каталог с книгами, передано в показ/выбор альбома")
					self.frame.Show_album(Key_Value[1])

				if Key_Value[0] == 'root_album':
					print("Получен адрес выбранного альбома " + str(Key_Value[1]))
					root = Key_Value[1]
					if load_unload==0: #если каталог с музыкой загружен впервые  
						B = Book(root)
						load_unload=1
						print("загружаю файл в первый раз")
						print("load_unload=" + str(load_unload))
					else: #каталог с музыкой уже загружен, нужно освободить ресурс
						print("производжу смену каталога")
						B.stop()
						play_pause = 0
						play_load = 0
						print("выгружаю музыку")
						B.unload()
						print("загружаю нолвую музыку")
						B = Book(root)
					
						
						print("load_unload="+ str(load_unload))

				if Key_Value[0] == 'B_Play' and root != None and play_pause == 0 and play_load==0:  
					# первый раз загружаем файл и воспроиводим его
					#root пока не определен - брать после выбора каталога!!!!
					B.play()
					play_pause = 1
					play_load = 1
					print("играю музыку первй раз")
					print("play_pause ="+ str( play_pause))
					print("***************")
				
				if Key_Value[0] == 'B_Play' and root != None and play_pause == 0 and play_load == 1:
					# воспроиводим файл поставленный на паузу
					B.pause()
					play_pause = 1
					print("пауза")
					print("play_pause =" + str(play_pause))
					print("***************")

				if Key_Value[0] == 'B_Pause' and root != None and play_pause == 1 and play_load == 1:  # ставим файл на паузу
					B.pause()
					play_pause = 0
					print("пауза")
					print("play_pause =" + str(play_pause))
					print("***************")
					

				if Key_Value[0] == 'B_Stop_ON' and root != None:  # воспроиводим файл
					B.stop()
					play_pause = 0
					play_load = 0  # сбрасываем чтобы можно было опять загрузить файл и воспроивести его с начала


					global q

			while evtloop.Pending():
				evtloop.Dispatch()
			evtloop.ProcessIdle()

		wx.EventLoop.SetActive(old)

	def OnInit(self):

		self.frame = Form_player()  # MyFrame(None, -1, "This is a test")
		self.frame.Show(True)
		self.SetTopWindow(self.frame)

		self.keepGoing = True
		return True
#####################################################################################################################
as_there_Form_player = None
as_there_Book = None
app = MyApp()
app.MainLoop()
