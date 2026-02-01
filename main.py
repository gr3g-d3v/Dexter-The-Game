import pygame # «Сматли, эта такая каманда кампьютиру! Она гаварит: "Эй, давай играть и делать самуи крутые мультики!" 🎮✨ Это как бута мы достали бальшуууую каробку с конструктарам, штабы пастроить сваю игу... игу... игру! 🤖🧸 Кароче, пыщ-пыщ и гатова! 🚀💥»
import yaml
import sys
import os
import json

#устанавливаем все нужные библиотеки сразу чтобы не искать если ли например библиотеки (нужные версии) на компе где скачана наша ААА игра cl


class Engine:
    def __init__(self, name, config_file="config.yml"):   # <--- это конструктор
        pygame.init() # свойства игры
        with open(config_file, "r", encoding="utf-8") as cfg:
            self.config=yaml.safe_load(cfg)

        self.width=self.config['screen']['width']
        self.height=self.config['screen']['height']
        self.name=name
        self.current_scene = None
        self.current_line = 0
        self.is_typing = False
        self.text_speed = self.config['text']['speed']
        self.auto_mode = False
        self.auto_timer = 0
        self.auto_delay = 3000

        self.backgrounds = {}
        self.characters = {}
        self.sounds = {}
        self.music = {}

        # загрузка ресурсов
        self.load_resources()

        # история диалогов
        self.dialog_history = []

        # текущие отображаемые элементы
        self.current_background = None
        self.current_characters = {}
        self.choices = []
        self.waiting_for_choice = False
        pass

    def fonts_loading(self):
        try:
            font_path = os.path.join('fonts', self.config['fonts']['main']) #путь к шрифтам
            self.font_dialog = pygame.font.Font(font_path, self.config['fonts']['dialog_size']) #открытый, необходимый шрифт который сохраняется в поле(переменной)
            self.font_name = pygame.font.Font(font_path, self.config['fonts']['name_size'])
            self.font_choice = pygame.font.Font(font_path, self.config['fonts']['choice_size'])
        except:
            # используем системные шрифты если свои не найдены
            self.font_dialog = pygame.font.SysFont('Arial', 24)
            self.font_name = pygame.font.SysFont('Arial', 20, bold=True)
            self.font_choice = pygame.font.SysFont('Arial', 22)

    def pics_loading(self): #активация функции
        for bg_pics in os.listdir("backgrounds"): #цикл проходит по всем файлам в нашей папке с фонами
            if bg_pics.endswith((".jpg")):
                path=os.path.join("backgrounds", bg_pics) #создается путь к файлу
                try:
                    picture=pygame.image.load(path).convert() #дали путь и она загружает файл
                    picture=pygame.transform.scale(picture, (self.width, self.height)) #растягивает по ширине экрана
                    self.backgrounds[bg_pics.split('.')[0]] = picture # добавляет в список (!!!теория!!!)
                except Exception as e:
                    print(f"Ошибка загрузки фона {bg_pics}: {e}")

        for ch_pics in os.listdir("characters"): #цикл проходит по всем файлам в нашей папке
            if ch_pics.endswith((".png")):
                path=os.path.join("characters", ch_pics) #создается путь к файлу
                try:
                    picture=pygame.image.load(path).convert_alpha() #дали путь и она загружает файл в виде пнг
                    self.characters[ch_pics.split('.')[0]] = picture # добавляет в список (!!!теория!!!)
                except Exception as e:
                    print(f"Ошибка загрузки персонажа {ch_pics}: {e}")



morgan=Engine("Dexter")
moser=Engine("Brian")

morgan.pics_loading()