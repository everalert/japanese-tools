#!python3
# -*- coding: utf-8 -*-

# Y!Furigana Inserter add-on for Anki 2.1
# Copyright (C) 2021  EVAL/Galeforce

# Replaces selected field with content generated from the Yahoo Japan
# Furigana API in the format required for Anki's Japanese Support addon.
# Requires you to sign up and get an API key from Yahoo Japan, which
# may require a Japanese mobile phone number. Changes cannot be undone.


from aqt import mw, gui_hooks
from aqt.editor import Editor, EditorWebView
from aqt.qt import *
from aqt.utils import tooltip

import requests, re
import xml.etree.ElementTree as ET
from datetime import datetime


def furigana_get_words(sentence: str):
	xml_string = requests.get(get_yahoo_uri(sentence))
	xml_root = ET.fromstring(xml_string.content)
	return xml_root.findall('{urn:yahoo:jp:jlp:FuriganaService}Result/{urn:yahoo:jp:jlp:FuriganaService}WordList/{urn:yahoo:jp:jlp:FuriganaService}Word')

def furigana_parse_word(element):
	output = u""
	if element.find('{urn:yahoo:jp:jlp:FuriganaService}SubWordList') != None:
		for subword in element.findall('{urn:yahoo:jp:jlp:FuriganaService}SubWordList/{urn:yahoo:jp:jlp:FuriganaService}SubWord'):
			output += furigana_parse_word(subword)
	else:
		surface = element.find('{urn:yahoo:jp:jlp:FuriganaService}Surface')
		furigana = element.find('{urn:yahoo:jp:jlp:FuriganaService}Furigana')
		if furigana != None and furigana.text != surface.text:
			output += " "+surface.text+"["+furigana.text+"]"
		else:
			output += surface.text
	return output

def get_yahoo_uri(sentence: str):
	cfg = mw.addonManager.getConfig(__name__)
	API_KEY = cfg.get('api_key', True)
	GRADE = str(cfg.get('grade', True))
	return 'https://jlp.yahooapis.jp/FuriganaService/V1/furigana?appid='+API_KEY+'&grade='+GRADE+'&sentence='+sentence

def cleanup_text(text: str):
	s = text
	p = r'(\[[\s\S]+?\]|\s)'
	while re.search(p, s) != None:
		s = re.sub(p, '', s)
	return s

def insert_furigana(editor: Editor):
	editor.loadNoteKeepingFocus()
	text = cleanup_text(editor.note.fields[editor.currentField])
	output = ''
	for word in furigana_get_words(text):
		output += furigana_parse_word(word)
	try:
		editor.note.fields[editor.currentField] = ''
		editor.loadNoteKeepingFocus()
		editor.doPaste(html=output.strip(), internal=True)
	except Exception as ex:
		tooltip(str(ex))

def add_context_menu_item(webview: EditorWebView, menu: QMenu):
	editor = webview.editor
	a: QAction = menu.addAction('Y!Furigana')
	a.triggered.connect(lambda _, e=editor: insert_furigana(e))

def init():
	gui_hooks.editor_will_show_context_menu.append(add_context_menu_item)


init()