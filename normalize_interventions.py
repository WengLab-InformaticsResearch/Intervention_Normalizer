import sys
from intervention_normalizer import configure, preprocess, entity_extractor, relation_extractor, attribute_extractor, postprocess, batch_process
import os
import argparse
import json
import time


def init_argparse():
    parser = argparse.ArgumentParser(
        description="normalize intervention in the MEPs."
    )
    parser.add_argument("--data_dir")
    parser.add_argument("--output_dir")
    parser.add_argument("--quickumls_dir")
    return parser.parse_args()


def save2json(result, outfile):
    with open(outfile, 'w') as f:
        json.dump(result, f)


# retrieve the directory path and file paths
resource_path = configure.RESOURCE_PATH

# use if the json files are contained in subfolders
def contain_subcategory(parsed_args, nlp, quickUMLS_file, resource_path):
    if not os.path.isdir(parsed_args.data_dir):
        print("please input the correct data folder")
        sys.exit()

    for x in os.listdir(parsed_args.data_dir):
        temp_data_path = os.path.join(parsed_args.data_dir, x)
        if not os.path.isdir(temp_data_path):
            continue
        print("processing year:\t" + x)
        temp_output_path = os.path.join(parsed_args.output_dir, x)
        if not os.path.isdir(temp_output_path):
            os.mkdir(temp_output_path)

        file_list = [x for x in os.listdir(temp_data_path) if x.endswith(".json")]
        chunks = [file_list[x:x+2000] for x in range(0, len(file_list), 2000)]
        for i in range(len(chunks)):
            print("processing batch " + str(i))
            batch_process.process(nlp, quickUMLS_file, resource_path, temp_data_path, temp_output_path, chunks[i])

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # read data_dir and output_dir, and quickumls_dir
    parsed_args = init_argparse()
    quickUMLS_file = parsed_args.quickumls_dir

    # configure the spacy
    nlp = configure.spacy_config()

    # use if the json files are contained in subfolders
    # contain_subcategory(parsed_args, nlp, quickUMLS_file, resource_path)

    # batch process
    file_list = [x for x in os.listdir(parsed_args.data_dir) if x.endswith(".json")]
    chunks = [file_list[x:x + 2000] for x in range(0, len(file_list), 2000)]
    for i in range(len(chunks)):
        print("processing batch " + str(i))
        batch_process.process(nlp, quickUMLS_file, resource_path, parsed_args.data_dir, parsed_args.output_dir, chunks[i])


    # for file in file_list:
    #     print("processing\t" + str(file))
    #     # preprocess data input
    #     start_time = time.time()
    #     print("preprocessing...")
    #     snippets, json_f = preprocess.run(os.path.join(parsed_args.data_dir, file), nlp)
    #     elapsed_time = time.time() - start_time
    #     print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
    #     print("extracting entities...")
    #     # extract treatment entities
    #     entity_extractor.run(snippets, nlp, quickUMLS_file, resource_path)
    #     elapsed_time = time.time() - start_time
    #     print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
    #     print("extracting relations...")
    #     # extract entity relationships
    #     relation_extractor.run(snippets)
    #     elapsed_time = time.time() - start_time
    #     print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
    #     print("extracting attributes...")
    #     # attribute extraction and association
    #     attribute_extractor.run(snippets, nlp)
    #     elapsed_time = time.time() - start_time
    #     print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
    #     # postprocess
    #     print("postprocessing...")
    #     postprocess.run(snippets)
    #     elapsed_time = time.time() - start_time
    #     print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
    #     # save, outputs
    #     save2json(json_f, os.path.join(parsed_args.output_dir, file))
    #     elapsed_time = time.time() - start_time
    #     print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
