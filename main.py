import sys
import configure
import postprocess
import preprocess_parser
import relation_extractor
import attribute_extractor
import save_json
import entity_extraction
import os
import argparse


def init_argparse():
    parser = argparse.ArgumentParser(
        description="normalize intervention in the MEPs."
    )
    parser.add_argument("--data_dir")
    parser.add_argument("--output_dir")
    return parser.parse_args()


# retrieve the directory path and file paths
resource_path = configure.RESOURCE_PATH
quickUMLS_file = configure.QUICKUMLS_FILE

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # read data_dir and output_dir
    parsed_args = init_argparse()
    
    if not os.path.isdir(parsed_args.data_dir):
        print("please input the correct data folder")
        sys.exit()
    
    if not os.path.isdir(parsed_args.output_dir):
        os.mkdir(parsed_args.output_dir)

    # configure the spacy
    nlp = configure.spacy_config()

    file_list = [x for x in os.listdir(parsed_args.data_dir) if x.endswith(".json")]
    for file in file_list:
        # preprocess data input
        snippets, json_f = preprocess_parser.run(os.path.join(parsed_args.data_dir, file), nlp)

        # extract treatment entities
        entity_extraction.run(snippets, nlp)

        # extract entity relationships
        relation_extractor.run(snippets)

        # attribute extraction and association
        attribute_extractor.run(snippets, nlp)

        # postprocess
        postprocess.run(snippets)

        # save, outputs
        save_json.run(file, json_f, parsed_args.output_dir)
