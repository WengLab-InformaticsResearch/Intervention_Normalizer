import json
import os
from collections import defaultdict


# save a list of structured snippets to json file.
def save2json(result, outfile):

    with open(outfile, 'w') as f:
        json.dump(result, f)


def run(file_name, result, output_dir):
    save2json(result, os.path.join(output_dir, file_name))



