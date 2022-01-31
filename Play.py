
import wx								#используем для проприсовки фрейма
import imageio 								#используем для заполнения карты событий
import io
import chardet
import os
import codecs
# https://mutagen.readthedocs.io/en/latest/user/gettingstarted.html
from mutagen.mp3 import MP3
import pygame
pygame.init()		#не знаю зачем, но иначе не работает, а может и работает - надо попробывать
pygame.mixer.init() 	#не знаю зачем, но иначе не работает, а может и работает - надо попробывать


class Form_player(wx.Frame):

	# глобальная переменная для передачи состояния в управляющий класс

# долго думал и решил что в папке есть файл ini_Form.txt
# в которым сохраняем список ключей - просто передавать их при инициализации долшо и чревато ошибками. 
# при выборе нового скрина - передаем при формировании класса название ini файла в котором прописываем параметры
# ключи: R, G, B- цвет маски, IMAGE_PATH_M-файл карты событий.png, IMAGE_PATH_BG-фон, IMAGE_PATH_B-кнопки
# B*_Width, B*_Height - параметры кнопки * (кнопки считаем с лева направо и с верху вниз)
# Shift*_ - параметры сдвигаемой кнопки - ПОКА КНОПКИ СДВИГАЮТСЯ ТОЛЬКО ПО ГОРИЗОНТАЛИ!!!! от MIN до MAX


# ПРАВИЛА ДЛЯ ФОРМИРОВАНИЯ КАРТЫ СОБЫТИЙ (event_map) - цвет в канале R !!!
# 0 значение по умолчанию, НЕ ИСПОЛЬЗОВАТЬ В КАРТЕ СОБЫТИЙ!!
# значения с 1 по 255 - любые, привязка событий в управляющем классе


#______________________Инициация переменных класса

	def __init__(self, filename='ini.txt', **kwargs):
		wx.Frame.__init__(self, None, -1, "Shaped Window", style = wx.FRAME_SHAPED | wx.SIMPLE_BORDER )
		
#=========================== работает ===============================================================================================
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

		self.EVENT_Form_player.update({'B_Play_Pause':0})
		self.EVENT_Form_player.update({'B_Stop': 1})
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

#_____________________________________________________________________________методы класса_____________________________________________________________________________________

	# заполняем линию загрузки/воспроиведения
	def Show_album (self, add):
		folder = os.listdir(add)
		files = os.listdir(add+folder[0])
		for i in files:
			if (os.path.splitext(i)[1]) == '.png':
				addr=(str(add)+str(folder[0])+"\\"+str(os.path.splitext(i)[0])+str(os.path.splitext(i)[1]))
				self.ButtonPaint("Album", addr)   
				dc = wx.ClientDC(self)
				dc.Blit(0, 0, self.bmp_form.GetWidth(), self.bmp_form.GetHeight(), self.DC_B, 0, 0)
				

				


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

		pos = self.ClientToScreen(evt.GetPosition())
		origin = self.GetPosition()

		self.delta = wx.Point(pos.x - origin.x, pos.y - origin.y)
		self.EVENT_Form_player.update({'X2': self.delta.x-1})
		self.EVENT_Form_player.update({'Y2': self.delta.y-1})
		# для более понятной записи разбил выбор флага на два этапа
		arr = self.event_map[self.EVENT_Form_player['Y2'], self.EVENT_Form_player['X2']]

		# присваиваиваем глобальноcть переменной as_there_Form_player
#		global as_there_Form_player
		#_______________________________________________________________________________________ 

		# работаем с картой событий по нажатию кнопок
		if arr[0] == self.EVENT_Form_player['Flag']:


