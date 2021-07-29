# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
import re


### GENERAL HELPERS

def containsAny(str, set):
    """Check whether 'str' contains ANY of the chars in 'set'"""
    return 1 in [c in str for c in set]

def containsAll(str, set):
    """Check whether 'str' contains ALL of the chars in 'set'"""
    return 0 not in [c in str for c in set]

def wordToKanjiOnly(word):
	return re.sub(ur'([^\u4E00-\u9FFF]+)','',word)

def wordDelFurigana(word):
	return re.sub(r'\[(.*?)\]','',word)

def getMinKanji(kMap,kanji,word):
	"""Return KanjiDamage ID of minimum knowledge to cover all Kanji in a word"""
	i = 0
	while i<(len(kanji)-1) and not containsAll(''.join(kanji[:(i+1)]),set(wordToKanjiOnly(word))):
		i += 1
	return kMap[kanji[i]] if containsAll(''.join(kanji),set(wordToKanjiOnly(word))) else 9999
	#return i

def processOnyomiForOutput(onyomi=''):
	# For output collection of Onyomi for processing
	# possible delimiters (after deleting spaces): , / 'or' . - 'also' 
	rChr = ','
	output = onyomi.replace(' ','')
	output = output.replace('also',rChr)
	output = output.replace('or',rChr)
	output = output.replace('-',rChr)
	output = output.replace('.',rChr)
	output = output.replace(',',rChr)
	output = output.replace('/',rChr)
	return output.split(rChr)



### KANJIDAMAGE CLASSES

