import re

import xml.etree.ElementTree as ET
from typing import Optional

def parse_xml(xml_string: str) -> dict:
    xml_string = xml_string.strip()
    xml_string = f"<root>{xml_string}</root>"
    root = ET.fromstring(xml_string)
    
    def parse_element(element: ET.Element) -> Optional[dict]:
        if len(element) == 0:
            if element.text is None:
                return None
            else:
                return element.text.strip()
        else:
            result = {}
            for child in element:
                child_result = parse_element(child)
                if child_result is not None:
                    if child_result != "None":
                        result[child.tag] = child_result
                    else:
                        result[child.tag] = None
            return result
    
    return parse_element(root)


def extract_language_and_code(markdown_string):
    # Updated pattern to capture the language name after the first set of backticks
    pattern = re.compile(r"```(\w+)\n(.*?)```", re.DOTALL)
    match = pattern.search(markdown_string)
    if match:
        # Return a 2-tuple containing the language name and the code
        return match.group(1), match.group(2)
    else:
        return None

