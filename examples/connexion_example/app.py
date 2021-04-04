"""Example usage of `connexion`.

Taken from (https://github.com/hjacobs/connexion-example/blob/master/app.py).
"""

import os
from typing import Optional, Dict, List, Any, Tuple, Union
import datetime
import logging
from pathlib import Path

import connexion
from connexion import NoContent

from .ex import open_bldr

Pet = Dict[str, Any]
Response = Tuple[str, int]

PETS: Dict[str, Pet] = {}


def get_pets(
    limit: int,
    animal_type: Optional[str] = None
) -> Dict[str, List[Pet]]:
    return {
        'pets': [
            pet for pet in PETS.values()
            if animal_type is None or
            pet['animal_type'] == animal_type[:limit]
        ]
    }


def get_pet(pet_id: str) -> Union[Pet, Response]:
    return PETS.get(pet_id, False) or ('Not found', 404)


def put_pet(pet_id: str, pet: Pet) -> Response:
    exists = pet_id in PETS
    pet['id'] = pet_id

    if exists:
        logging.info(f'Updating pet {pet_id}..')
        PETS[pet_id].update(pet)
    else:
        logging.info(f'Creating pet {pet_id}..')
        pet['created'] = datetime.datetime.utcnow()
        PETS[pet_id] = pet
    return NoContent, (200 if exists else 201)


def delete_pet(pet_id: str) -> Response:
    if pet_id in PETS:
        logging.info(f'Deleting pet {pet_id}..')
        del PETS[pet_id]
        return NoContent, 204
    else:
        return NoContent, 404

logging.basicConfig(level=logging.INFO)
app = connexion.App(__name__)
swagger_dir = os.path.abspath('./connexion_example')
swagger_path = Path(swagger_dir) / 'swagger.json'
if not swagger_path.is_file():
    with open(swagger_path, 'w') as f:
        f.write(open_bldr.build.json(indent=2))
app.add_api('swagger.json')
application = app.app

if __name__ == '__main__':
    app.run(port=8080, server='gevent')
