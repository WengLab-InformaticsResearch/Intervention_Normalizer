import json
import os
import configure
from collections import defaultdict


# save a list of structured snippets to json file.
def save2json(name, snippets, outfile):
    output = {'name': name,
              'snippets': snippets}
    with open(outfile, 'w') as f:
        json.dump(output, f)


def run(snippets):
    procedure = []
    device = []
    activity = []
    drug = []
    none = []
    has_relation = []
    has_attribute = []
    visited = []
    total = []
    file_ids = defaultdict(list)
    for snippet in snippets:
        file_ids[snippet['file_id']].append(snippet)
        if snippet['text'].lower() in visited:
            continue
        visited.append(snippet['text'].lower())
        total.append(snippet)
        flag = False
        if 'has_drug' in snippet.keys():
            drug.append(snippet)
            flag = True
        if 'has_procedure' in snippet.keys():
            procedure.append(snippet)
            flag = True
        if 'has_device' in snippet.keys():
            device.append(snippet)
            flag = True
        if 'has_activity' in snippet.keys():
            activity.append(snippet)
            flag = True
        if 'has_relation' in snippet.keys() and snippet['has_relation'] != 'N/A':
            has_relation.append(snippet)

        found = False
        for key in snippet.keys():
            if not isinstance(snippet[key], list):
                continue
            for entity in snippet[key]:
                if 'has_duration' in entity.keys() or 'has_form' in entity.keys() or 'has_strength' in entity.keys() or 'has_route' in entity.keys() or 'has_frequency' in entity.keys() or 'has_dosage' in entity.keys() or 'has_count' in entity.keys():
                    has_attribute.append(snippet)
                    break
            if found:
                break

        if not flag:
            none.append(snippet)

    save2json('has_procedure', procedure,
              os.path.join(configure.SAVE_PATH, 'has_procedure.json'))
    save2json('has_device', device,
              os.path.join(configure.SAVE_PATH, 'has_device.json'))
    save2json('has_drug', drug,
              os.path.join(configure.SAVE_PATH, 'has_drug.json'))
    save2json('has_activity', activity,
              os.path.join(configure.SAVE_PATH, 'has_activity.json'))
    save2json('has_none', none,
              os.path.join(configure.SAVE_PATH, 'has_none.json'))
    save2json('total', total,
              os.path.join(configure.SAVE_PATH, 'total.json'))
    save2json('has_attribute', has_attribute,
              os.path.join(configure.SAVE_PATH, 'has_attribute.json'))
    save2json('has_relation', has_relation,
              os.path.join(configure.SAVE_PATH, 'has_relation.json'))
    for key, value in file_ids.items():
        save2json(key, value, os.path.join(configure.SAVE_PATH, key + '.json'))
