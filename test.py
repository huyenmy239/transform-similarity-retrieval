import os
import json

filepath = "data/transformations.json"

if os.path.exists(filepath):
    with open(filepath, "r") as f:
        print (json.load(f))