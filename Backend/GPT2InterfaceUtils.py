import random

from config import *


def getUpdatedMap(map, place_name, come_from, res):
    links = set()
    if come_from:
        links.add(come_from)
        map["locations"][come_from]["links"].append(place_name)
    objects = set()
    NPCs = set()
    for chunk_data in res:
        cat = chunk_data["category"]
        # root_text = chunk_data["chunk"].root.text
        if cat == PICKABLE or cat == HEALTH:
            objects.add(chunk_data["full_text"])
            map["objects"][chunk_data["full_text"]] = {
                                                "interactions": ["pick_up", "attack"],
                                                "action": "carrying",
                                                "damage": random.randint(0, 3),
                                                "protection": 0
                                            }
        elif chunk_data["category"] == INTERACTABLE:
            NPCs.add(chunk_data["full_text"])
            map["NPCs"][chunk_data["full_text"]] = {
                                                "attitude": -9999,
                                                "interactions": ["fight"],
                                                "health": random.randint(3, 6),
                                                "damage": random.randint(2, 10)
                                            }
        elif chunk_data["category"] == POSITION:
            links.add(chunk_data["full_text"])

    # if len(links) > 5:
        # links = links[:5]

    map["locations"][place_name] = {
        "conditions": [],
        "options" : [],
        "links": list(links),
        "objects": list(objects),
        "NPCs": list(NPCs)
    }
    # print(json.dumps(map, indent=4, sort_keys=True))
    return map


def cleanGpt2Prediction(input_text, prediction):
    """concat input and prediction, remove the last unfinished sentence,
    remove dialog line"""
    if input_text and input_text[-1] != " ": input_text += " "
    prediction = input_text + prediction.strip()
    cutted = ""
    if prediction[-1] != '.':
        last_dot_idx = prediction.rfind('. ')
        if last_dot_idx != -1:
            cutted = prediction[last_dot_idx + 1:]
            prediction = prediction[:last_dot_idx + 1]
    print(f"""{'='*20}\n-> Removed:\n|{cutted}|\nat the end of prediction""")
    res = [line for line in prediction.split('\n') if line and line.strip()[0] != '"']
    return '\n'.join(res)


def getMostPreciseKnownHypernym(hypernym_list):
    res = 0
    for hyp in hypernym_list:
        if hyp in TYPE_DICT: res = hyp
    return res