class kdItem(object):
	"""docstring for kdItem"""

	catalogue = []
	mostMutants = 0
	lastMutant = None
	mostKunyomi = 0
	lastKunyomi = None
	mostJukugo = 0
	lastJukugo = None
	mostSynonyms = 0
	lastSynonym = None
	mostLookalikes = 0
	lastLookalike = None
	defaultMultiplier = 3

	def __init__(self, catalogue=catalogue):
		self.kanji = kdKanji(parent=self)
		self.data = []
		self.headers = []
		catalogue.append(self)
		#collections
		self.mutants = []
		self.kunyomi = []
		self.jukugo = []
		self.lookalikes = []
		self.synonyms = []
		#meta
		self.id = ''
		self.no = 0
		self.url = ''
		#data
		self.onyomi = ''
		self.onyomiKana = ''
		self.onyomiMnemonic = ''
		self.lookalikeMnemonic = ''
		self.usedIn = ''
		self.note = ''
		#misc
		self.codeJIS = '' # Shift JIS
		self.codeUTF = ''
		self.codeRTK = '' # Remembering the Kanji
		self.codeSKIP = '' # System of Kanji Indexing by Patterns
		self.codeFC = '' # Four-Corner System
		self.codeRad = '' # Radical

	# Meta

	def setNo(self, no=0):
		if no>0:
			self.no = no
			self.id = 'KD-'+str(no).zfill(4)
		else:
			self.no = 0
			self.id = ''

	def setUrl(self, url=''):
		self.url = url

	# Mutants

	def addMutant(self, mutant, name, url=''):
		newMutant = kdMutant(mutant, name, self)
		newMutant.setUrl(url)
		self.mutants.append(newMutant)
		kdItem.mostMutants = max(kdItem.mostMutants,self.countMutants())
		kdItem.lastMutant = newMutant
		del newMutant

	def countMutants(self):
		return len(self.mutants)

	def calcMostMutants(self, catalogue=catalogue):
		kdItem.mostMutants = 0
		for item in catalogue:
			kdItem.mostMutants = max(kdItem.mostMutants,item.countMutants())
		return kdItem.mostMutants

	# Kanji

	def setKanji(self, kanji='', meaning='', mnemonic='', comp='', rating='', tags='', strCount=0, strOrder=0, isRad='', isRadNote=''):
		self.kanji.setKanji(kanji)
		self.kanji.setMeaning(meaning)
		self.kanji.setMnemonic(mnemonic)
		self.kanji.setComposition(comp)
		self.kanji.setRating(rating)
		self.kanji.setTags(tags)
		self.kanji.setStrCount(strCount)
		self.kanji.setStrOrder(strOrder)
		self.kanji.setRadical(isRad, isRadNote)

	def getKanjiData(self):
		return self.kanji.getData()

	def getKanjiHeaders(self):
		return self.kanji.getHeaders()

	# Onyomi

	def setOnyomi(self, onyomi='', kana='', mnemonic=''):
		self.onyomi = onyomi
		self.onyomiKana = kana
		self.onyomiMnemonic = mnemonic

	def getOnyomiData(self):
		return [self.onyomi, self.onyomiKana, self.onyomiMnemonic, 1 if self.onyomi!='' else 0]

	def getOnyomiHeaders(self):
		return ['onyomi', 'onyomi-kana', 'onyomi-mnemonic','onyomi-exists']

	def getDummyOnyomi(self):
		return ['', '', '', 0]

	# Kunyomi

	def addKunyomi(self, word, rating, pre, suf, desc, tags):
		newKunyomi = kdKunyomi(word, rating, self)
		newKunyomi.setPrefix(pre)
		newKunyomi.setSuffix(suf)
		newKunyomi.setDescription(desc)
		newKunyomi.setTags(tags)
		self.kunyomi.append(newKunyomi)
		kdItem.mostKunyomi = max(kdItem.mostKunyomi,self.countKunyomi())
		kdItem.lastKunyomi = newKunyomi
		del newKunyomi

	def countKunyomi(self):
		return len(self.kunyomi)

	def calcMostKunyomi(self, catalogue=catalogue):
		kdItem.mostKunyomi = 0
		for item in catalogue:
			kdItem.mostKunyomi = max(kdItem.mostKunyomi,item.countKunyomi())
		return kdItem.mostKunyomi

	def getKunyomiList(self):
		return ''.join('<span>{0}</span>'.format(k.word) for k in self.kunyomi)

	# Jukugo

	def addJukugo(self, word, rating, meaning, pre, suf, desc, comp, tags):
		newJukugo = kdJukugo(word, rating, self)
		newJukugo.setMeaning(meaning)
		newJukugo.setPrefix(pre)
		newJukugo.setSuffix(suf)
		newJukugo.setDescription(desc)
		newJukugo.setComposition(comp)
		newJukugo.setTags(tags)
		self.jukugo.append(newJukugo)
		kdItem.mostJukugo = max(kdItem.mostJukugo,self.countJukugo())
		kdItem.lastJukugo = newJukugo
		del newJukugo

	def countJukugo(self):
		return len(self.jukugo)

	def calcMostJukugo(self, mostJukugo=mostJukugo, catalogue=catalogue):
		kdItem.mostJukugo = 0
		for item in catalogue:
			kdItem.mostJukugo = max(kdItem.mostJukugo,item.countJukugo())
		return kdItem.mostJukugo

	def getJukugoList(self):
		return ''.join('<span>{0}</span>'.format(j.word) for j in self.jukugo)

	# Used In

	def setUsedIn(self, usedIn='', add=False):
		if add:
			self.usedIn += usedIn
		else:
			self.usedIn = usedIn

	# Lookalikes

	def addLookalike(self, kanji='', kanjiUrl='', meaning='', hint='', radical='', radicalUrl=''):
		newLookalike = kdLookalike(kanji, kanjiUrl, meaning, hint, self)
		newLookalike.setRadical(radical)
		newLookalike.setRadicalUrl(radicalUrl)
		self.lookalikes.append(newLookalike)
		kdItem.mostLookalikes = max(kdItem.mostLookalikes,self.countLookalikes())
		kdItem.lastLookalike = newLookalike
		del newLookalike

	def setLookalikeMnmemonic(self, mnemonic=''):
		self.lookalikeMnemonic = mnemonic

	def countLookalikes(self):
		return len(self.lookalikes)

	def calcMostLookalikes(self, catalogue=catalogue):
		kdItem.mostLookalikes = 0
		for item in catalogue:
			kdItem.mostLookalikes = max(kdItem.mostLookalikes,item.countLookalikes())
		return kdItem.mostLookalikes

	# Synonyms

	def addSynonym(self, synonym, words, url):
		newSynonym = kdSynonym(synonym, words, self)
		newSynonym.setUrl(url)
		self.synonyms.append(newSynonym)
		kdItem.mostSynonyms = max(kdItem.mostSynonyms,self.countSynonyms())
		kdItem.lastSynonym = newSynonym
		del newSynonym

	def countSynonyms(self):
		return len(self.synonyms)

	def calcMostSynonyms(self, catalogue=catalogue):
		kdItem.mostSynonyms = 0
		for item in catalogue:
			kdItem.mostSynonyms = max(kdItem.mostSynonyms,item.countSynonyms())
		return kdItem.mostSynonyms

	def setNote(self, arg=''):
		self.note = arg

	# Output
	# meta -> kanji -> onyomi -> kunyomi -> jukugo -> note -> mutants -> usedin -> synonyms (-> lookalikes -> codes)

	def getData(self, m=defaultMultiplier):
		self.data = []
		self.outMosts = self.getMosts()
		self.outLasts = self.getLasts()
		self.data.extend([self.id, self.no, self.url]) # meta
		self.data.extend(self.getKanjiData()) # kanji
		self.data.extend(self.getOnyomiData()) # onyomi
		if self.outMosts['kunyomi']>0: # kunyomi
			self.outMultKunyomi = self.outMosts['kunyomi']+(m-self.outMosts['kunyomi']%m) if self.outMosts['kunyomi']%m else self.outMosts['kunyomi']
			for k in self.kunyomi:
				self.data.extend(k.getData())
			self.data.extend(self.outLasts['kunyomi'].getDummyData()*(self.outMultKunyomi-self.countKunyomi()))
			self.data.extend([self.getKunyomiList(), 1 if self.getKunyomiList()!='' else 0])
		if self.outMosts['jukugo']>0: # jukugo
			self.outMultJukugo = self.outMosts['jukugo']+(m-self.outMosts['jukugo']%m) if self.outMosts['jukugo']%m else self.outMosts['jukugo']
			for j in self.jukugo:
				self.data.extend(j.getData())
			self.data.extend(self.outLasts['jukugo'].getDummyData()*(self.outMultJukugo-self.countJukugo()))
			self.data.extend([self.getJukugoList(), 1 if self.getJukugoList()!='' else 0])
		self.data.extend([self.note, 1 if self.note!='' else 0]) # note
		if self.outMosts['mutants']>0: # mutants
			self.outMultMutants = self.outMosts['mutants']+(m-self.outMosts['mutants']%m) if self.outMosts['mutants']%m else self.outMosts['mutants']
			for mut in self.mutants:
				self.data.extend(mut.getData())
			self.data.extend(self.outLasts['mutant'].getDummyData()*(self.outMultMutants-self.countMutants()))
		self.data.extend([self.usedIn]) # used in
		if self.outMosts['synonyms']>0: # synonyms
			self.outMultSynonyms = self.outMosts['synonyms']+(m-self.outMosts['synonyms']%m) if self.outMosts['synonyms']%m else self.outMosts['synonyms']
			for s in self.synonyms:
				self.data.extend(s.getData())
			self.data.extend(self.outLasts['synonym'].getDummyData()*(self.outMultSynonyms-self.countSynonyms()))
		return self.data

	def getHeaders(self, m=defaultMultiplier):
		self.headers = []
		self.outMosts = self.getMosts()
		self.outLasts = self.getLasts()
		self.headers.extend(['id', 'no', 'url']) # meta
		self.headers.extend(self.getKanjiHeaders()) # kanji
		self.headers.extend(self.getOnyomiHeaders()) # onyomi
		if self.outMosts['kunyomi']>0: # kunyomi
			self.outMultKunyomi = self.outMosts['kunyomi']+(m-self.outMosts['kunyomi']%m) if self.outMosts['kunyomi']%m else self.outMosts['kunyomi']
			kunyomiHeaders = self.outLasts['kunyomi'].getHeaders()
			self.headers.extend([e.replace('kunyomi','kunyomi'+str(i/len(kunyomiHeaders)+1).zfill(2)) for i,e in enumerate(kunyomiHeaders*self.outMultKunyomi)]+['kunyomi-shortlist','kunyomi-anyexist'])
		if self.outMosts['jukugo']>0: # jukugo
			self.outMultJukugo = self.outMosts['jukugo']+(m-self.outMosts['jukugo']%m) if self.outMosts['jukugo']%m else self.outMosts['jukugo']
			jukugoHeaders = self.outLasts['jukugo'].getHeaders()
			self.headers.extend([e.replace('jukugo','jukugo'+str(i/len(jukugoHeaders)+1).zfill(2)) for i,e in enumerate(jukugoHeaders*self.outMultJukugo)]+['jukugo-shortlist','jukugo-anyexist'])
		self.headers.extend(['note','note-exists']) # note
		if self.outMosts['mutants']>0: # mutants
			self.outMultMutants = self.outMosts['mutants']+(m-self.outMosts['mutants']%m) if self.outMosts['mutants']%m else self.outMosts['mutants']
			headersMutants = self.outLasts['mutant'].getHeaders()
			self.headers.extend([e.replace('mutant','mutant'+str(i/len(headersMutants)+1).zfill(2)) for i,e in enumerate(headersMutants*self.outMultMutants)])
		self.headers.extend(['usedin']) # used in
		if self.outMosts['synonyms']>0: # synonyms
			self.outMultSynonyms = self.outMosts['synonyms']+(m-self.outMosts['synonyms']%m) if self.outMosts['synonyms']%m else self.outMosts['synonyms']
			synonymHeaders = self.outLasts['synonym'].getHeaders()
			self.headers.extend([e.replace('synonym','synonym'+str(i/len(synonymHeaders)+1).zfill(2)) for i,e in enumerate(synonymHeaders*self.outMultSynonyms)])
		return self.headers

	def getCatalogue(self, catalogue=catalogue):
		return catalogue

	def getMosts(self):
		return {'mutants': self.calcMostMutants(), 'kunyomi': self.calcMostKunyomi(), 'jukugo': self.calcMostJukugo(), 'synonyms': self.calcMostSynonyms(), 'lookalikes': self.calcMostLookalikes()}

	def getLasts(self):
		return {'mutant': kdItem.lastMutant, 'kunyomi': kdItem.lastKunyomi, 'jukugo': kdItem.lastJukugo, 'synonym': kdItem.lastSynonym, 'lookalike': kdItem.lastLookalike}




