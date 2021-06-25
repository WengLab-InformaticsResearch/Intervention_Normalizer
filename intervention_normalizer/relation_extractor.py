import os
from collections import defaultdict
import re
from intervention_normalizer import configure


# retrieve the regular expression for each relation from 'relation_patterns.txt'
def get_rel():
    # var_map: store the trigger phrases for the regular expressions
    var_map = {}
    # rel_map: store the regular expressions for each relation
    rel_map = defaultdict(list)
    with open(os.path.join(configure.RESOURCE_PATH, 'relation_patterns.txt'), 'r') as patterns:
        for line in patterns:
            if line.startswith('#') or len(line) == 0 or re.search(r'^\s', line):
                continue
            if line.startswith('@'):
                var_map[line.split('::')[0]] = line.split('::')[1].strip()
            else:
                rel = line.split('::')[0].strip()
                pat = line.split('::')[1].strip()
                for key, value in var_map.items():
                    pat = pat.replace(key, value)
                rel_map[rel].append(pat)
    return rel_map


def extract_relation(snippets):
    rel_map = get_rel()
    for snippet in snippets:
        if 'entities' not in snippet.keys():
            continue
        # number of treatment entities in the snippet
        entity_num = len(snippet['entities'])
        rep = snippet['representation']
        # print('processing:\t', rep)
        for key, value in rel_map.items():
            if int(key.split('@')[1]) != entity_num:
                continue
            for item in value:
                if re.search(item, rep):
                    # print('relation found:\t', key, item)
                    snippet['relation'] = key.split('@')[0]
                    break
            if 'relation' in snippet.keys():
                break
        if 'relation' not in snippet.keys():
            snippet['relation'] = 'N/A'


def run(snippets):
    extract_relation(snippets)