#			if int(arr[0]) == int(self.dic['Menu_key']): 
#				as_there_Form_player = "Кошмар выбрали меню!!!!"


			if int(arr[0]) == int(self.dic['B_Play_Pause_Key']):
				if int(self.EVENT_Form_player['B_Play_Pause']):
						self.EVENT_Form_player['B_Play_Pause'] = 0
						self.ButtonPaint("B_Pause")
				else:
					self.ButtonPaint("B_Play")
					self.EVENT_Form_player['B_Play_Pause'] = 1

			if int(arr[0]) == int(self.dic['B_Stop_Key']):
				if int(self.EVENT_Form_player['B_Stop']):
					self.EVENT_Form_player['B_Stop'] = 0
					self.ButtonPaint("B_Stop_ON")
				else:
					self.ButtonPaint("B_Stop_OFF")
					self.EVENT_Form_player['B_Stop'] = 1

			if int(arr[0]) == int(self.dic['B_Forward_Key']):
				if int(self.EVENT_Form_player['B_Forward']):
					self.EVENT_Form_player['B_Forward'] = 0
					self.ButtonPaint("B_Forward_ON")
				else:
					self.ButtonPaint("B_Forward_OFF")
					self.EVENT_Form_player['B_Forward'] = 1

			if int(arr[0]) == int(self.dic['B_Back_Key']):
				if int(self.EVENT_Form_player['B_Back']):
					self.EVENT_Form_player['B_Back'] = 0
					self.ButtonPaint("B_Back_ON")
				else:
					self.ButtonPaint("B_Back_OFF")
					self.EVENT_Form_player['B_Back'] = 1

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
#____________________________________________перерисовка кнопок которые двигаются и оставлют после себя "шлейф"

	def ButtonPaint(self, key, addr=None):	#перенос кнопок и т.д. на холст в память 
								#пример вызова 		self.ButtonPaint("B_Pause")	


		#КУДА.Blit(в_какое_место_xdest, в_какое_место_ydest, width_картинки,
		#height_картинки, откуда_source=self.DC_B1, смещение_в_self.DC_B1_xsrc,
		#смещение_в_self.DC_B1_ysrc, logicalFunc=wx.COPY, #useMask=False,
		#чтото_про_маску_xsrcMask=-1, ysrcMask=-1)

		global as_there_Form_player
		as_there_Form_player = key  # передача в "космос" что нажата клавиша key,
									# далее идет визуализация а логика отработки телодвижений отдается в управление
									# класс  MyApp,
									# да я в курсе что есть ключ Form - пока это игнорируем, т.к. это будет 
									# использоваться в прорисовке движков громкости и т.п. изменяющих после себя
									# фон

		if key == "Album":
			print(addr)
			bmp_Album = wx.Image(addr, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
			DC_Album = wx.MemoryDC()  # выделяем холст в памяти
			# связываем холст с размерами
			DC_Album.SelectObject(wx.Bitmap(bmp_Album.GetWidth(), bmp_Album.GetHeight()))
			DC_Album.DrawBitmap(bmp_Album, 0, 0, False)
			self.DC_B.Blit(int(self.dic['X_image']), int(self.dic['Y_image']), bmp_Album.GetWidth(), bmp_Album.GetHeight(),
                            DC_Album, 0, 0)


		# прорисовка рабочей области
		if key == "Form":
			self.DC_B.Blit(0, 0, self.bmp_form.GetWidth(), self.bmp_form.GetHeight(), self.DC_B, int(
			self.dic['X_mem']), int(self.dic['Y_mem']))

		#прорисовка кнопок
		if key=="B_Pause":
			self.DC_B.Blit(int(self.dic['B_Play_Pause_XScreen']), int(self.dic['B_Play_Pause_YScreen']),
                 int(self.dic['B_Play_Pause_Width']), int(self.dic['B_Play_Pause_Height']),
                 self.DC_B, int(self.dic['B_Play_Pause_XMem_ON']), int(self.dic['B_Play_Pause_YMem_ON']))

		if key == "B_Play":
			self.DC_B.Blit(int(self.dic['B_Play_Pause_XScreen']), int(self.dic['B_Play_Pause_YScreen']),
                 int(self.dic['B_Play_Pause_Width']), int(self.dic['B_Play_Pause_Height']),
                 self.DC_B, int(self.dic['B_Play_Pause_XMem_OFF']), int(self.dic['B_Play_Pause_YMem_OFF']))

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

		if key == "B_Forward_OFF":
			self.DC_B.Blit(int(self.dic['B_Forward_XScreen']), int(self.dic['B_Forward_YScreen']),
                 int(self.dic['B_Forward_Width']), int(self.dic['B_Forward_Height']),
                 self.DC_B, int(self.dic['B_Forward_XMem_OFF']), int(self.dic['B_Forward_YMem_OFF']))

		if key == "B_Back_ON":
			self.DC_B.Blit(int(self.dic['B_Back_XScreen']), int(self.dic['B_Back_YScreen']),
                 int(self.dic['B_Back_Width']), int(self.dic['B_Back_Height']),
                 self.DC_B, int(self.dic['B_Back_XMem_ON']), int(self.dic['B_Back_YMem_ON']))

		if key == "B_Back_OFF":
			self.DC_B.Blit(int(self.dic['B_Back_XScreen']), int(self.dic['B_Back_YScreen']),
                 int(self.dic['B_Back_Width']), int(self.dic['B_Back_Height']),
                 self.DC_B, int(self.dic['B_Back_XMem_OFF']), int(self.dic['B_Back_YMem_OFF']))

#############################################################################################################
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

 #               if os.path.splitext(address+file)[1]=='.png' or os.path.splitext(address+file)[1]=='.jpg': #выбираем картинки
 #                   self.image= pygame.image.load(address+file)

		self.list_mp3.sort()  # сортируем список файлов чтобы озвучивать в правильном порядке
		self.len = len(self.list_mp3)  # длинна списка
		
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
		rut = None

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
				print(as_there_Form_player)

				if as_there_Form_player == 'Menu_ON': #вызывает меню выбора каталога книг
					dialog = wx.DirDialog(None, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
					if dialog.ShowModal() == wx.ID_OK:
						rut = dialog.GetPath()+'\\'
						print(rut)
						self.frame.Show_album(rut)
#						B = Book(rut)
				
				if as_there_Form_player == 'B_Play' and rut != None and play_pause==0 : # воспроиводим файл
					B.play()
					play_pause=1
					print("играю музыку")
				
				if (as_there_Form_player == 'B_Pause' or as_there_Form_player == 'B_Play') and rut != None and play_pause == 1:  # воспроиводим файл
					B.pause()
					print("пауза")

				
				if as_there_Form_player == 'B_Stop_ON' and rut != None:  # воспроиводим файл
					B.stop()
					play_pause = 0
				
				as_there_Form_player=None



#				global q
#				if q == 1:
#					dialog = wx.DirDialog(None, "Choose a directory:",style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
#					if dialog.ShowModal() == wx.ID_OK:
#						print (dialog.GetPath())
#				print(q)
#				if q == 1:
#					rut1 = dialog.GetPath()+ '\\'
#					print("rut1=" + rut1)
#					rut = "D:\PY\\"
#					print("rut=" + rut)
#					if rut1==rut: print("УРа всме рОвно")  
#					print(rut)
#					B = Book(rut1)
#					B.play()
#				q=2
#				print(as_there_Book)

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
#####################################################################################################################




as_there_Form_player = None
as_there_Book = None
app = MyApp()
app.MainLoop()