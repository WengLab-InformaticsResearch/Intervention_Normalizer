import re
import os
import json


# read in a raw abstract, find all the abbreviation and corresponding full names, return a dict
def extract_abbreviations_helper(doc):
    dct = {}
    for abrv in doc._.abbreviations:
        # review and remove the invalid abbreviations: rule: if the full name contains parenthesis, then remove
        fname = abrv._.long_form.text
        if re.search(r'[\(\)]', fname) is None:
            dct[str(abrv)] = fname
    return dct


def extract_abbreviations(data_path, nlp):
    abrv = {}
    for file in os.listdir(data_path):
        if file.endswith(".json"):
            file_path = os.path.join(data_path, file)
            with open(file_path, 'r') as f:
                text = json.load(f)['abstract']
                doc = nlp(text)
                abrv[file.rstrip('.json')] = extract_abbreviations_helper(doc)
    return abrv


# read in the annotation file and extract the intervention snippets.
def extract_snippets_helper(read_path):
    snippets = []
    with open(read_path) as f_read:
        json_f = json.load(f_read)
        if 'Sentence-level breakdown' not in json_f.keys():
            return snippets
        for sents in json_f['Sentence-level breakdown']:
            if 'Evidence Elements' not in sents.keys():
                continue
            for inter in sents['Evidence Elements']['Intervention']:
                snippets.append(inter)
    return snippets


def extract_snippets(data_path):
    inter = {}
    for file in os.listdir(data_path):
        if file.endswith(".json"):
            file_path = os.path.join(data_path, file)
            inter[file.rstrip(".json")] = extract_snippets_helper(file_path)
    return inter


# for each file, we replace the abbreviations in the intervention snippets with their full name
# replace the abbreviations with the full name, also remove the parenthesis

# the return would be a list of snippets, all attributes would be stored in a dict format
def remove_parenthesis(file_id, abrv, inter):
    snippets = []
    for item in inter:
        snippet = {'file_id': file_id,
                   'start_pos': item['start'],
                   'end_pos': item['end'],
                   'raw_text': item['term']}

        # remove the abbreviation within the parenthesis (including parenthesis).
        processed = snippet['raw_text']

        for key, value in abrv.items():
            # match the key in the parenthesis, also before and after the key in the parenthesis should have minimum
            # num of characters
            processed = re.sub(rf'\(\s*{key}\s*\)', '', processed)
            # replace the abbreviation with full name
            if key in processed:
                processed = re.sub(rf'{key}', value, processed)
        # directly remove the parenthesis as well as the content.
        processed = re.sub(r'\(.*?\)', '', processed)
        # replace two spaces with one space
        processed = re.sub(r'( )+', ' ', processed)
        snippet['processed'] = processed

        if snippet['processed'] != snippet['raw_text']:
            raw = snippet['raw_text']
            processed = snippet['processed']
            print(f'text changed:\n before:\t{raw}\nafter:\t{processed}')
        snippets.append(snippet)
    return snippets


# helper normalize the text
def normalize_text(text):
    # remove extra '(' ')'
    text = re.sub(r'[\(\)]', '', text)
    # replace multiple whitespace with one
    text = re.sub(r'( )+', ' ', text)
    # remove '-' and ' .'
    text = re.sub(r'-', ' ', text)
    text = re.sub(r'\s\.', ' ', text)
    # replace '+' with 'plus'
    text = re.sub(r'\+', ' plus ', text)
    # replace unicode whitespace
    text = text.replace(u'\u00a0', ' ')
    text = re.sub(r'\s+', ' ', text)
    # the return result would be lower and stripped
    return text.lower().strip()


# preprocess
def run(data_file, nlp):
    # extract abbreviation
    print('-' * 25 + 'extracting abbreviations' + '-' * 25)
    abrv = extract_abbreviations(data_file, nlp)
    print(abrv)

    # extract intervention snippets
    print('-' * 25 + 'extracting intervention snippets' + '-' * 25)
    inter = extract_snippets(data_file)
    print(inter)

    # remove parenthesis
    snippets = []
    print('-' * 25 + 'removing parenthesis' + '-' * 25)

    for file in os.listdir(data_file):
        if file.endswith(".json"):
            file_id = file.rstrip('.json')
            snippets.extend(remove_parenthesis(file_id, abrv[file_id], inter[file_id]))

    # text normalization
    print('-' * 25 + 'normalizing text' + '-' * 25)
    for snippet in snippets:
        snippet['processed'] = normalize_text(snippet['processed'])
    return snippets

