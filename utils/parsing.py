import re
from typing import Optional, Union

import glob
import os

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

from rich import print

from utils.enums import Role
from utils.llm import llm_turn
from utils.custom_types import NestedStrDict

from agents.prompt_management import get_msg

from anthropic import Anthropic


PRINT_PREFIX = "[bold][Parsing][/bold]"

TOKEN_GROWTH_ALLOWANCE = 128
MAX_TOKENS_ANTHROPIC = 8192


def files2dict(path: str, extension: str) -> dict[str, str]:
    retval = {}

    source_files = glob.glob(os.path.join(path, f'*{extension}'))

    for source_file in source_files:
        with open(source_file, 'r') as f:
            retval[os.path.basename(source_file).replace(extension, "")] = f.read()

    return retval

def escape_xml(text: str) -> str:
    def replace(match):
        char = match.group(0)
        if char == '&': return '&amp;'
        if char == '<': return '&lt;'
        if char == '>': return '&gt;'
        if char == "'": return '&apos;'
        if char == '"': return '&quot;'
    
    # Use negative lookbehind and lookahead to avoid escaping < and > in tags
    pattern = r'(?<!<)([&<>\'""])(?![^<]*>)'
    return re.sub(pattern, replace, text)

def unescape_xml(text: str) -> str:
    return text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&apos;", "'").replace("&quot;", '"')

def xmlstr2dict(xml_string: str, client: Anthropic, depth: int = 0) -> dict:
    def escape_code_blocks(text: str) -> str:
        def escape_block(match):
            return f"```{match.group(1)}\n{escape_xml(match.group(2))}```"
        
        return re.sub(r"```(\w*)\n(.*?)```", escape_block, text, flags=re.DOTALL)

    xml_string = escape_code_blocks(xml_string)

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
                                temperature=1.0,
                                max_tokens=min(len(xml_string) + TOKEN_GROWTH_ALLOWANCE, MAX_TOKENS_ANTHROPIC))

            return xmlstr2dict(fixed_xml, client, depth + 1)
        else:
            error_message = f"Error parsing XML, and fix attempt limit of {depth+1} reached:\n{xml_string}"
            print(f"{PRINT_PREFIX} [red][bold]{error_message}[/bold][/red]")
            raise RecursionError(error_message)
    
    def parse_element(element: ET.Element) -> Union[dict, str, list, None]:
        if len(element) == 0:
            text = element.text.strip() if element.text else None
            return None if text == "None" else text
        
        result = {}
        for child in element:
            child_result = parse_element(child)
            if child.tag in result:
                if isinstance(result[child.tag], list):
                    result[child.tag].append(child_result)
                else:
                    result[child.tag] = [result[child.tag], child_result]
            else:
                result[child.tag] = child_result
        
        if element.attrib:
            result['_attributes'] = {k: (None if v == "None" else v) for k, v in element.attrib.items()}
        
        return result

    return parse_element(root)

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

def get_yes_no_input(prompt: Optional[str] = None, rich_open: str = "", rich_close: str = "", with_cancel: bool = False) -> Optional[bool]:
    if bool(rich_open) ^ bool(rich_close):
        error_message = f"{PRINT_PREFIX} Only one parameter passed for rich (needs either both rich_open and rich_close, or neither)"
        print(f"[red][bold]{error_message}[/bold][/red]")
        raise ValueError(error_message)

    while True:
        if prompt:
            print(rich_open + prompt + rich_close, end=' ')

        user_input = input(f"(y/n{'/c' if with_cancel else ''}) > ").lower().strip()

        if user_input in ['y', 'yes']:
            return True
        elif user_input in ['n', 'no']:
            return False
        elif with_cancel and user_input in ['c', 'cancel']:
            return None
        else:
            print(f"""Invalid input. Please enter 'y' or 'n'{" (or 'c' for 'cancel')" if with_cancel else ''}.""")

def remove_escape_key(string: str) -> str:
    return string.replace('^[', '').replace('\x1b', '')

def format_nested_dict(d, indent=0):
    lines = []
    for key, value in d.items():
        if isinstance(value, dict):
            lines.append('  ' * indent + f"{key}:")
            lines.append(format_nested_dict(value, indent + 1))
        else:
            lines.append('  ' * indent + f"{key}: {value}")
    return '\n'.join(lines)
