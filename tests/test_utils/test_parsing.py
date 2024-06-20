import sys
import os
from xml.etree.ElementTree import Element, tostring

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from utils.parsing import xmlstr2dict, dict2xml
from utils.custom_types import NestedStrDict


@pytest.mark.parametrize("xmlstr, client, expected", [
    ("<response>This is what will be read aloud.</response><action>None</action>", None, { "response": "This is what will be read aloud.", "action": None }),

    ("""<response>Okay, I'll get to writing the story now and email it to tim.jones@mail.com when complete. Is there anything else I can help with?</response>
<action>
<task>Write a short story about a friendly cat and email it</task>
<details>
<story_title>Here Kitty Kitty</story_title>
<recipient_email>tim.jones@mail.com</recipient_email>
</details>
</action>""", None, { "response": "Okay, I'll get to writing the story now and email it to tim.jones@mail.com when complete. Is there anything else I can help with?",
                      "action": { "task": "Write a short story about a friendly cat and email it",
                                 "details": { "story_title": "Here Kitty Kitty",
                                              "recipient_email": "tim.jones@mail.com" } } }),

    ("<response>Sounds good. Talk later!</response><action>REST</action>", None, { "response": "Sounds good. Talk later!", "action": "REST" }),                                         
])
def test_xmlstr2dict(xmlstr, client, expected):
    assert xmlstr2dict(xmlstr, client) == expected

@pytest.mark.parametrize(
    "d, expected_xml, tag",
    [
        (
            {"name": "John", "age": "30"},
            '<root><name>John</name><age>30</age></root>',
            "root",
        ),
        (
            {
                "person": {
                    "name": "John",
                    "age": "30",
                    "address": {
                        "street": "123 Main St",
                        "city": "New York",
                    },
                },
            },
            (
                '<root><person><name>John</name><age>30</age>'
                '<address><street>123 Main St</street><city>New York</city></address>'
                '</person></root>'
            ),
            "root",
        ),
        (
            {},
            '<root />',
            "root",
        ),
        (
            {"name": "John", "age": None},
            '<root><name>John</name><age>None</age></root>',
            "root",
        ),
        (
            {"name": "John", "age": "30"},
            '<person><name>John</name><age>30</age></person>',
            "person",
        ),
    ],
)
def test_dict2xml(d: NestedStrDict, expected_xml: str, tag: str):
    assert tostring(dict2xml(d, tag=tag)).decode() == expected_xml