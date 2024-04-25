import re

import xml.etree.ElementTree as ET
from typing import Optional

def parse_xml(xml_string: str) -> dict[str, Optional[str]]:
    xml_string = xml_string.strip()
    xml_string = f"<root>{xml_string}</root>"
    root = ET.fromstring(xml_string)
    result = {}
    
    for child in root:
        if child.text is None or child.text.strip() == "None":
            result[child.tag] = None
        else:
            result[child.tag] = child.text.strip()
    
    return result


def extract_language_and_code(markdown_string):
    # Updated pattern to capture the language name after the first set of backticks
    pattern = re.compile(r"```(\w+)\n(.*?)```", re.DOTALL)
    match = pattern.search(markdown_string)
    if match:
        # Return a 2-tuple containing the language name and the code
        return match.group(1), match.group(2)
    else:
        return None