class kdMutant(object):
	"""docstring for kdMutant"""

	catalogue = []

	def __init__(self, mutant='', name='', parent=None, catalogue=catalogue):
		self.mutant = mutant
		self.name = name
		self.parent = parent
		catalogue.append(self)
		self.url = ''

	def setMutant(self, mutant=''):
		self.mutant = mutant

	def setName(self, name=''):
		self.name = name

	def setUrl(self, url=''): # not sure if used on website?
		self.url = url

	def getHeaders(self):
		return ['mutant', 'mutant-name', 'mutant-exists']

	def getData(self):
		return [self.mutant, self.name, 1]

	def getDummyData(self):
		return ['', '', 0]


		

class kdKanji(object):
	"""docstring for kdKanji"""
	
	catalogue = []

	def __init__(self, kanji='', meaning='', mnemonic='', parent=None, catalogue=catalogue):
		self.kanji = kanji
		self.meaning = meaning
		self.mnemonic = mnemonic
		self.parent = parent
		catalogue.append(self)
		self.comp = ''
		self.rating = ''
		self.tags = ''
		self.strCount = 0
		self.strOrder = ''
		self.isRad = False 
		self.isRadNote = ''

	def setKanji(self, arg=''):
		self.kanji = arg

	def setMeaning(self, arg=''):
		self.meaning = arg

	def setMnemonic(self, arg=''):
		self.mnemonic = arg

	def setComposition(self, arg=''):
		self.comp = arg

	def setRating(self, arg=''):
		self.rating = arg

	def setTags(self, arg=''):
		self.tags = arg

	def setStrCount(self, arg=0):
		self.strCount = arg

	def setStrOrder(self, arg=0):
		if len(self.kanji)<5 and len(self.kanji)>0 and self.kanji!='<<<' and self.kanji!='L' and self.kanji!='￥':
			self.strOrder = 'kanjidamage-'+str(arg).zfill(4)+'-stroke.png'
		else:
			self.strOrder = ''

	def setRadical(self, radical=False, note=''):
		self.isRad = 1 if radical==True else 0
		self.isRadNote = note

	def getHeaders(self):
		return ['kanji', 'kanji-meaning', 'kanji-mnemonic', 'kanji-mnemonic-exists', 'kanji-composition', 'kanji-rating', 'kanji-tags', 'kanji-stroke-count', 'kanji-stroke-order', 'kanji-isradical', 'kanji-isradical-note']

	def getData(self):
		return [self.kanji, self.meaning, self.mnemonic, 1 if len(self.mnemonic)>0 else 0, self.comp, self.rating, self.tags, self.strCount, self.strOrder, self.isRad, self.isRadNote]

	def getDummyData(self):
		return ['', '', '', 0, '', '', '', '', '', '', '']




