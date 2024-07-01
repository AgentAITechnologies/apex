from typing import Optional

import glob
import os
import re

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

from rich import print

from utils.enums import Role
from utils.llm import llm_turn
from utils.custom_types import NestedStrDict

from agents.prompt_management import get_msg

from anthropic import Anthropic


PRINT_PREFIX = "[bold][Parsing][/bold]"


def files2dict(path: str, extension: str) -> dict[str, str]:
    retval = {}

    source_files = glob.glob(os.path.join(path, f'*{extension}'))

    for source_file in source_files:
        with open(source_file, 'r') as f:
            retval[os.path.basename(source_file).replace(extension, "")] = f.read()

    return retval

def xmlstr2dict(xml_string: str, client: Anthropic, depth: int = 0) -> dict:
    try:
        xml_string = xml_string.strip()
        xml_string = f"<root>{xml_string}</root>"
        root = ET.fromstring(xml_string)

    except ET.ParseError:
        if depth < 6:
            print(f"{PRINT_PREFIX} [yellow][bold]Error parsing XML:\n{xml_string}[/bold][/yellow]")
            print(f"{PRINT_PREFIX} [yellow][bold]Attempting fix...[/bold][/yellow]")

            system_prompt = """You are an expert in the field of programming, and are especially good at finding mistakes XML files.
    Make sure there are no mistakes in the XML file, such as invalid characters, missing or unclosed tags, etc.
    You may also want to make sure that the XML file is well-formed.
    Make sure the tag pairs that were given remain and are balanced.
    If there are any singleton tags, you should close them or replace them with an equivalent description."""
            user_prompt = f"Fix the following XML file according to the given instructions. Be especially vigilant for singleton tags:\n{xml_string}\n"
            
            assistant_prompt = "<root>"
            stop_seq = "</root>"

            messages = [get_msg(Role.USER, user_prompt), get_msg(Role.ASSISTANT, assistant_prompt)]

            fixed_xml = llm_turn(client=client,
                                prompts={"system": system_prompt,
                                        "messages": messages},
                                stop_sequences=[stop_seq],
                                temperature=1.0)

            return xmlstr2dict(fixed_xml, client, depth + 1)
        else:
            print(f"{PRINT_PREFIX} [red][bold]Error parsing XML, and fix attempt limit of {depth+1} reached:\n{xml_string}[/bold][/red]")
            exit(1)
    
    def parse_element(element: ET.Element) -> Optional[dict] | Optional[str]:
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
    
    result = parse_element(root)
    if isinstance(result, dict):
        return result
    else:
        print(f"[red][bold]{PRINT_PREFIX} root element evaluated to {type(result)}, expected dict")
        exit(1)

def dict2xml(d: NestedStrDict, tag: str="root") -> Element:
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

def xml2xmlstr(xml: Element, no_root: bool=True) -> str:
    def extract_root_xmlstr(xml_str: str, root_str):
        xml_str = xml_str.strip()
        open_tag, close_tag = f"<{root_str}>", f"</{root_str}>"

        match = xml_str[xml_str.find(open_tag)+len(open_tag):xml_str.find(close_tag)]

        return match.strip()
    
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

def get_yes_no_input(prompt: str, rich_open: str = "", rich_close: str = "") -> bool:
    if bool(rich_open) ^ bool(rich_close):
        print(f"[red][bold]{PRINT_PREFIX} Only one parameter passed for rich (needs eith both rich_open and rich_close, or neither)[/bold][/red]")
        exit(1)

    while True:
        user_input = input(prompt + " (y/n): ").lower().strip()
        if user_input in ['y', 'yes']:
            return True
        elif user_input in ['n', 'no']:
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")