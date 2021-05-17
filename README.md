# Intervention_Normalizer

An automated pipeline to normalize complex interventions into the computable representation to enable structured queries. 

## Prerequest
1. Install 'QuickUMLS' locally. Reference: https://github.com/Georgetown-IR-Lab/QuickUMLS
2. Install 'scispaCy' locally. Reference: https://github.com/allenai/scispacy. Note that the pre-trained model we use is "en_core_sci_lg". Make sure to follow the guidance in Reference to download this model. We also use the abbreviation component, be sure to add this component. 
3. Check 'package-list.txt' for the full packages list.
## How to use
1. **Configure the resource, quickUMLS, input and output paths in configure.py.** Note that currently we only support the input data as: a .txt file with the raw abstract text (e.g., 88754.txt, where '88754' is the file id) in combined with an .ann file that include the annotated rew text intervention snippets of this abstract (e.g., 88754.ann, where '88754' is again the file id). The only purpose of having the file abstract text is to extraction the abbreviations for intervention snippets preprocessing. You can find some examples in the *"example/dataset"* folder. The default resource folder is *"resource/"*, input folder is *"example/dataset"*, output folder is *"example/result"*
2. **Run the program.**
```
cd intervention_normalizer
python main.py
```
## Example
input:

    "brodalumab 210 mg every 2 weeks after receiving ustekinumab through 52 weeks"
    
output:

![image](https://user-images.githubusercontent.com/14129718/118528078-eb990a80-b70f-11eb-9185-cd4ad2db000f.png)



    
