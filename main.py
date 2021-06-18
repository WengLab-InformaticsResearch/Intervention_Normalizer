import sys
import configure
import postprocess
import preprocess
import relation_extractor
import attribute_extractor
import entity_extractor
import os
import argparse
import json


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

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # read data_dir and output_dir, and quickumls_dir
    parsed_args = init_argparse()
    quickUMLS_file = parsed_args.quickumls_dir
    
    if not os.path.isdir(parsed_args.data_dir):
        print("please input the correct data folder")
        sys.exit()
    
    if not os.path.isdir(parsed_args.output_dir):
        os.mkdir(parsed_args.output_dir)

    # configure the spacy
    nlp = configure.spacy_config()

    file_list = [x for x in os.listdir(parsed_args.data_dir) if x.endswith(".json")]
    for file in file_list:
        print("processing\t" + str(file))
        # preprocess data input
        print("preprocessing...")
        snippets, json_f = preprocess.run(os.path.join(parsed_args.data_dir, file), nlp)

        print("extracting entities...")
        # extract treatment entities
        entity_extractor.run(snippets, nlp, quickUMLS_file, resource_path)

        print("extracting relations...")
        # extract entity relationships
        relation_extractor.run(snippets)

        print("extracting attributes...")
        # attribute extraction and association
        attribute_extractor.run(snippets, nlp)

        # postprocess
        print("postprocessing...")
        postprocess.run(snippets)

        # save, outputs
        save2json(json_f, os.path.join(parsed_args.output_dir, file))
