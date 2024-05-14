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


def extract_language_and_code(markdown_string: str) -> Optional[tuple[str, str]]:
    pattern = re.compile(r"```(\w+)\n(.*?)```", re.DOTALL)
    match = pattern.search(markdown_string)
    if match:
        language_name = match.group(1)
        code = match.group(2)
        return language_name, code
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
    
def strip_step_tags(text):
    pattern = r'<step_\d+>(.*?)</step_\d+>'
    return re.sub(pattern, r'\1', text, flags=re.DOTALL)
    
def extract_steps(xml_string):
    # Pattern matches the text within step tags and the step numbers
    pattern = r"<step_(\d+)>(.*?)</step_\1>"
    # Find all matches in the provided XML string
    matches = re.findall(pattern, xml_string, re.DOTALL)
    # Convert each match to a tuple of (step number as int, step text)
    results = [f"<step_{step}>{text.strip()}</step_{step}>" for step, text in matches]
    return results
    
'''
def extract_steps(xml_string):
    # Pattern matches the text within step tags and the step numbers
    pattern = r"<step_(\d+)>(.*?)</step_\1>"
    # Find all matches in the provided XML string
    matches = re.findall(pattern, xml_string, re.DOTALL)
    # Convert each match to a tuple of (step number as int, step text)
    results = [(int(step), text.strip()) for step, text in matches]
    return results
'''
