# KCAT
 A Knowledge-Constraint Typing Annotation Tool

## Entity Linking
download code and data from [Mulrel](https://github.com/lephong/mulrel-nel)

replace the source file "ed_ranker.py" with our file "ed_ranker.py" in directory "EL"
Train the model by

    export PYTHONPATH=$PYTHONPATH:../
    python -u -m nel.main --mode train --n_rels 3 --mulrel_type ment-norm --model_path model

Run the api by

    python elapi.py --model_path model

Test the api in web
input:
    
    http://10.214.155.248:5000/edl/ranking/?text=obama%20is%20america%20president&&offset=0-4
    
result:
    
    [{"start": 0, "end": 4, "surface_form": "obama", "entity": "Barack_Obama"}]
    

## Fined-grain Typing

Requirements: Python 3.5 or 3.6, tkinter

run following command to start annotator client

    python annotation.py --dataset dataset_name
 
    
