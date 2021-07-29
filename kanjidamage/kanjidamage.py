# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from kanjicolorizer.colorizer import KanjiColorizer
from kanjidamage.kd import *
import csv, HTMLParser, glob, cairosvg, os, sys, re


### SETUP
fileOutput = 'output.csv'
fileOnyomi = 'onyomi.csv'
fileVocab = 'vocabulary.csv'
fileIKanji = 'imagekanji.csv'
imgDir = 'img/'
dataDir = 'data/'
baseUrl = 'http://www.kanjidamage.com'
kdItems = []
allOnyomi = []
kanjiMap = {}
kanjiString = ''
dataFiles = glob.glob(dataDir+'*.html')[:-10]
#console
consoleExtPad = '  '
consoleExtProg = '.. '
consoleTxtAnalyse = 'Scraping Data'
consoleTxtOutput = 'Writing Output'
consoleTxtImage = 'Writing Images'
consoleTxtVocab = 'Generating Word List'

### SCRAPING
print consoleExtPad+consoleTxtAnalyse+consoleExtProg,
sys.stdout.flush()
for z,filename in enumerate(dataFiles):
	### SETUP
	page = open(filename)
	soup = BeautifulSoup(page,'html.parser')
	encoding = soup.original_encoding
	kd = kdItem()
	#clean
	soup.find(class_='navbar').decompose()

	### META
	#need to figure out how to extract URL, possibly after multiple file input stage?
	if soup.find('div',class_='navigation-header').find('div',class_='span8') != None:
		meta = soup.find('div',class_='navigation-header').find('div',class_='span8')
		metaNo = ''.join(list(meta.stripped_strings)).split('\n')[-1]
		metaUrl = baseUrl+'/kanji'
		#setting
		kd.setNo(metaNo)
		kd.setUrl(metaUrl)

	### MUTANTS
	if soup.find('h2',text='Mutants') != None:
		for mutant in soup.find('h2',text='Mutants').findNext('table').findChildren('tr'):
			if len(mutant.findChildren('td')[0].findChildren('img')) > 0:
				del mutant.findChildren('td')[0].findChildren('img')[0]['alt']
				mutantItem = unicode(mutant.findChildren('td')[0].findChildren('img')[0]).encode(encoding)
			else:
				mutantItem = unicode(mutant.findChildren('td')[0].string if mutant.findChildren('td')[0].string!=None else '').encode(encoding)
			mutantName = unicode(mutant.findChildren('td')[1].string if mutant.findChildren('td')[1].string!=None else '').encode(encoding)
			#setting
			kd.addMutant(mutantItem, mutantName)

	### KANJI+NOTE
	if soup.find('h1') != None:
		kNav = soup.find('h1')
		#isRadical
		kanjiIsRad = True if meta.find('img',alt='Flag') != None else False
		#char,meaning
		for i in kNav.find('span',class_='kanji_character').findChildren('img'):
			del i['alt']
		kanjiChar = unicode(''.join([unicode(c) for c in kNav.find('span',class_='kanji_character').contents])).encode(encoding)
		kanjiMeaning = unicode(kNav.find('span',class_='translation').string).encode(encoding)
		#composition - radicalNote also found here, possibly need to separate?, also tags can be part of this string
		kNav = kNav.parent
		kNav.find('h1').decompose()
		for a in kNav.findChildren('a',class_='component'):
			a.name = 'span'
			del a['href']
		for a in kNav.findChildren('a',class_='label'):
			a['class'] = 'tag'
		kanjiComp = ''.join([unicode(x).encode(encoding) for x in kNav.contents]).replace('\n','').replace('>(','> (').replace(')<',') <')
		kanjiIsRadNote = ''
		#rating,strokes,tags
		kNav = kNav.find_next('div',class_='span4')
		kanjiRating = unicode(kNav.find('span',class_='usefulness-stars').string).encode(encoding) if kNav.find('span',class_='usefulness-stars')!=None else ''
		kanjiTags = ''
		for tag in kNav.find_all(class_='label'):
			tag['class'] = 'tag'
			tag['href'] = baseUrl+tag['href']
			kanjiTags += unicode(tag)
			tag.decompose()
		kanjiTags = kanjiTags.encode(encoding)
		kanjiStrCount = unicode(kNav.findChildren('div')[0].string.split(' ')[0]).encode(encoding) if kNav.findChildren('div')[0].string!=None else ''
		#note
		itemNote = ''
		if kNav.find_next('div',class_='description') != None:
			kNav = kNav.find_next('div',class_='description')
			itemNote = ''.join([unicode(x).encode(encoding) for x in kNav.contents]).replace('\n','') if kNav.contents != None else ''
		#mnemonic
		if kNav.find_next('h2',text='Mnemonic')!=None:
			kNav = kNav.find_next('h2',text='Mnemonic').find_next('table').findChildren('tr')[0].findChildren('td')[1]
			kanjiMnemonic = ''.join([unicode(x).encode(encoding) for x in kNav.contents]).replace('\n','')
		else:
			kanjiMnemonic = ''
		#setting
		kd.setKanji(kanjiChar, kanjiMeaning, kanjiMnemonic, kanjiComp, kanjiRating, kanjiTags, kanjiStrCount, metaNo, kanjiIsRad, kanjiIsRadNote)
		kd.setNote(itemNote)
		if len(wordToKanjiOnly(kanjiChar.decode(encoding)))>0:
			kanjiMap[kanjiChar.decode(encoding)] = int(metaNo)
			kanjiString += kanjiChar.decode(encoding)

	### ONYOMI
	if soup.find('h2',text='Onyomi') != None:
		onyomi = soup.find('h2',text='Onyomi').findNext('table').find('tr').findChildren('td')
		onyomiSound = unicode(''.join(onyomi[0].stripped_strings) if onyomi[0].stripped_strings!=None else '').encode(encoding).replace('\n','')
		onyomiMnemonic = unicode(''.join(unicode(c) for c in onyomi[1].contents) if onyomi[1].contents!=None else '').encode(encoding).replace('\n','')
		#setting
		kd.setOnyomi(onyomiSound, '', onyomiMnemonic)
		allOnyomi.extend(processOnyomiForOutput(onyomiSound))

	### KUNYOMI
	if soup.find('h2',text='Kunyomi') != None:
		for kunyomi in soup.find('h2',text='Kunyomi').findNext('table').findChildren('tr'):
			#prefix,word,suffix
			#are there cases of infixes or multiple kanji_character spans?
			pwsList = kunyomi.findChildren('td')[0].find_all('span')
			prefix = ''
			word = ''
			suffix = ''
			for pws in pwsList:
				if pws['class'] == [u'particles']:
					#are there cases where furigana handling is needed for pre/suf?
					if word=='':
						prefix = unicode(pws.string).encode(encoding)
					else:
						suffix = unicode(pws.string).encode(encoding)
				elif pws['class']==[u'kanji_character']:
					word += unicode(''.join(pws.stripped_strings))
			word = unicode(word).encode(encoding).replace('＊','*').split('*')
			word[0] = kanjiChar+'['+word[0]+']'
			word = ''.join(word)
			#rating
			rating = unicode(kunyomi.find(class_='usefulness-stars').string).encode(encoding)
			#tags
			tags = ''
			tagList = kunyomi.find_all(class_='label')
			for tag in tagList:
				tag['class'] = 'tag'
				tag['href'] = baseUrl+tag['href']
				tags += unicode(tag)
			tags = tags.encode(encoding).replace('\n','')
			#description
			#some unneccessary p nonsense (see 0024:mune), need to clean up
			[x.decompose() for x in kunyomi.findChildren('td')[1].find_all(class_='tag')]
			[x.decompose() for x in kunyomi.findChildren('td')[1].find_all(class_='usefulness-stars')]
			description = ''.join(unicode(x) for x in kunyomi.findChildren('td')[1].children).encode(encoding).replace('\n','').replace('<br></br>','') if kunyomi.findChildren('td')[1].children!=None else ''
			#print str(description)
			#setting
			kd.addKunyomi(word,rating,prefix,suffix,description,tags)

	### JUKUGO
	if soup.find('h2',text='Jukugo') != None:
		for jukugo in soup.find('h2',text='Jukugo').findNext('table').findChildren('tr'):
			#prefix,word,suffix
			#are there cases of infixes or multiple kanji_character spans?
			pwsList = jukugo.findChildren('td')[0].find_all('span')
			prefix = ''
			word = ''
			suffix = ''
			for pws in pwsList:
				if pws['class'] == [u'particles']:
					#are there cases where furigana handling is needed for pre/suf?
					if word=='':
						prefix = unicode(pws.string).encode(encoding)
					else:
						suffix = unicode(pws.string).encode(encoding)
				elif pws['class']==[u'kanji_character']:
					word += unicode(''.join(pws.stripped_strings))
			word = unicode(word).encode(encoding).replace('(','[').replace(')',']')
			#meaning
			meaning = jukugo.findChildren('td')[1].findNext('p').stripped_strings
			meaning = unicode(next(meaning)).encode(encoding)
			#rating
			rating = unicode(jukugo.find(class_='usefulness-stars').string).encode(encoding)
			#tags
			tags = ''
			tagList = jukugo.find_all(class_='label')
			for tag in tagList:
				tag['class'] = 'tag'
				tag['href'] = baseUrl+tag['href']
				tags += unicode(tag)
			tags = tags.encode(encoding).replace('\n','')
			#composition
			composition = jukugo.findChildren('td')[1].findNext('p').findNext('br')
			if composition!=None:
				for tag in composition.findChildren('a'):
					tag.name = 'span'
					#tag['class'] = 'component' #breaks consistency with website (see 0001:ordinary)
					del tag['href']
				composition = composition.encode(encoding).replace('\n','').replace('<br>','').replace('</br>','')
			else:
				composition = ''
			#description
			#some unneccessary p nesting (see 0007:looks), need to clean up
			description = ''
			descList = jukugo.findChildren('td')[1].find_all('p')[1:]
			for desc in descList:
				description += unicode(desc)
			description = description.encode(encoding).replace('\n','').replace('<p>','').replace('</p>','') # there a better way to deal with p tags?
			#setting
			kd.addJukugo(word, rating, meaning, prefix, suffix, description, composition, tags)

	### LOOKALIKES
	#the fuck is this shit fuck you
	#if soup.find('h2',text='Lookalikes') != None:
	#	for lookalike in soup.find('h2',text='Lookalikes').findNext('table').findChildren('tr')[1:]:
	#		lookalikeItems = lookalike.findChildren('td')
	#		#kanji+kanjiurl
	#		kanjiItem = lookalikeItems[0].findChildren('a')[0]
	#		kanjiUrl = baseUrl+kanjiItem['href'] if kanjiItem.string!=None else ''
	#		if len(kanjiItem.findChildren('img')) > 0:
	#			del kanjiItem.findChildren('img')[0]['alt']
	#			kanji = unicode(kanjiItem.findChildren('img')[0]).encode(encoding)
	#		else:
	#			kanji = unicode(kanjiItem.string if kanjiItem.string!=None else '').encode(encoding)
	#		#meaning
	#		meaning = unicode(lookalikeItems[1].string if lookalikeItems[1].string!=None else '').encode(encoding)
	#		#hint
	#		hint = unicode(lookalikeItems[2].string if lookalikeItems[2].string!=None else '').encode(encoding)
	#		#radical+radicalurl
	#		radicalItem = lookalikeItems[3].findChildren('a')[0]
	#		radicalUrl = baseUrl+radicalItem['href'] if radicalItem.string!=None else ''
	#		if len(radicalItem.findChildren('img')) > 0:
	#			del radicalItem.findChildren('img')[0]['alt']
	#			radical = unicode(radicalItem.findChildren('img')[0]).encode(encoding)
	#		else:
	#			radical = unicode(radicalItem.string if radicalItem.string!=None else '').encode(encoding)
	#		#setting
	#		kd.addLookalike(kanji, kanjiUrl, meaning, hint, radical, radicalUrl)
	#	mnemonicList = list(soup.find(text='Lookalikes').findNext('table').next_siblings)
	#	mnemonicListMax = -1
	#	for mnemonicItem in mnemonicList:
	#		if mnemonicItem.name in {'h2','table','ul',None}:
	#			break
	#		else:
	#			mnemonicListMax += 1

	### USED IN
	if soup.find('h2',text='Used In') != None:
		for usedIn in soup.find('h2',text='Used In').findNext('ul').findChildren('li'):
			if len(usedIn.findChildren('img')) > 0:
				del usedIn.findChildren('img')[0]['alt']
			usedIn.findChildren('a')[0]['href'] = baseUrl+usedIn.findChildren('a')[0]['href']
			usedIn = unicode(usedIn.findChildren('a')[0]).encode(encoding)
			kd.setUsedIn(usedIn, True)

	### SYNONYMS
	if soup.find('h2',text='Synonyms') != None:
		for synonym in soup.find('h2',text='Synonyms').findNext('table').findChildren('tr'):
			#synonym,url
			syn = synonym.findNext('a').string.encode(encoding)
			url = baseUrl+synonym.findNext('a')['href'].encode(encoding)
			#words
			words = list(synonym.findNext('td').findNext('br').stripped_strings)[0].encode(encoding).replace('\n\xc2\xa0\xc2\xa0','').replace(' ','').replace('　','').split('\n')
			#setting
			kd.addSynonym(syn, words, url)

	### CLEANUP
	kdItems.append(kd)
	del kd
	### CONSOLE
	print '\r'+consoleExtPad+consoleTxtAnalyse+consoleExtProg+'No.'+str(metaNo),
	sys.stdout.flush()
	#print consoleBase+consoleNext


