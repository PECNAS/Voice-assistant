import webbrowser
import datetime
import keyboard
import re
import sys
import speech_recognition as sr
import pyttsx3
import eel
import threading
import json
import os
import apiai

from pyowm import OWM
from pyowm.utils.config import get_default_config

eel.init("web")

with open("config.json", 'r', encoding='utf-8') as file:
	config = json.load(file)

config['dictation'] = False
config['owm_state'] = None

owm_config_dict = get_default_config()
owm_config_dict['language'] = 'ru'
owm = OWM(config['owm_token'], owm_config_dict)

def get_weather(query):
	try:
		mgr = owm.weather_manager()
		observation = mgr.weather_at_place(query)
		w = observation.weather
		wind = w.wind()

		if 45 > wind['deg'] > 316 or wind['deg'] == 0:
			wind_direction = "Северный"
		elif 135 > wind['deg'] > 46:
			wind_direction = "Восточный"
		elif 225 > wind['deg'] > 136:
			wind_direction = "Южный"
		elif 315 > wind['deg'] > 226:
			wind_direction = "Северный"

		return config['phrases']['weather'].format(int(w.temperature('celsius')['temp']),
											w.detailed_status,
											wind_direction,
											w.wind()['speed'])
	except Exception as e:
		return config['phrases']['unknown_city']

def talk(text):
	engine.say(text)
	eel.add_to_log(f"{config['assistant_name']}: {text}")
	engine.startLoop(False)
	engine.iterate()
	engine.endLoop()

def tap(text):
	query = query.replace("запятая", ",")
	query = query.replace("восклицательный знак", "!")
	query = query.replace("знак вопроса", "?")
	query = query.replace("точка", ".")
	query = query.replace("кавычка", '"')
	keyboard.write(text)

def hot(combination):
	try:
		keyboard.press_and_release(combination)
	except ValueError:
		talk(config['phrases']['unknown_combination'])

def start(path):
	try:
		os.startfile(path)
	except FileNotFoundError:
		talk(config['phrases']['unknown_programm'])

def link(href):
	try:
		webbrowser.open(href)
	except Exception as e:
		print(repr(e))
		print(e)
		print(dir(e))


def handler(query):
	if config['owm_state'] != None:
		talk(get_weather(query))
		config['owm_state'] = None
		return 0

	for phrase in config['query_phrases']:
		if query.startswith(phrase['phrase']):
			if phrase['type'] == "web_find":
				query = query.replace(phrase['phrase'], "")
				webbrowser.open(f"https://www.google.com/search?q={query}")
			elif phrase['type'] == "dictation_start":
				config['dictation'] = True
				query = query.replace(phrase['phrase'], "")
				tap(query)

			elif phrase['type'] == "dictation_stop":
				if config['dictation'] == True:
					config['dictation'] = False
					talk(config['phrases']['dictation_stoped'])

			return 0

	for command in config['user_commands']: # цикл по самим командам(список словарей)
		if query == command['phrase'].lower(): # если запрос совпадает с командой
			if command['type'] == "Нажатие": # задаем функции 
				func = tap
			elif command['type'] == "Сочетание клавиш":
				func = hot
			elif command['type'] == "Запуск программы":
				func = start
			elif command['type'] == "Открыть ссылку":
				func = link
			func(command['action'].lower()) # вызываем функцию через переменную
			return 0 # завершаем цикл и функцию

	if query.startswith("посчитай"):
		try:
			query = query.replace("х", "*").replace("посчитай", "")
			talk(eval(query))
		except SyntaxError:
			eel.add_to_log(config['phrases']['unavailable_calculation'])
	elif query == "сколько время":
		now = datetime.datetime.now()
		talk("Сейчас " + str(now.hour) + ":" + str(now.minute))

	elif config['owm_state'] == None and query == "какая погода":
		talk(config['phrases']['get_city'])
		config['owm_state'] = "get_towm"

	elif config['dictation'] == True:
		tap(query)
	else:
		request = apiai.ApiAI('7f01246612e64e3f89264a85a965ddd3').text_request()
		# На каком языке будет послан запрос
		request.lang = 'ru'
		# ID Сессии диалога (нужно, чтобы потом учить бота)
		request.session_id = '3301megabot'
		# Посылаем запрос к ИИ с сообщением от юзера
		request.query = query
		responseJson = json.loads(request.getresponse().read().decode('utf-8'))
		# Разбираем JSON и вытаскиваем ответ
		response = ''
		response = responseJson['result']['fulfillment']['speech'] 
		# Если есть ответ от бота - выдаём его,
		# если нет - бот его не понял
		if response:
			talk(response)
		else:
			talk(config['phrases']['dont_understand'])

