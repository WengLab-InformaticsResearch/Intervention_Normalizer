import configure
import os


def get_map():
    drug_types = "T116,T195,T123,T122,T103,T120,T104,T200,T196,T126,T131,T125,T129,T130,T197,T114,T109,T121,T192,T127"
    procedure_types = "T060,T065,T058,T059,T063,T062,T061"
    device_types = "T203,T074,T075"
    activity_types = "T052,T053,T056,T051,T064,T055,T066,T057,T054"
    sem_map = {}

    for item in drug_types.split(','):
        sem_map[item] = 'drug'
    for item in procedure_types.split(','):
        sem_map[item] = 'procedure'
    for item in device_types.split(','):
        sem_map[item] = 'device'
    for item in activity_types.split(','):
        sem_map[item] = 'activity'
    return sem_map


def get_semtype_id(file):
    sem_id = {}
    with open(file, 'r') as f:
        for line in f:
            tokens = line.split('|')
            sem_id[tokens[3]] = tokens[2]
    return sem_id


def convert2standard(snippets):
    sem_id = get_semtype_id(os.path.join(configure.RESOURCE_PATH, 'semGroups.txt'))

    sem_map = get_map()

    result = []

    for snippet in snippets:
        standard = {'file_id': snippet['file_id'], 'start': snippet['start_pos'], 'end': snippet['end_pos'],
                    'text': snippet['raw_text']}
        drug = []
        procedure = []
        device = []
        activity = []

        components = []
        for entity in snippet['entities']:
            components.append(entity['cui'])
            temp_entity = {'text': entity['ngram'], 'maps_to': entity['cui'] + ':' + entity['term']}
            sem_type = sem_map[sem_id[entity['semtypes'][0]]]
            del entity['ngram']
            del entity['term']
            del entity['cui']
            del entity['similarity']
            del entity['semtypes']
            del entity['preferred']
            del entity['id']

            # deal with the negation
            if 'has_negation' not in entity.keys() or len(entity['has_negation']) == 0:
                entity['has_negation'] = 'affirmed'
            else:
                entity['has_negation'] = 'negated'

            for key, value in entity.items():
                temp_entity[key] = value

            if sem_type == 'drug':
                drug.append(temp_entity)
            if sem_type == 'procedure':
                procedure.append(temp_entity)
            if sem_type == 'device':
                device.append(temp_entity)
            if sem_type == 'activity':
                activity.append(temp_entity)

        if len(drug) > 0:
            standard['has_drug'] = drug
        if len(procedure) > 0:
            standard['has_procedure'] = procedure
        if len(device) > 0:
            standard['has_device'] = device
        if len(activity) > 0:
            standard['has_activity'] = activity


        # add the relation
        if snippet['relation'] == 'N/A':
            relation = 'N/A'
        elif snippet['relation'] == 'combined_with':
            comp = '<->'.join(components)
            relation = 'combined_with (' + comp + ')'
        elif snippet['relation'] == 'before':
            comp = '->'.join(components)
            relation = 'before (' + comp + ')'
        elif snippet['relation'] == 'after':
            comp = '->'.join(reversed(components))
            relation = 'before (' + comp + ')'
        elif snippet['relation'] == 'contain':
            comp = '->'.join(components)
            relation = 'contain (' + comp + ')'
        elif snippet['relation'] == 'in':
            comp = '->'.join(reversed(components))
            relation = 'contain (' + comp + ')'
        elif snippet['relation'] == 'substituted_for':
            comp = '->'.join(components)
            relation = 'substituted_for (' + comp + ')'
        elif snippet['relation'] == 'switched_to':
            comp = '->'.join(reversed(components))
            relation = 'substituted_for (' + comp + ')'
        elif snippet['relation'] == 'without':
            comp = '->'.join(components)
            relation = 'without (' + comp + ')'
        elif snippet['relation'] == 'or':
            comp = '<->'.join(components)
            relation = 'or (' + comp + ')'

        standard['has_relation'] = relation
        result.append(standard)
    return result


def run(snippets):
    snippets = convert2standard(snippets)
    return snippets
