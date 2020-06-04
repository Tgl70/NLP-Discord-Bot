#!/usr/bin/env python3
import time
import json
import requests

import spacy
from spacy import displacy
from nltk.corpus import wordnet as wn
from itertools import chain

from config import *
from GPT2InterfaceUtils import *
from GPT2InterfaceSpacyUtils import *


class GPT2Interface(object):
    def __init__(s):
        print('Loading nlp model "en_core_web_md"')
        s.nlp = spacy.load("en_core_web_sm")  # small version of SpaCy language model
        # s.nlp = spacy.load("en_core_web_md")  # medium version

    def getGpt2Prediction(s, map_object, come_from, place_name, input_text,
                            removeDeterminers=True, concatenate=False):
        """Takes the json map object, the name of the place which will be
        created by gpt2, an (optional) input text to orient the gpt2
        prediction and the concatenate option (dev).
        Will get the gpt2 prediction, clean it and append it to the input
        analyse it and fill the map object with detected entities
        returns both prediction text and the updated map object"""
        # Log an average response time from the Gpt2 server
        start = time.time()
        prediction = s.requestGpt2Prediction(input_text)
        elapsed = time.time() - start

        if not prediction:
            print("Empty Gpt2 prediction")
            return "", map_object

        prediction = cleanGpt2Prediction(input_text, prediction)
        print(f"\n-> GPT2 prediction: {elapsed} s\n")

        with open("responsesTimes.txt", 'a') as f:
            f.write(f"{elapsed}\n")
        res = s.analyseGpt2Output(prediction, removeDeterminers, concatenate)
        return prediction, getUpdatedMap(map_object, place_name, come_from, res)

    def analyseGpt2Output(s, res, removeDeterminers=True, concatenate=False):
        s.doc = s.nlp(res)
        nounChunks = cleanNounChunks(s.doc.noun_chunks)
        if concatenate:
            final_tokens = concatPrepositions(nounChunks, s.doc)
        else:
            final_tokens = formatWordGroups(nounChunks, s.doc, removeDeterminers)
        # Get hypernym for each noun chunk root text
        print(f"{'-'*20}\n")
        for idx, chunk_data in enumerate(final_tokens):
            wordSenses = wn.synsets(chunk_data["chunk"].root.text)
            if not len(wordSenses): continue  # Word not found
            # We're only taking the first sense here!!!!!! as in WordNet native!!!! res = wordSenses[0]
            res = wordSenses[0].hypernym_paths()
            # but this yields a list into another list: remove useless master list
            res = res[0]
            # Now we got the synsets, but we want the actual hypernyms, not the synset (custom WN object)
            # each iteration is an lower level of hypernym (hyponym), first one is the root
            hypernym_tree = [a.lemma_names()[0] for a in res]
            final_hypernym = getMostPreciseKnownHypernym(hypernym_tree)
            try:
                category = TYPE_DICT[final_hypernym]
            except:
                category = IGNORE
                print(f"""{RED}Unknown category {hypernym_tree} for word: {chunk_data["chunk"].root.text}{RESET}""")
            chunk_data["category"] = category
            if category == IGNORE: continue
            # print(f"""--> {chunk_data["chunk"].text}""")
            # print(f"""--> {RED}{chunk_data["full_text"]:40}{CYAN}{CONV_DICT[category]:15}{GREEN}{final_hypernym:25}{YELLOW}{chunk_data["chunk"].root.text:20}{RESET}""")
            # print(GREY + '    ' + ', '.join(hypernym_tree) + RESET)
        # displacy.serve(s.doc, style="dep")
        return final_tokens

    def requestGpt2Prediction(s, inputText="", length=100):
        try:
            rJson = requests.post(GPT2_ENDPOINT,
                            json={'length': str(length), 'text': inputText})
        except: # (ConnectionError, ConnectionRefusedError):
            print("Could not connect to Gpt2 server, is it running?")
        else:
            return rJson.text


if __name__ == '__main__':
    interface = GPT2Interface()
    with open(MAP_FILEPATH, 'r') as f:
        map = json.load(f)
    res = interface.getGpt2Prediction(map, None, "start_place",
                                    "test main GPT2Interface", True)
