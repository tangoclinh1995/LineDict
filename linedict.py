import urllib.request
import urllib.parse
import json
import re
import sqlite3



MAX_EXAMPLE_DOWNLOADED = 50
SPAN_TAG_OPEN_REGEX = "<span class=\"autolink\" data-query=\"[\%\d\w]+\">"
CHINESE_WORD_FILTER_REGEX = "<a>(<b>)?(.+?)(<\/b>)?<\/a>"



def DownloadUsageExample(word, discoveryMode = False):
	url = "http://linedict.naver.com/cnen/example/search.dict"

	requestData = urllib.parse.urlencode({
		"callback": "jQuery1_1",
		"query": word,
		"page_size": MAX_EXAMPLE_DOWNLOADED,
		"page": 1,
		"_": 1,
		"format": "json"
		})

	response = urllib.request.urlopen(url, requestData.encode("utf-8"))
	dataJson = json.loads(response.read().decode("utf-8")[10:-1:])
	examples = dataJson["exampleList"]

	result = []

	for e in examples:
		entry = {}

		entry["id"] = e["exampleId"]
		entry["example"] = e["example"]
		entry["difficulty"] = int(e["degreeType"])

		entry["translation"] = e["translation"].replace("</span>", "").replace("</strong>","").replace("<strong class=\"colg\">", "")
		entry["translation"] = re.sub(SPAN_TAG_OPEN_REGEX, "", entry["translation"])

		entry["pinyin"] = e["pinyin"].replace("<strong class=\"colg\">", "<b>").replace("</strong>", "</b>")

		entry["separation"] = e["exampleAutolink"].replace("</span>", "</a>").replace("</strong>","</b>").replace("<strong class=\"colg\">", "<b>")
		entry["separation"] = re.sub(SPAN_TAG_OPEN_REGEX, "<a>", entry["separation"])

		result.append(entry)

	if discoveryMode:
		newWords = {}

		for r in result:
			detail = r["separation"]

			for m in re.finditer(CHINESE_WORD_FILTER_REGEX, detail):
				if m.group(2) in newWords:
					newWords[m.group(2)] += 1
				else:
					newWords[m.group(2)] = 1

		return result, newWords
	else:
		return result


def SaveDataToDatabase(word, content):
	def paramGenerator():
		for x in content:
			yield (x["id"], x["example"], x["translation"], x["pinyin"], x["separation"], x["difficulty"])


	conn = sqlite3.connect("linedict.db")
	cur = conn.cursor()

	strExampleIdList = ""
	for e in content:
		strExampleIdList += e["id"] + "\n"

	cur.execute("INSERT OR IGNORE INTO words (word, examples) VALUES(?,?)", (word, strExampleIdList))
	cur.executemany("INSERT OR IGNORE INTO examples (id,example,translation,pinyin,separation,difficulty) VALUES(?,?,?,?,?,?)", paramGenerator())

	conn.commit()
	conn.close()


def ShowDataConsole(word, content):
    print()
    print("==========")
    
    for e in content:
        print(e["example"],"(Level",str(e["difficulty"]) + ")")
        print(e["pinyin"].replace("<b>","").replace("</b>",""))
        print(e["translation"])
        print()

    print("==========")


def DictionaryMode(word):
        content = DownloadUsageExample(word)
        ShowDataConsole(word, content)


def DiscoveryMode(word):
    return

def Main():
    mode = int(input(("Mode (1-Dictionary; 2-Discovery): ")))

    if mode != 1 and mode != 2:
        return
    
    while True:
        word = input("Input word: ").strip()

        if mode == 1:
            DictionaryMode(word)
        else:
            DiscoveryMode(word)
        
        if input("Continue (Y/N): ").upper() == "N":
            break



Main()
