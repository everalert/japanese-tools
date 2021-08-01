# -*- coding: utf-8 -*-

# Insert DateTime add-on for Anki 2.1
# Copyright (C) 2021  EVAL/Galeforce

# Intended to be used as a way of quickly filling an ID-type
# sort field from the card editor in decks where imported and
# live-added cards are mixed.


from aqt import gui_hooks
from aqt.editor import Editor, EditorWebView
from aqt.qt import *
from aqt.utils import tooltip

from datetime import datetime


def insert_id(editor: Editor):
	dt = datetime.now()
	new_id = dt.strftime("%Y.%m.%d %H:%M:%S")
	try:
		editor.doPaste(html=new_id, internal=True)
	except Exception as ex:
		tooltip(str(ex))

def add_context_menu_item(webview: EditorWebView, menu: QMenu):
	editor = webview.editor
	a: QAction = menu.addAction('Insert DateTime')
	a.triggered.connect(lambda _, e=editor: insert_id(e))

def init():
	gui_hooks.editor_will_show_context_menu.append(add_context_menu_item)


init()