import json
import os
import xml.etree.ElementTree as ET
from typing import Optional
import requests

from rich import print
from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document

from utils.console_io import debug_print as dprint
from utils.parsing import dict2xml, xml2xmlstr, escape_xml

PRINT_PREFIX = "[bold][FEEDBACK][/bold]"


def stage_experience(log: dict) -> Optional[requests.Response]:
    LOCAL_EXPERIENCES = os.environ.get("LOCAL_EXPERIENCES", "False").lower() == "true"
    if LOCAL_EXPERIENCES:
        output_dir = os.environ.get("OUTPUT_DIR", "data/output/")
        os.makedirs(output_dir, exist_ok=True)
        persist_directory = os.path.join(output_dir, "local_vector_store")

        embeddings = FastEmbedEmbeddings()
        vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings
        )

        task_content = log.get("task", "")
        is_valid_xml = False

        if task_content and isinstance(task_content, str):
            try:
                ET.fromstring(task_content)
                is_valid_xml = True
            except ET.ParseError:
                is_valid_xml = False

        if not is_valid_xml:
            try:
                xml_elem = dict2xml(log, tag="experience")
                task_content = xml2xmlstr(xml_elem, no_root=False)
            except Exception:
                task_content = f"<experience>{escape_xml(str(log))}</experience>"

        metadata = {}
        for k, v in log.items():
            if isinstance(v, (str, int, float, bool)):
                metadata[k] = v
            elif v is None:
                metadata[k] = ""
            else:
                metadata[k] = json.dumps(v)

        doc = Document(page_content=task_content, metadata=metadata)

        dprint(f"{PRINT_PREFIX} [DEBUG] Storing experience to local vector store at {persist_directory}:")
        dprint(f"{PRINT_PREFIX} [DEBUG] Page Content (XML):\n{task_content}")
        dprint(f"{PRINT_PREFIX} [DEBUG] Metadata:\n{metadata}")

        vector_store.add_documents([doc])
        print(f"[green]{PRINT_PREFIX} Indexed experience into local vector DB at {persist_directory}[/green]")
        return None

    AGENTAI_API_URL = os.environ.get("AGENTAI_API_URL")
    AGENTAI_API_KEY = os.environ.get("AGENTAI_API_KEY")

    if AGENTAI_API_URL:
        if AGENTAI_API_KEY:
            headers = {
                'Authorization': AGENTAI_API_KEY
            }

            dprint(f"{PRINT_PREFIX} [DEBUG] Storing experience via remote API at {AGENTAI_API_URL}/experience:")
            dprint(f"{PRINT_PREFIX} [DEBUG] Payload:\n{log}")

            response = requests.post(f"{AGENTAI_API_URL}/experience",
                                     headers=headers,
                                     json=log)
            
            return response
        else:
            print(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_KEY not set in .env - unable to log task trace[/red][/bold]")
            return None
    else:
        print(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_URL not set in .env - unable to log task trace[/red][/bold]")
        return None


def get_experiences(target_vector_name: str, target_vector_query: str, limit: int) -> Optional[list[dict] | dict]:
    LOCAL_EXPERIENCES = os.environ.get("LOCAL_EXPERIENCES", "False").lower() == "true"
    if LOCAL_EXPERIENCES:
        output_dir = os.environ.get("OUTPUT_DIR", "data/output/")
        os.makedirs(output_dir, exist_ok=True)
        persist_directory = os.path.join(output_dir, "local_vector_store")

        embeddings = FastEmbedEmbeddings()
        vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings
        )

        try:
            dprint(f"{PRINT_PREFIX} [DEBUG] Querying local vector store at {persist_directory} for: '{target_vector_query}' (limit={limit})")
            results = vector_store.similarity_search(target_vector_query, k=limit)
            experiences = []
            for doc in results:
                dprint(f"{PRINT_PREFIX} [DEBUG] Loaded document content:\n{doc.page_content}")
                dprint(f"{PRINT_PREFIX} [DEBUG] Loaded document metadata:\n{doc.metadata}")
                if doc.metadata:
                    experiences.append(doc.metadata)

            dprint(f"{PRINT_PREFIX} [DEBUG] Total local experiences retrieved: {len(experiences)}")
            return experiences
        except Exception as e:
            print(f"[yellow]{PRINT_PREFIX} Query on local vector store returned error: {e}[/yellow]")
            return []

    AGENTAI_API_URL = os.environ.get("AGENTAI_API_URL")
    AGENTAI_API_KEY = os.environ.get("AGENTAI_API_KEY")

    if AGENTAI_API_URL:
        if AGENTAI_API_KEY:
            query = {
                'target_vector_name': target_vector_name,
                'target_vector_query': target_vector_query,
                'limit': limit
            }
            headers = {
                'Authorization': AGENTAI_API_KEY
            }

            dprint(f"{PRINT_PREFIX} [DEBUG] Querying remote API at {AGENTAI_API_URL}/experience with:\n{query}")

            response = requests.get(f"{AGENTAI_API_URL}/experience",
                                    headers=headers,
                                    json=query)

            res_data = response.json()
            dprint(f"{PRINT_PREFIX} [DEBUG] Remote API response:\n{res_data}")
            return res_data
        else:
            print(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_KEY not set in .env - unable to retrieve task trace[/red][/bold]")
    else:
        print(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_URL not set in .env - unable to retrieve task trace[/red][/bold]")


def get_remote_experiences(target_vector_name: str, target_vector_query: str, limit: int) -> Optional[str]:
    experiences = get_experiences(target_vector_name, target_vector_query, limit)

    if isinstance(experiences, dict) and "request_deny_reason" in experiences and "message" in experiences:
        print(f"[red][bold]{PRINT_PREFIX} {experiences['message']}[/bold][/red]")
        exit(1)

    if experiences:
        if isinstance(experiences, dict) and "error" in experiences:
            print(f"[red][bold]{PRINT_PREFIX} Error retrieving remote experiences: {experiences}[/red][/bold]")
            return None
        else:
            result = ""
            
            for i, experience in enumerate(experiences):
                result += f"<example idx={i+1}>\n\n"

                result += experience.get('task', '') + "\n"
                result += f"<os_type>{experience.get('os_family', '')}</os_type>" + "\n"

                result += experience.get('trace', '') + "\n"

                result += f"<human_feedback>\n"
                result += experience.get('feedback', '') + "\n"
                result += "</human_feedback>\n"
                result += f"<agent_reflection>\n"
                result += experience.get('elaboration', '') + "\n"
                result += "</agent_reflection>\n\n"

                result += "</example>\n"
            
            dprint(f"{PRINT_PREFIX} [DEBUG] Formatted experience examples string:\n{result}")
            return result

    else:
        # TODO: log this as an error depending on telemetry level
        print(f"[red][bold]{PRINT_PREFIX} No remote experiences found[/red][/bold]")
        return None