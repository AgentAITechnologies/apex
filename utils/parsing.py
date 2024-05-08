import re

import xml.etree.ElementTree as ET
from typing import Optional

def xmlstr2dict(xml_string: str) -> dict:
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
                        result.update(child.attrib)
                    else:
                        result[child.tag] = None
            return result
    
    return parse_element(root)

def dict2xml(d, tag="root"):
    """
    Convert a dictionary with possible nested dictionaries into XML
    """
    elem = ET.Element(tag)
    for key, val in d.items():
        if isinstance(val, dict):
            # If the value is another dictionary, recurse
            child = dict2xml(val, key)
        else:
            # Otherwise, just create an element
            child = ET.Element(key)
            child.text = str(val)
        elem.append(child)
    return elem

def xml2xmlstr(xml, no_root=True):
    def extract_root_xmlstr(xml_str, root_str):
        # Pattern to find content within <root></root>
        pattern = rf"<{root_str}>(.*?)</{root_str}>"
        # Search using the pattern
        match = re.search(pattern, xml_str)
        # Return the matched group if found
        return match.group(1) if match else None
    
    if no_root:
        return extract_root_xmlstr(ET.tostring(xml, encoding="unicode"), xml.tag)
    else:
        return ET.tostring(xml, encoding="unicode")


def extract_language_and_code(markdown_string):
    # Updated pattern to capture the language name after the first set of backticks
    pattern = re.compile(r"```(\w+)\n(.*?)```", re.DOTALL)
    match = pattern.search(markdown_string)
    if match:
        # Return a 2-tuple containing the language name and the code
        return match.group(1), match.group(2)
    else:
        return None
    
def find_missing_format_items(string):
    # Regular expression pattern to match format items not surrounded by extra curly braces
    pattern = r'(?<!\{)\{(\w+)\}(?!\})'

    format_items = re.findall(pattern, string)
    
    if format_items:
        return format_items
    else:
        return None

