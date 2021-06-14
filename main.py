import configure
import postprocess
import preprocess_parser
import relation_extractor
import attribute_extractor
import save_json
import entity_extraction


# retrieve the directory path and file paths
resource_path = configure.RESOURCE_PATH
data_file = configure.DATA_FILE
quickUMLS_file = configure.QUICKUMLS_FILE

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # configure the spacy
    nlp = configure.spacy_config()

    # preprocess including data input
    snippets = preprocess_parser.run(data_file, nlp)

    # extract treatment entities
    entity_extraction.run(snippets, nlp)

    # extract entity relationships
    print('-' * 25 + 'extracting relationship' + '-' * 25)
    relation_extractor.run(snippets)

    # attribute extraction and association
    attribute_extractor.run(snippets, nlp)

    # postprocess
    snippets = postprocess.run(snippets)

    # save, outputs
    save_json.run(snippets)
