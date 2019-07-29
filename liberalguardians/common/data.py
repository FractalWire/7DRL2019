from __future__ import annotations
import logging
import json

from liberalguardians.common.logging import StyleAdapter

logger = StyleAdapter(logging.getLogger(__name__))

logger.info("data initialisation")
logger.debug("Loading game data : started")

img_dir = "data/img"

# OBSOLETE
# portrait_size = 256

# TODO: change json -> yaml, more readable/editable
with open('data/ranks.json') as f:
    ranks = json.load(f)

with open("data/professions.json") as f:
    professions = json.load(f)

with open("data/locations.json") as f:
    locations = json.load(f)

with open('data/areas.json') as f:
    areas = json.load(f)

with open('data/interactions.json') as f:
    interactions = json.load(f)

logger.debug("Loading game data : done")
