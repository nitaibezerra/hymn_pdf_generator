import os
import sys

import yaml
from models import Hymn
from pdf_elements import HymnPDFGenerator


def main(yaml_path: str):
    with open(yaml_path, 'r') as file:
        data = yaml.safe_load(file)

    hymn_book = data['hymn_book']

    intro_name = hymn_book['intro_name']
    name = hymn_book['name']
    owner = hymn_book['owner']

    hymns = [
        Hymn(
            number=hymn.get('number'),
            title=hymn.get('title'),
            style=hymn.get('style'),
            offered_to=hymn.get('offered_to'),
            extra_instructions=hymn.get('extra_instructions'),
            text=hymn.get('text'),
            repetitions=hymn.get('repetitions'),
            received_at=hymn.get('received_at')
        )
        for hymn in hymn_book['hymns']
    ]

    output_filename = os.path.splitext(yaml_path)[0] + ".pdf"

    cover_image_path = os.path.join(os.path.dirname(yaml_path), 
                                    hymn_book['cover_image_path'])
     
    generator = HymnPDFGenerator(hymns, 
                                 output_filename, 
                                 intro_name, 
                                 name, 
                                 owner, 
                                 cover_image_path)
    generator.create_pdf()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_yaml>")
        sys.exit(1)

    yaml_path = sys.argv[1]
    main(yaml_path)
