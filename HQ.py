`#!/usr/bin/env python3
import time
import sys
import requests, json, io, os
from google.cloud import vision
from google.cloud.vision import types
import threading


api_key = "google cloud api key"
search_engine_id = "google search engine id"

#used to track how much time methods take
start_time = time.time()

a1 = 0
a2 = 0
a3 = 0

b1 = 0
b2 = 0
b3 = 0
	
c1 = 0
c2 = 0
c3 = 0

a_results = 0
b_results = 0
c_results = 0

def main():

	file_name = "/Users/davidp/Desktop/screen_cap.png"

	text = detect_text(file_name)

	[unfiltered_question, answers] = parse_text(text)

	words = word_tokenize(unfiltered_question)
	question_list = [w for w in words if not w in stop_words]
	question = ""
	for word in question_list:
		question += word + " "

	wordsA = word_tokenize(answers[0])
	answerA_list = [w for w in wordsA if not w in stop_words]
	ans_A = ""
	for word in answerA_list:
		ans_A += word + " "
	answers[0] = ans_A

	wordsB = word_tokenize(answers[1])
	answerB_list = [w for w in wordsB if not w in stop_words]
	ans_B = ""
	for word in answerB_list:
		ans_B += word + " "
	answers[1] = ans_B

	wordsC = word_tokenize(answers[2])
	answerC_list = [w for w in wordsC if not w in stop_words]
	ans_C = ""
	for word in answerC_list:
		ans_C += word + " "
	answers[2] = ans_C

	print("--- %s seconds ---" % (time.time() - get_text  ))

	print(question)

	[a_count, b_count, c_count] = googleQuestion(question, answers)

	print(answers[0] ,": ", a_count)
	print(answers[1] ,": ", b_count)
	print(answers[2] ,": ", c_count)

	print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")

	t1 = threading.Thread(target = tallyResults, args =(0, answers, question))
	t2 = threading.Thread(target = tallyResults, args =(1, answers, question))
	t3 = threading.Thread(target = tallyResults, args =(2, answers, question))

	t1.start()
	t2.start()
	t3.start()

	t1.join()
	t2.join()
	t3.join()

	a_w_question_count =  a1 + a2 + a3
	b_w_question_count =  b1 + b2 + b3
	c_w_question_count =  c1 + c2 + c3

	print(answers[0] + " with question: " + str(a_w_question_count))
	print(answers[1] + " with question: " + str(b_w_question_count))
	print(answers[2] + " with question: " + str(c_w_question_count))

	print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")

	print(answers[0] + " total results: " + str(a_results))
	print(answers[1] + " total results: " + str(b_results))
	print(answers[2] + " total results: " + str(c_results))

	print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")

	[a_conf, b_conf, c_conf] = calcConfidence(a_count, b_count, c_count, 
		a_w_question_count, b_w_question_count,c_w_question_count,
		int(a_results), int(b_results), int(c_results))

	print(answers[0] + " Confidence: " + str(a_conf) + "%")
	print(answers[1] + " Confidence: " + str(b_conf) + "%")
	print(answers[2] + " Confidence: " + str(c_conf) + "%")


def detect_text(path):
	"""Detects text in the file."""
	client = vision.ImageAnnotatorClient()

	with io.open(path, 'rb') as image_file:
		content = image_file.read()

	image = types.Image(content=content)

	response = client.text_detection(image=image)
	texts = response.text_annotations

	page = ""

	page = texts[0].description

	return page

def parse_text(text):

	lst = text.split("?")

	questionParts = lst[0].splitlines()

	question = ""

	for i in questionParts:
		question += i + " "

	question += "?"

	#print(question)

	wordList = lst[1].splitlines()

	answers = []

	for i, l in enumerate(wordList):
		if len(l) == 0:
			continue
		elif l == " ":
			continue
		else:
			answers.append(l)

	#print(answers)

	return question, answers

def googleQuestion(question, answers):
	snippet = buildSnippet(question)

	[a, b, c] = countChoices(answers, snippet)

	return a, b, c

def calcConfidence(ac, bc, cc, awqc, bwqc, cwqc, ar, br, cr):
	totalc = ac + bc + cc + 1
	totalcwq = awqc + bwqc + cwqc + 1
	totalr = ar + br + cr + 1

	count_weights = 40
	count_with_question_weights = 40
	result_weights = 20

	a_conf = ((ac/totalc) * count_weights) + ((awqc/totalcwq) * count_with_question_weights) + ((ar/totalr) * result_weights)
	b_conf = ((bc/totalc) * count_weights) + ((bwqc/totalcwq) * count_with_question_weights) + ((br/totalr) * result_weights)
	c_conf = ((cc/totalc) * count_weights) + ((cwqc/totalcwq) * count_with_question_weights) + ((cr/totalr) * result_weights)

	return int(a_conf), int(b_conf), int(c_conf)


def buildSnippet(question):
	snippet = ""
	questionTick = requests.get('https://www.googleapis.com/customsearch/v1?key=' +api_key+ '&cx=' +search_engine_id+ '&q=' +question)
	if (questionTick.status_code == 200):
		theJSON = questionTick.json()
		if "items" in theJSON:
			for i in theJSON["items"]:
				if "title" in i:
					s1 = i["title"].encode('utf-8')
					b_a = str(s1)
					[throw1, add1] = b_a.split("'",1)
					snippet += "\n" + add1
				if "snippet" in i:
					s2 = i["snippet"].encode('utf-8')
					b_b = str(s2)
					[throw2, add2] = b_b.split("'",1)
					snippet += "\n" + add2
				else:
					print("No snippet")
			return snippet
		else:
			print("no items")
	else:
		print("Recieved an Error from server, cannot retrieve results " + str(questionTick.status_code))

def countChoices(answers, snippet):
	a = snippet.upper().count(answers[0].upper())
	b = snippet.upper().count(answers[1].upper())
	c = snippet.upper().count(answers[2].upper())

	return a, b, c


def totalResults(query):
	snippet = ""

	tick = requests.get('https://www.googleapis.com/customsearch/v1?key=' +api_key+ '&cx=' +search_engine_id+ '&q=' +query)

	theJSON = tick.json()
	if "queries" in theJSON:
		if "request" in theJSON["queries"]:
			if "totalResults" in theJSON["queries"]["request"][0]:
				results = theJSON["queries"]["request"][0]["totalResults"]

	if "items" in theJSON:
		for i in theJSON["items"]:
			if "title" in i:
				s1 = i["title"].encode('utf-8')
				b_a = str(s1)
				[throw1, add1] = b_a.split("'",1)
				snippet += "\n" + add1
			if "snippet" in i:
				s2 = i["snippet"].encode('utf-8')
				b_b = str(s2)
				[throw2, add2] = b_b.split("'",1)
				snippet += "\n" + add2
	return results, snippet


def tallyResults(index, answers, question):
	question_and_choice =  question + ' "' + answers[index] + '"'
	[results, snippet] = totalResults(question_and_choice)
	[a, b, c] = countChoices(answers, snippet)

	global a1, a2, a3, b1, b2, b3, c1, c2, c3, a_results, b_results, c_results

	if index == 0:
		a_results = results
		a1 = a
		b1 = b
		c1 = c

	elif index == 1:
		b_results = results
		a2 = a
		b2 = b
		c2 = c

	else:
		c_results = results
		a3 = a
		b3 = b
		c3 = c


if __name__ == "__main__": main()
