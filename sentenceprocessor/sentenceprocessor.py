#!python3
# -*- coding: utf-8 -*-

import os, re, copy, requests
import pyexcel_ods as ods
import xml.etree.ElementTree as ET
from pydub import AudioSegment, effects
from io import BytesIO

from spkeys import YAHOOJAPAN_API_KEY, AZURE_KEY1, AZURE_KEY2, AZURE_LOCATION, AZURE_TOKEN_ENDPOINT, AZURE_VOICE_ENDPOINT



FILENAME = 'SKMN2G.ods'
SHEET_IN = 'data'
SHEET_OUT = SHEET_IN+'_ruby'

FURIGANA_COLUMNS = [6,7,8,10]
FURIGANA_ROW_SEPARATOR = '''
'''

AUDIO_FOLDER = 'SKMN2G/'
AUDIO_COLUMNS = [6,7]
AUDIO_ID_COLUMN = 5 # unique prefixes that are combined with column headers to make filenames
AUDIO_FORMAT = 'riff-48khz-16bit-mono-pcm' # wav
AUDIO_EXPORT_FORMAT = { 'ext':'.ogg', 'format':'ogg', 'codec':'libvorbis', 'bitrate':'96000', 'params':[]}
AUDIO_VOICE = [
	{ 'name':'ja-JP-NanamiNeural', 'prosody':{'pitch':'-12Hz','rate':'1.15'} },
	{ 'name':'ja-JP-KeitaNeural', 'prosody':{'pitch':'+0Hz','rate':'1.05','volume':'100'} }
]



def process_spreadsheet():
	data = ods.get_data(FILENAME)
	generate_audio_from_sheet(data, SHEET_IN)
	generate_furigana_from_sheet(data, SHEET_IN, SHEET_OUT)
	ods.save_data(FILENAME, data)

### FURIGANA GENERATION

def generate_furigana_from_sheet(ods_data, sheet_in, sheet_out):
	print('Generating Furigana:', end='\r')
	output = copy.deepcopy(ods_data[sheet_in])
	for i,row in enumerate(output):
		if i > 0:
			print('Generating Furigana: '+str(i), end='\r')
			furigana_process_row(row, FURIGANA_COLUMNS)
	print('Generating Furigana: DONE')
	ods_data.update({sheet_out: output})

def furigana_process_row(row, cols):
	sentence = u""
	output = u""
	for i,col in enumerate(cols):
		if i>0:
			sentence += FURIGANA_ROW_SEPARATOR
		sentence += row[col] if len(row)>col else ''
	request = 'https://jlp.yahooapis.jp/FuriganaService/V1/furigana?appid='+YAHOOJAPAN_API_KEY+"&grade=1&sentence="+sentence
	for word in furigana_get_words(request):
		output += furigana_parse_word(word)
	for i,value in enumerate(output.split(FURIGANA_ROW_SEPARATOR)):
		if len(row)>cols[i]:
			row[cols[i]] = value.strip()

def furigana_get_words(uri, head={}):
	xml_string = requests.get(uri)
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

### AUDIO GENERATION

def generate_audio_from_sheet(ods_data, sheet_in):
	print('Generating TTS:', end='\r')
	token = get_speech_token()
	data = ods_data[sheet_in]
	column_headers = []
	audio_items = []
	for i, row in enumerate(data):
		if len(row) > AUDIO_ID_COLUMN and len(row) > max(AUDIO_COLUMNS):
			if i == 0:
				for col in AUDIO_COLUMNS:
					column_headers.append(row[col])
			else:
				print('Generating TTS: '+str(i), end='\r')
				for j, col in enumerate(AUDIO_COLUMNS):
					column_headers.append(row[col])
					audio_items.append(audio_get_item(row, col, AUDIO_ID_COLUMN, column_headers[j]))
				while len(audio_items) > 0:
					item = audio_items.pop()
					audio_process_item(token, item['text'], item['filename'])
	print('Generating TTS: DONE')

def audio_get_item(row, text_col, id_col, header):
	return { 'text':row[text_col], 'filename':row[id_col]+'-'+header }

def audio_process_item(token, text, filename):
	conversation = re.match('^Ａ「([\s\S]+)」Ｂ「([\s\S]+)」$', text)
	if conversation != None:
		voice1 = generate_voice(token, conversation.group(1), AUDIO_VOICE[0])
		voice2 = generate_voice(token, conversation.group(2), AUDIO_VOICE[1])
		if voice1 != None and voice2 != None:
			voice = AudioSegment.from_wav(BytesIO(voice1))
			voice = voice.append(AudioSegment.from_wav(BytesIO(voice2)), 0)
			write_voice_to_file(voice, filename)
	else:
		voice = generate_voice(token, text, AUDIO_VOICE[0])
		if voice != None:
			write_voice_to_file(voice, filename)

def get_speech_token():
	headers = { 'Ocp-Apim-Subscription-Key': AZURE_KEY1 }
	response = requests.post(AZURE_TOKEN_ENDPOINT, headers=headers)
	return str(response.text)

def generate_voice(token, text, speaker):
	headers = {
		'Authorization': 'Bearer '+token,
		'Content-Type': 'application/ssml+xml',
		'X-Microsoft-OutputFormat': AUDIO_FORMAT,
		'User-Agent': 'Chrome/73.0.3683.86'
	}
	xml_body = ET.Element('speak', version='1.0')
	xml_body.set('{http://www.w3.org/XML/1998/namespace}lang', 'ja-JP')
	voice = ET.SubElement(xml_body, 'voice')
	voice.set('{http://www.w3.org/XML/1998/namespace}lang', 'ja-JP')
	voice.set('name', speaker['name'])
	prosody = ET.SubElement(voice, 'prosody')
	for key, value in speaker['prosody'].items():
		prosody.set(key, value)
	prosody.text = text
	body = ET.tostring(xml_body)
	response = requests.post(AZURE_VOICE_ENDPOINT, headers=headers, data=body)
	if response.status_code == 200:
		return response.content
	else:
		print("ERROR:"+str(response.status_code))
		print(str(response.headers))
		return None

def write_voice_to_file(voice, filename):
	if not os.path.isdir(AUDIO_FOLDER):
		os.makedirs(AUDIO_FOLDER)
	audio = voice if type(voice) == AudioSegment else AudioSegment.from_wav(BytesIO(voice))
	x,f,c,b,p = AUDIO_EXPORT_FORMAT.values()
	audio.export(AUDIO_FOLDER+filename+x, f, codec=c, bitrate=b, parameters=p)



process_spreadsheet()



### REFERENCES
# https://developer.yahoo.co.jp/webapi/jlp/furigana/v1/furigana.html
# https://www.programmersought.com/article/73392223812/
# https://ffmpeg.org/ffmpeg-codecs.html#Audio-Encoders
# https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/rest-text-to-speech
# https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/speech-synthesis-markup?tabs=csharp#adjust-prosody
# https://github.com/jiaaro/pydub/blob/master/API.markdown