def assistant_main():
	eel.add_to_log(config['states']['started'])
	r = sr.Recognizer() # инициализируем распознователь
	m = sr.Microphone(device_index=config['device_index']) # инициализируем микрофон

	engine.setProperty('voice', config['voice_id']) # выставляем нужный голос

	while running.is_set():
		with m as source:
			r.adjust_for_ambient_noise(source, duration=.5) # фильтруем внешние шумы
			audio = r.listen(source) # слушаем
		try:
			query = r.recognize_google(audio, language="ru-RU") # распознаем
			if config['appeal'] == True:
				if query.startswith(config['assistant_name']):
					eel.add_to_log(f"You: {query}")
					query = query.strip(f"{config['assistant_name']} ")
					handler(query.lower())
			else:
				eel.add_to_log(f"You: {query}")
				handler(query.lower())

		except sr.UnknownValueError: # тут исключение на пустой voice
			pass # пропускаем эту ошибку
		except sr.RequestError: # тут исключение на запрос
			eel.add_to_log(config['phrases']['connection_error'])

def get_listen_devices():
	array = []
	for index, name in enumerate(sr.Microphone.list_microphone_names()):
		if index != 0:
			array.append({'name': name,
						'index': index})

	return array

def get_voices():
	array = []
	for voice in engine.getProperty('voices'):
		array.append({'voice_id': voice.id,
					'name': voice.name})
	return array

def write_to_config():
	with open("config.json", 'w', encoding="utf-8") as file:
		json.dump(config, file, ensure_ascii=True)

@eel.expose
def delete_command(c_type, c_phrase, c_action):
	print(config['user_commands'])
	c_dict = {"type": c_type, "phrase": c_phrase, "action": c_action}
	print(c_dict)
	config['user_commands'].remove(c_dict)
	write_to_config()

@eel.expose
def add_user_command(c_type, c_phrase, c_action):
	c_dict = {"type": c_type, "phrase": c_phrase, "action": c_action}
	if c_dict not in config['user_commands']: # если команды не существует
		config['user_commands'].append(c_dict) # добавляем в конфиг
		write_to_config() # и записываем в файл
		return True
	else:
		return False

@eel.expose
def update_config(appeal, assistant_name, device_index, voice_id):
	config['appeal'] = appeal
	config['assistant_name'] = assistant_name
	config['device_index'] = int(device_index)
	config['voice_id'] = voice_id

	write_to_config()

	engine.setProperty('voice', config['voice_id']) # выставляем нужный голос

@eel.expose
def get_settings():
	dict_to_return = {}

	dict_to_return['appeal'] = config['appeal']
	dict_to_return['assistant_name'] = config['assistant_name']
	dict_to_return['devices'] = get_listen_devices()
	dict_to_return['voices'] = get_voices()
	dict_to_return['device_index'] = config['device_index']
	dict_to_return['voice_id'] = config['voice_id']
	dict_to_return['user_commands'] = config['user_commands']

	return dict_to_return

@eel.expose
def assistant_stop():
	running.clear()
	thread.join()

	eel.add_to_log(config['states']['stoped'])

@eel.expose
def assistant_start():
	global running
	running = threading.Event()
	running.set()

	if len(threading.enumerate()) == 1: # если запущен только главный поток
		global thread
		thread = threading.Thread(target=assistant_main)
		thread.start()
	else:
		eel.add_to_log(config['phrases']['assistant_already_started'])


if __name__ == "__main__":
	global engine
	engine = pyttsx3.init()
	eel.start("main.html", mode='chrome', size=(1080, 780))