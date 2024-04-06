import re

def extract_language_and_code(markdown_string):
    # Updated pattern to capture the language name after the first set of backticks
    pattern = re.compile(r"```(\w+)\n(.*?)```", re.DOTALL)
    match = pattern.search(markdown_string)
    if match:
        # Return a 2-tuple containing the language name and the code
        return match.group(1), match.group(2)
    else:
        return None


# TODO: Handle N indentation levels
def md2dict(markdown):
    extracted_code = extract_language_and_code(markdown)
    if extracted_code: # detected code block
        language_name, code = extracted_code
        return {
            "code_block": {
                "language_name": language_name,
                "code": code
            }
        }
    else: # no code block detected, interpret as markdown heirarchy
        tree = {}
        current_node = tree
        path = []
        order_idx = 0

        for line in markdown.split('\n'):
            if line.startswith('#'):
                level = line.count('#')
                title = line[level+1:].strip()
                # Adjust the path to the current level
                path = path[:level-1]
                path.append(title)
                # Navigate to the correct position in the tree
                current_node = tree
                for step in path[:-1]:
                    current_node = current_node.setdefault(step, {'_content': ""})
                # Add or update the node
                if title not in current_node:
                    current_node[title] = {'_content': "", "_order": order_idx}
                    order_idx = order_idx + 1
                current_node = current_node[title]
            else:
                if '_content' in current_node:
                    current_node['_content'] = current_node['_content'] + line
                else:
                    current_node['_content'] = line

                if '_order' not in current_node:
                    current_node['_order'] = order_idx
                    order_idx = order_idx + 1

        return tree


def dict2md(result_dict, level=1):
    for key, value in result_dict.items():
        if key != "_content" and key!= "_order":
            print("#"*level + f" {key}")

        if isinstance(value, dict):
            dict2md(value, level=level+1)
        else:
            if value != "" and key != "_order":
                print(f"{value}")


# Only addresses used formatting cases. Will not work correctly for other cases.
def parse_response(response):
    if response.content[0].type == "text":
        parsed_response = md2dict(response.content[0].text)
        return parsed_response
    else:
        print(f"[parse_message] response.content[0].type was not text: {response.content[0].type}")
        return None