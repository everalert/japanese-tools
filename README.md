# Japanese Tools

Collection of scripts related to Japanese study. Not all are up-to-date and may need some tweaking.

### `/sentenceprocessor`
Generates TTS audio files and Anki-formatted Furigana from ODS spreadsheets.
* Requires [Azure Cognitive Services](https://azure.microsoft.com/en-us/services/cognitive-services/) Speech API and [Yahoo! Japan](https://developer.yahoo.co.jp/webapi/jlp/furigana/v1/furigana.html) API keys.
* Place keys in `spkeys.py` (see `sentenceprocessor.py` for variable names)

### `/yojijukugo`
[四字熟語辞典ONLINE](https://yoji.jitenon.jp/) idiom scraper.

### `/kanjidamage`
[KanjiDamage](http://www.kanjidamage.com/) (RTK-like study website) scraper and kanji diagram generator.
* Requires `/kanjicolorizer` folder from [KanjiColorizer](https://github.com/cayennes/kanji-colorize) in main directory.
* May also need to extract [KanjiVG](https://github.com/KanjiVG/kanjivg/releases) data to `/kanjicolorizer/data/kanjivg`

### `/anki_datetime`
[Anki](https://apps.ankiweb.net/) addon that lets you insert the current datetime into an editor field from the context menu.
* Intended for quickly filling an ID-style sort field with something unique.

### `/anki_furigana`
[Anki](https://apps.ankiweb.net/) addon that generates furigana for a single editor field.
* Requires [Yahoo! Japan](https://developer.yahoo.co.jp/webapi/jlp/furigana/v1/furigana.html) API key.
* Accessible from the context menu.
* Replaces field with the API output; cannot be undone.