class kdWord(object):
	"""docstring for kdWord"""

	__metaclass__ = ABCMeta

	def __init__(self, word='UNDEFINED', rating='☆☆☆☆☆', parent=None):
		self.word = word
		self.rating = rating
		self.parent = parent
		self.appendCatalogue()
		self.meaning = ''
		self.pre = ''
		self.suf = ''
		self.desc = ''
		self.comp = ''
		self.tags = ''

	def setWord(self, word='UNDEFINED'):
		self.word = word

	def setMeaning(self, meaning=''):
		self.meaning = meaning

	def setRating(self, rating='UNDEFINED'):
		self.rating = rating

	def setPrefix(self, prefix='☆☆☆☆☆'):
		self.pre = prefix

	def setSuffix(self, suffix=''):
		self.suf = suffix

	def setDescription(self, desc=''):
		self.desc = desc

	def setComposition(self, comp=''):
		self.comp = comp

	def setTags(self, tags=''):
		self.tags = tags

	@abstractmethod
	def appendCatalogue(self):
		pass

	@abstractmethod
	def getHeaders(self):
		pass

	@abstractmethod
	def getData(self):
		pass

	@abstractmethod
	def getDummyData(self):
		pass


class kdKunyomi(kdWord):
	"""docstring for kdKunyomi"""

	catalogue = []

	def appendCatalogue(self):
		kdKunyomi.catalogue.append(self)

	def getHeaders(self):
		return ['kunyomi', 'kunyomi-pre', 'kunyomi-suf', 'kunyomi-desc', 'kunyomi-rating', 'kunyomi-tags', 'kunyomi-exists']

	def getData(self):
		return [self.word, self.pre, self.suf, self.desc, self.rating, self.tags, 1]

	def getDummyData(self):
		return ['', '', '', '', '', '', 0]


