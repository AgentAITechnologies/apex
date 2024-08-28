import json
import os
from typing import Optional
import requests

from rich import print


PRINT_PREFIX = "[bold][FEEDBACK][/bold]"


def stage_experience(log: dict) -> Optional[requests.Response]:
    AGENTAI_API_URL = os.environ.get("AGENTAI_API_URL")
    AGENTAI_API_KEY = os.environ.get("AGENTAI_API_KEY")

    if AGENTAI_API_URL:
        if AGENTAI_API_KEY:
            headers = {
                'Authorization': AGENTAI_API_KEY
            }

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

            response = requests.get(f"{AGENTAI_API_URL}/experience",
                                    headers=headers,
                                    json=query)

            return response.json()
        else:
            print(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_KEY not set in .env - unable to retrieve task trace[/red][/bold]")
    else:
        print(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_URL not set in .env - unable to retrieve task trace[/red][/bold]")

def get_remote_experiences(target_vector_name: str, target_vector_query: str, limit: int) -> Optional[str]:
    experiences = get_experiences(target_vector_name, target_vector_query, limit)

    if experiences:
        if "error" in experiences:
            print(f"[red][bold]{PRINT_PREFIX} Error retrieving remote experiences: {experiences}[/red][/bold]")
            return None
        else:
            result = ""
            
            for i, experience in enumerate(experiences):
                result += f"<example idx={i+1}>\n\n"

                result += experience['task'] + "\n"
                result += f"<os_type>{experience['os_family']}<os_type>" + "\n"

                result += experience['trace'] + "\n"

                result += f"<human_feedback>\n"
                result += experience['feedback'] + "\n"
                result += "</human_feedback>\n"
                result += f"<agent_reflection>\n"
                result += experience['elaboration'] + "\n"
                result += "</agent_reflection>\n\n"

                result += "</example>\n"
            
            return result

    else:
        # TODO: log this as an error depending on telemetry level
        print(f"[red][bold]{PRINT_PREFIX} No remote experiences found[/red][/bold]")
        return None
