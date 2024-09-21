import os
import shutil
from dotenv import load_dotenv, set_key
from rich.console import Console
from rich.prompt import Prompt

console = Console()

def setup_env():
    template_file = '.env.template'
    env_file = '.env'

    # Check if .env.template exists
    if not os.path.exists(template_file):
        console.print(f"[bold red]Error: {template_file} not found in the current directory.[/bold red]")
        return

    # Copy .env.template to .env if .env doesn't exist
    if not os.path.exists(env_file):
        try:
            shutil.copy(template_file, env_file)
            console.print(f"[green]Created {env_file} from {template_file}[/green]")
        except Exception as e:
            console.print(f"[bold red]Error copying file: {str(e)}[/bold red]")
            return
    else:
        console.print(f"[yellow]{env_file} already exists. Updating existing file.[/yellow]")

    # Load the current .env file
    load_dotenv(env_file)

    # Prompt user for Anthropic API key
    api_key = Prompt.ask("Please enter your Anthropic API key").strip()

    try:
        # Update the ANTHROPIC_API_KEY in the .env file
        set_key(env_file, "ANTHROPIC_API_KEY", api_key)
        console.print("[green]Anthropic API key has been updated in the .env file.[/green]")
    except Exception as e:
        console.print(f"[bold red]Error updating API key: {str(e)}[/bold red]")

if __name__ == "__main__":
    setup_env()