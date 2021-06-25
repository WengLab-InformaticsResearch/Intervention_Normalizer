from intervention_normalizer import preprocess, entity_extractor, relation_extractor, attribute_extractor, postprocess
import os
import json
import time

def save2json(result, outfile):
    with open(outfile, 'w') as f:
        json.dump(result, f)

def process(nlp, quickUMLS_file, resource_path, input, output, file_list):
    json_f_list = list()
    snippets_list = list()
    start_time = time.time()
    # preprocess
    # print("preprocessing...")
    for file in file_list:
        # print("processing\t" + str(file))
        snippets, json_f = preprocess.run(os.path.join(input, file), nlp, file)
        if json_f is None:
            continue
        snippets_list.extend(snippets)
        json_f_list.append(json_f)

    # deal with rest of the processing
    # print("extracting entities...")
    # extract treatment entities
    entity_extractor.run(snippets_list, nlp, quickUMLS_file, resource_path)

    # print("extracting relations...")
    # extract entity relationships
    relation_extractor.run(snippets_list)

    # print("extracting attributes...")
    # attribute extraction and association
    attribute_extractor.run(snippets_list, nlp)

    # postprocess
    # print("postprocessing...")
    postprocess.run(snippets_list)

    for file in json_f_list:
        # save, outputs
        save2json(file, os.path.join(output, file['doc_id'] + '.json'))

    elapsed_time = time.time() - start_time
    print("Batch finished:\t" + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