### OUTPUT
if len(kdItems):
	csvOutput = csv.writer(open(fileOutput,'wb'))
	print '\n'+consoleExtPad+consoleTxtOutput+consoleExtProg,
	sys.stdout.flush()
	csvOutput.writerow(kdItems[0].getHeaders())
	kStr = u''
	kFileMap = []
	# Write Output CSV
	for z,kd in enumerate(kdItems):
		print '\r'+consoleExtPad+consoleTxtOutput+consoleExtProg+'No.'+str(kd.no),
		sys.stdout.flush()
		csvOutput.writerow(kd.getData())
		if len(kd.kanji.kanji)<5 and kd.kanji.kanji!='<<<' and kd.kanji.kanji!='L' and kd.kanji.kanji!='￥':
			kStr += kd.kanji.kanji.decode(encoding) if len(kd.kanji.kanji)<5 else u''
			kFileMap.append([''.join(hex(ord(kd.kanji.kanji.decode(encoding)))[2:]).zfill(5)+'.svg',kd.kanji.strOrder.replace('.png','.svg'),kd.kanji.strOrder])
	# Process Onyomi
	csvOnyomi = csv.writer(open(fileOnyomi,'wb'))
	allOnyomi = sorted(list(set(allOnyomi)),key=len,reverse=True) # remove duplicates by converting to a set and back, then sort
	for z,on in enumerate(allOnyomi):
		csvOnyomi.writerow([on])
	# Generate Images
	print '\n'+consoleExtPad+consoleTxtImage+consoleExtProg,
	sys.stdout.flush()
	kc = KanjiColorizer('--mode contrast --image-size 256 --characters '+kStr+' --filename-mode code --output-directory img') # consider adding --group-mode
	kc.write_all()
	for z,f in enumerate(kFileMap):
		print '\r'+consoleExtPad+consoleTxtImage+consoleExtProg+f[2],
		sys.stdout.flush()
		cairosvg.svg2png(url=imgDir+f[0],write_to=imgDir+f[2])
		os.remove(imgDir+f[1]) if os.path.isfile(imgDir+f[1]) else False
		os.rename(imgDir+f[0],imgDir+f[1])
	# Output Words
	csvVocab = csv.writer(open(fileVocab,'wb'))
	print '\n'+consoleExtPad+consoleTxtVocab+consoleExtProg,
	sys.stdout.flush()
	wordList = []
	for z,w in enumerate(kdItems[0].lastKunyomi.catalogue):
		print '\r'+consoleExtPad+consoleTxtVocab+consoleExtProg+str(z+1)+'/'+str(len(kdItems[0].lastKunyomi.catalogue)+len(kdItems[0].lastJukugo.catalogue)),
		sys.stdout.flush()
		w = w.getData()
		if str(w[0]) not in wordList:
			wordList.append(str(w[0]))
			csvVocab.writerow(['K'+str(z+1).zfill(4),getMinKanji(kanjiMap,kanjiString,w[0].decode(encoding)),wordDelFurigana(w[0]),w[0], w[1], w[2], '', '', w[3]])
	for z,w in enumerate(kdItems[0].lastJukugo.catalogue):
		print '\r'+consoleExtPad+consoleTxtVocab+consoleExtProg+str(z+1+len(kdItems[0].lastKunyomi.catalogue))+'/'+str(len(kdItems[0].lastKunyomi.catalogue)+len(kdItems[0].lastJukugo.catalogue)),
		sys.stdout.flush()
		w = w.getData()
		if str(w[0]) not in wordList:
			wordList.append(str(w[0]))
			csvVocab.writerow(['J'+str(z+1).zfill(4),getMinKanji(kanjiMap,kanjiString,w[0].decode(encoding)),wordDelFurigana(w[0])]+w[:-4])
	print '\n'+consoleExtPad+'DONE'