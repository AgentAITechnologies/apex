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

def get_experience(target_vector_name: str, target_vector_query: str, limit: int):
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