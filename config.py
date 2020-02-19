"""File loading all the constants for python use"""

import argparse
import json

CONSTANTS_PATH = "./constants.json"

with open(CONSTANTS_PATH) as f:
    data = json.load(f)

constants = argparse.Namespace(**data)
