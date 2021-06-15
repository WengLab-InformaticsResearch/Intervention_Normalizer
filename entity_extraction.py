import re
import configure
import os
from quickumls import QuickUMLS


# concepts and terms to exclude for linking
# the attribute and relation words would be excluded for the entity extraction


# import the excluded terms
def exclude_terms_helper(file):
    lst = []
    with open(file, 'r') as f:
        for line in f:
            if line.startswith('@'):
                lst.append(line.split('::')[1].strip().replace('\\\\', '\\'))
    return lst


def get_exclude_terms(attr_file, rel_file, extra_file):
    attr = exclude_terms_helper(attr_file)
    rel = exclude_terms_helper(rel_file)
    terms = '|'.join(attr + rel)

    extra_terms = []
    with open(extra_file, 'r') as f:
        for line in f:
            extra_terms.append(line.strip())

    terms = '|'.join(extra_terms) + '|' + terms
    return terms


def get_semtype_map(file):
    sem_map = {}
    with open(file, 'r') as f:
        for line in f:
            tokens = line.split('|')
            sem_map[tokens[2]] = tokens[3]
    return sem_map


# functions involved in the mapping
terms_excluded = []


def extract_entities(snippet, matcher, exclude_terms, sem_map):
    lst = []
    result = matcher.match(snippet, best_match=True, ignore_syntax=False)
    for item in result:
        text = item[0]['ngram']
        # exclude if in the attribute or relation phrase/word list or extra terms
        invalid = False

        if re.match(f'^({exclude_terms})$', text, re.I):
            terms_excluded.append(snippet + '\t' + text)
            invalid = True

        if invalid:
            print(f'the excluded term is:\t{text}')
        else:
            types = item[0]['semtypes']
            type_full = set()
            for tp in types:
                type_full.add(sem_map[tp])
            item[0]['semtypes'] = type_full
            lst.append(item[0])
        lst = sorted(lst, key=lambda i: i['start'])
    return lst


# expand boundary based on contextual syntactic information
def expand_boundary(rep, nlp, excluded):
    doc = nlp(rep)
    merged = {}
    flag = ''
    start = -1
    end = -1
    accepted_pos = ['ADJ', 'NOUN', 'ADV', 'PROPN', 'PRON', 'X']
    for token in reversed(doc):
        if flag == '':
            if 'entity' in token.text.lower():
                flag = token.text
                end = token.idx + len(token.text)
                start = token.idx
            continue

        if re.match(f'^({excluded})$', token.text, re.I):
            merged[flag] = (start, end)
            flag = ''
            end = -1
            start = -1
            continue
        if token.pos_ in accepted_pos:
            start = token.idx
            continue
        merged[flag] = (start, end)
        flag = ''
        end = -1
        start = -1
    if flag != '':
        merged[flag] = (start, end)
    return merged


def remapping(entities, merged, rep, processed, matcher, sem_map, excluded_terms):
    new_entities = []

    for key, value in merged.items():
        rep_str = rep[value[0]: value[1]]
        flag = False
        if len(rep_str.split(' ')) > 1:
            flag = True
        # find the start and end index in the processed
        start = len(processed)
        end = 0
        anchor = ''
        for entity in entities:
            if entity['id'] in rep_str:
                if entity['start'] < start:
                    start = entity['start']
                    anchor = entity['id']
                if entity['end'] > end:
                    end = entity['end']
        start = start - (rep_str.find(anchor))
        result = extract_entities(processed[start: end], matcher, excluded_terms, sem_map)
        if len(result) == 0:
            print(f'the merged term {processed[start: end]} has no concept !!!')
            continue
        result = sorted(result, key=lambda i: i['start'])
        entity = result[-1]
        entity['ngram'] = processed[start: end]
        entity['start'] = start
        entity['end'] = end
        new_entities.append(entity)
    return new_entities


# substitute the treatment terms with "ENTITY" + num for lateral use
def convert_snippet(snippet):
    count = 0
    converted = ''
    pointer = 0

    for entity in snippet['entities']:
        start_pos = int(entity['start'])
        end_pos = int(entity['end'])

        rep = "ENTITY" + str(count)
        entity['id'] = rep
        converted = converted + snippet['processed'][pointer: start_pos] + rep
        pointer = end_pos
        count += 1
    converted = converted + snippet['processed'][pointer:len(snippet['processed'])]
    snippet['representation'] = converted


def run(snippets, nlp):
    resource_path = configure.RESOURCE_PATH
    sem_file = os.path.join(configure.RESOURCE_PATH, 'SemGroups.txt')
    quickUMLS_file = configure.QUICKUMLS_FILE

    # retrieve the predefined treatment semantic types
    drug_types, procedure_types, activity_types, device_types = configure.quickUMLS_config()

    # get the exclude_terms
    exclude_terms = get_exclude_terms(os.path.join(resource_path, 'attribute_patterns.txt'),
                                      os.path.join(resource_path, 'relation_patterns.txt'),
                                      os.path.join(resource_path, 'exclude_terms.txt'))

    # get sem_map, which is the association of the semantic types and semantic groups
    sem_map = get_semtype_map(sem_file)

    # initial extraction
    # print('*' * 25 + 'initial extraction' + '*' * 25)
    matcher = QuickUMLS(quickUMLS_file, overlapping_criteria='score', threshold=0.8,
                        accepted_semtypes=','.join([drug_types, procedure_types, activity_types, device_types]))

    for snippet in snippets:
        snippet['entities'] = extract_entities(snippet['processed'], matcher, exclude_terms,
                                               sem_map)
        convert_snippet(snippet)

    # remapping: expand the boundary of initially extracted treatment entities
    # print('*' * 25 + 'remapping' + '*' * 25)
    file = configure.QUICKUMLS_FILE
    # the overlapping criteria is changed to 'length' prior.
    matcher = QuickUMLS(file, overlapping_criteria='length', threshold=0.8,
                        accepted_semtypes=','.join([drug_types, procedure_types, activity_types, device_types]))

    remapping_exclude_terms = get_exclude_terms(os.path.join(resource_path, 'attribute_patterns.txt'),
                                                os.path.join(resource_path,
                                                             'relation_patterns.txt'),
                                                os.path.join(resource_path,
                                                             'remapping_exclude_terms.txt'))
    for snippet in snippets:
        # print('processing:\t' + snippet['processed'])
        if len(snippet['entities']) == 0:
            continue
        # print('before expanding:')
        # for entity in snippet['entities']:
        #     print(entity['ngram'])

        new_entities = remapping(snippet['entities'],
                                 expand_boundary(snippet['representation'],
                                                 nlp,
                                                 remapping_exclude_terms),
                                 snippet['representation'],
                                 snippet['processed'],
                                 matcher, sem_map, exclude_terms)
        new_entities = sorted(new_entities, key=lambda x: x['start'])
        snippet['entities'] = new_entities
        # print('after expanding:')
        # for entity in snippet['entities']:
        #     print(entity['ngram'])

    # convert semtype set to list (for json)
    for snippet in snippets:
        if 'entities' in snippet.keys():
            for entity in snippet['entities']:
                entity['semtypes'] = list(entity['semtypes'])

    # convert to representation
    for snippet in snippets:
        convert_snippet(snippet)
