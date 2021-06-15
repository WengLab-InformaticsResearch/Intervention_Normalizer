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


def extract_abbreviations(json_f, nlp):
    text = json_f['abstract']
    doc = nlp(text)
    abrv = extract_abbreviations_helper(doc)
    return abrv


# read in the annotation file and extract the intervention snippets.
def extract_snippets(json_f):
    snippets = []
    if 'Sentence-level breakdown' not in json_f.keys():
        return snippets
    for sents in json_f['Sentence-level breakdown']:
        if 'Evidence Elements' in sents.keys():
            for inter in sents['Evidence Elements']['Intervention']:
                snippets.append(inter)
        if 'Evidence Propositions' in sents.keys():
            for element in sents['Evidence Propositions']:
                if 'Intervention' not in element.keys():
                    continue
                if type(element['Intervention']) == str:
                    element['Intervention'] = {
                        'term': element['Intervention']
                    }
                    snippets.append(element['Intervention'])
                if type(element['Intervention']) == list:
                    for i in range(len(element['Intervention'])):
                        element['Intervention'][i] = {
                            'term': element['Intervention'][i]
                        }
                        snippets.append(element['Intervention'][i])

    return snippets


# for each file, we replace the abbreviations in the intervention snippets with their full name
# replace the abbreviations with the full name, also remove the parenthesis

# the return would be a list of snippets, all attributes would be stored in a dict format
def remove_parenthesis(abrv, inter):
    for item in inter:

        # remove the abbreviation within the parenthesis (including parenthesis).
        processed = item['term']

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
        item['processed'] = processed


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
def run(input_file, nlp):

    # covert the json to dict
    json_f = json.load(open(input_file, 'r'))

    # extract abbreviation
    # print('-' * 25 + 'extracting abbreviations' + '-' * 25)
    abrv = extract_abbreviations(json_f, nlp)
    # print(abrv)

    # extract intervention snippets
    # print('-' * 25 + 'extracting intervention snippets' + '-' * 25)
    inter = extract_snippets(json_f)
    # print(inter)

    # remove parenthesis
    # print('-' * 25 + 'removing parenthesis' + '-' * 25)
    remove_parenthesis(abrv, inter)

    # text normalization
    # print('-' * 25 + 'normalizing text' + '-' * 25)
    for snippet in inter:
        snippet['processed'] = normalize_text(snippet['processed'])
    return inter, json_f

