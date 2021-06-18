# Intervention_Normalizer

An automated pipeline to normalize complex interventions into the computable representation to enable structured queries. 

## Prerequest
1. Install 'QuickUMLS' locally. Reference: https://github.com/Georgetown-IR-Lab/QuickUMLS
2. Install 'scispaCy' locally. Reference: https://github.com/allenai/scispacy. Note that the pre-trained model we use is "en_core_sci_lg". Make sure to follow the guidance in Reference to download this model. We also use the abbreviation component, be sure to add this component. 
3. Check 'package-list.txt' for the full packages list.

## Example
input:

    "brodalumab 210 mg every 2 weeks after receiving ustekinumab through 52 weeks"
    
output:

```
{
    "file_id": "10010",
    "start": "285",
    "end": "297",
    "text": "brodalumab 210 mg every 2 weeks after receiving ustekinumab through 52 weeks",
    "has_drug": [
        {
            "text": "brodalumab",
            "maps_to": "C3491331:brodalumab",
            "start": 0,
            "end": 10,
            "has_strength": [
                "210 mg"
            ],
            "has_frequency": [
                "every 2 weeks"
            ],
            "has_negation": "affirmed"
        },
        {
            "text": "ustekinumab",
            "maps_to": "C1608841:ustekinumab",
            "start": 48,
            "end": 59,
            "has_duration": [
                "52 weeks"
            ],
            "has_negation": "affirmed"
        }
    ],
    "has_relation": "before (C1608841->C3491331)"
}
```


    
