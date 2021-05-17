import spacy
import scispacy
from scispacy.abbreviation import AbbreviationDetector

RESOURCE_PATH = "./resource"
DATA_FILE = "./example/dataset"
QUICKUMLS_FILE = ""
SAVE_PATH = "./example/result"


# configure the quickUMLS
def quickUMLS_config():
    drug_types = "T116,T195,T123,T122,T103,T120,T104,T200,T196,T126,T131,T125,T129,T130,T197,T114,T109,T121,T192,T127"
    procedure_types = "T060,T065,T058,T059,T063,T062,T061"
    device_types = "T203,T074,T075"
    activity_types = "T052,T053,T056,T051,T064,T055,T066,T057,T054"
    return drug_types, procedure_types, device_types, activity_types


# configure the spacy
def spacy_config():
    # use en_core_sci_lg model : A full spaCy pipeline for biomedical data
    nlp = spacy.load("en_core_sci_lg")

    # add a pipeline to detect the abbreviations:
    # The AbbreviationDetector is a Spacy component which implements the
    # abbreviation detection algorithm in "A simple algorithm for identifying abbreviation
    # definitions in biomedical text.", (Schwartz & Hearst, 2003).
    nlp.add_pipe("abbreviation_detector")
    return nlp