class kdJukugo(kdWord):
	"""docstring for kdJukugo"""

	catalogue = []

	def appendCatalogue(self):
		kdJukugo.catalogue.append(self)

	def getHeaders(self):
		return ['jukugo', 'jukugo-pre', 'jukugo-suf', 'jukugo-meaning', 'jukugo-comp', 'jukugo-desc', 'jukugo-rating', 'jukugo-tags', 'jukugo-exists']

	def getData(self):
		return [self.word, self.pre, self.suf, self.meaning, self.comp, self.desc, self.rating, self.tags, 1]

	def getDummyData(self):
		return ['', '', '', '', '', '', '', '', 0]




class kdLookalike(object):
	"""docstring for kdLookalike"""

	catalogue = []

	def __init__(self, kanji='', kanjiUrl='', meaning='', hint='', parent=None, catalogue=catalogue):
		self.kanji = kanji
		self.kanjiUrl = kanjiUrl
		self.meaning = meaning
		self.hint = hint
		self.parent = parent
		catalogue.append(self)
		self.radical = ''
		self.radicalUrl = ''

	def setKanji(self, arg=''):
		self.kanji = arg

	def setKanjiUrl(self, arg=''):
		self.kanjiUrl = arg

	def setRadical(self, arg=''):
		self.radical = arg

	def setRadicalUrl(self, arg=''):
		self.radicalUrl = arg

	def setMeaning(self, arg=''):
		self.meaning = arg

	def setHint(self, arg=''):
		self.hint = arg

	def getHeaders(self):
		return ['lookalike-kanji', 'lookalike-kanji-url', 'lookalike-meaning', 'lookalike-hint', 'lookalike-radical', 'lookalike-radical-url']

	def getData(self):
		return [self.kanji, self.kanjiUrl, self.meaning, self.hint, self.radical, self.radicalUrl]

	def getDummyData(self):
		return ['', '', '', '', '', '']
		
		




class kdSynonym(object):
	"""docstring for kdSynonym"""

	catalogue = []

	def __init__(self, synonym='UNDEFINED', words=[], parent=None, catalogue=catalogue):
		self.synonym = synonym
		self.words = words
		self.parent = parent
		catalogue.append(self)
		self.url = ''

	def setSynonym(self, synonym=''):
		self.synonym = synonym

	def setUrl(self, url=''):
		self.url = url

	def setWords(self, words=[]):
		self.words = words

	def addWord(self, word=''):
		self.words.append(word)

	def getHeaders(self):
		return['synonym', 'synonym-words', 'synonym-url', 'synonym-exists']

	def getData(self):
		return [self.synonym, ''.join('<span>{0}</span>'.format(w) for w in self.words), self.url, 1]

	def getDummyData(self):
		return['', '', '', 0]