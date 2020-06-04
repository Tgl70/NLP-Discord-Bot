from config import *


def cleanNounChunks(doc_noun_chunks):
    """Remove noun chunk repetitions and tokens < 3 char"""
    chunk_texts = []
    nounChunks = []
    for chunk in doc_noun_chunks:
        chunk_text = chunk.root.text.lower()
        if len(chunk_text) > 3 and chunk_text not in chunk_texts and chunk_text not in EXCLUDE_LIST:
            chunk_texts.append(chunk.root.text.lower())
            nounChunks.append(chunk)
    return nounChunks


def removeDeterminersFromTokens(tokens, doc):
    res = []
    for chunk in tokens:
        sliced_flag = False
        for child in chunk.root.children:
            if child.dep_ == "det":# and chunk.start == child.i:
                res.append({
                            "category": IGNORE,
                            "chunk": chunk,
                            "full_text": doc.text[doc[child.i + 1].idx:chunk.end_char]
                        })
                sliced_flag = True
        if not sliced_flag:
            res.append({
                        "category": IGNORE,
                        "chunk": chunk,
                        "full_text": chunk.text
                    })
    return res


def formatWordGroups(nounChunks, doc, removeDeterminers):
    if removeDeterminers:
        return removeDeterminersFromTokens(nounChunks, doc)
    return [{"chunk": chunk, "full_text": chunk.text, "category": IGNORE} for chunk in nounChunks]


def concatPrepositions(nounChunks, doc):
    # Append all trailing "prep" + "pobj" for each noun
    to_remove = []
    tmp_tokens = []
    for chunk in nounChunks:
        # check if a children of the chunk have the "prep" dep_
        prep = None
        for child in chunk.root.children:
            if child.dep_ == "prep" and chunk.end == child.i:
                # print(chunk, chunk.end, child.i)
                prep = child
        # If we have one, check if this child's child does have the "pobj" dep_
        pobj = None
        if prep:
            for child in prep.children:
                if child.dep_ == "pobj" and chunk.end + 2 >= child.i:
                    # print(chunk, chunk.end, child.i)
                    pobj = child
        if pobj: # Nice, now concatenate
            tmp_tokens.append({
                        "category": IGNORE,
                        "chunk": chunk,
                        "start_c": chunk.start_char,
                        "end_c": pobj.idx + len(pobj.text),
                        "full_text": doc.text[chunk.start_char:pobj.idx + len(pobj.text)]
                    })
            to_remove.append({"start_c": prep.idx, "end_c": pobj.idx + len(pobj.text)})
        else:
            tmp_tokens.append({
                        "category": IGNORE,
                        "chunk": chunk,
                        "start_c": chunk.start_char,
                        "end_c": chunk.end_char,
                        "full_text": doc.text[chunk.start_char:chunk.end_char]
                    })
    # Remove small concat chunks
    final_tokens = []
    for token in tmp_tokens:
        keep_flag = True
        for to_delete_spans in to_remove:
            # If token is inside a remove span
            if token["start_c"] >= to_delete_spans["start_c"] and token["end_c"] <= to_delete_spans["end_c"]:
                keep_flag = False
        if keep_flag:
            final_tokens.append(token)
    # Handle the PROPN concatenation
    propns_concat = {}
    propns = [token for token in doc if token.pos_ == "PROPN"]
    for propn in propns:
        propns_concat[propn.head.text] = propn.text
        # print(f"PROPN detected: {propn.text} linked to {propn.head.text}, char_idx = {propn.idx}")
    for token in final_tokens:
        if token["chunk"].root.text in propns_concat:
            token["full_text"] = propns_concat[token["chunk"].root.text] + ", " + token["full_text"]
    return final_tokens
