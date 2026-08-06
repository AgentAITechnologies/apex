import json
import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from agents.agent_manager.agent_manager import AgentManager
from utils.files import (
    clear_persistent_notes,
    get_persistent_notes_file_path,
    overwrite_persistent_notes,
    read_persistent_notes,
    write_persistent_note,
)


class DebugTUI:
    def __init__(self) -> None:
        self.console = Console()

    def run(self) -> None:
        while True:
            self.console.clear()
            self.console.print(
                Panel.fit(
                    "[bold cyan]APEX Interactive Debugger TUI[/bold cyan]\n"
                    "[dim]Manage persistent notes, vector store, agent registry, and conversation history[/dim]",
                    border_style="cyan",
                )
            )

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Option", style="bold yellow", width=8)
            table.add_column("Category", style="bold white")
            table.add_column("Description", style="dim")

            table.add_row("1", "Persistent Notes", "Display, modify, or clear persistent notes XML")
            table.add_row("2", "Vector Store", "Display, modify, or clear Chroma vector store contents")
            table.add_row("3", "Agent Registry", "Display, modify, or clear registered agents and tasks")
            table.add_row("4", "Conversation History", "Display, modify, or clear agent conversation histories")
            table.add_row("5", "Exit Debugger", "Return to APEX prompt")

            self.console.print(table)
            choice = Prompt.ask(
                "\n[bold green]Select an option[/bold green]",
                choices=["1", "2", "3", "4", "5"],
                default="5",
            )

            if choice == "1":
                self.manage_persistent_notes()
            elif choice == "2":
                self.manage_vector_store()
            elif choice == "3":
                self.manage_agent_registry()
            elif choice == "4":
                self.manage_conversation_history()
            elif choice == "5":
                self.console.print("[yellow]Exiting Debug TUI...[/yellow]\n")
                break

    def manage_persistent_notes(self) -> None:
        while True:
            self.console.clear()
            notes_path = get_persistent_notes_file_path()
            content = read_persistent_notes()

            self.console.print(Panel(f"[bold]Persistent Notes File:[/bold] {notes_path}", border_style="blue"))

            if content.strip():
                syntax = Syntax(content, "xml", theme="monokai", line_numbers=True)
                self.console.print(Panel(syntax, title="Current Persistent Notes", border_style="green"))
            else:
                self.console.print(
                    Panel("[italic yellow]Persistent notes are currently empty.[/italic yellow]", border_style="yellow")
                )

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Option", style="bold yellow", width=8)
            table.add_column("Action")
            table.add_row("1", "Display Notes (Raw)")
            table.add_row("2", "Modify Notes (Append Snippet)")
            table.add_row("3", "Modify Notes (Overwrite Entirely)")
            table.add_row("4", "Clear Notes")
            table.add_row("5", "Back to Main Menu")

            self.console.print(table)
            choice = Prompt.ask(
                "[bold green]Select action[/bold green]",
                choices=["1", "2", "3", "4", "5"],
                default="5",
            )

            if choice == "1":
                self.console.clear()
                self.console.print("[bold cyan]--- Raw Persistent Notes ---[/bold cyan]")
                self.console.print(content)
                Prompt.ask("\nPress Enter to continue")
            elif choice == "2":
                new_note = Prompt.ask("\n[bold]Enter XML note snippet to append[/bold]")
                if new_note.strip():
                    write_persistent_note(new_note)
                    self.console.print("[green]Note appended successfully![/green]")
                    Prompt.ask("Press Enter to continue")
            elif choice == "3":
                self.console.print(
                    "\n[yellow]Enter new content for persistent notes. Leave empty to cancel.[/yellow]"
                )
                new_content = Prompt.ask("[bold]New Content[/bold]", default="")
                if new_content.strip():
                    overwrite_persistent_notes(new_content)
                    self.console.print("[green]Persistent notes overwritten successfully![/green]")
                    Prompt.ask("Press Enter to continue")
            elif choice == "4":
                if Confirm.ask("[bold red]Are you sure you want to clear persistent notes?[/bold red]"):
                    clear_persistent_notes()
                    self.console.print("[green]Persistent notes cleared![/green]")
                    Prompt.ask("Press Enter to continue")
            elif choice == "5":
                break

    def _get_vector_store(self):
        try:
            from langchain_community.embeddings import FastEmbedEmbeddings
            from langchain_chroma import Chroma

            output_dir = os.environ.get("OUTPUT_DIR", "data/output/")
            os.makedirs(output_dir, exist_ok=True)
            persist_directory = os.path.join(output_dir, "local_vector_store")

            embeddings = FastEmbedEmbeddings()
            vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
            return vector_store, persist_directory
        except Exception as e:
            self.console.print(f"[red]Error initializing vector store: {e}[/red]")
            return None, None

    def manage_vector_store(self) -> None:
        while True:
            self.console.clear()
            vector_store, persist_directory = self._get_vector_store()
            if not vector_store:
                Prompt.ask("Press Enter to return")
                break

            self.console.print(Panel(f"[bold]Vector Store Directory:[/bold] {persist_directory}", border_style="blue"))

            data = vector_store.get()
            ids = data.get("ids", [])
            documents = data.get("documents", [])
            metadatas = data.get("metadatas", [])

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Index", style="bold yellow", width=6)
            table.add_column("ID", style="cyan", width=20)
            table.add_column("Document Content Preview", style="white")
            table.add_column("Metadata", style="dim")

            for i, doc_id in enumerate(ids):
                doc_text = documents[i] if i < len(documents) else ""
                preview = (doc_text[:60] + "...") if len(doc_text) > 60 else doc_text
                preview = preview.replace("\n", " ")
                meta_str = str(metadatas[i]) if i < len(metadatas) else "{}"
                if len(meta_str) > 40:
                    meta_str = meta_str[:37] + "..."
                table.add_row(str(i + 1), doc_id, preview, meta_str)

            if not ids:
                self.console.print("[italic yellow]Vector store is currently empty.[/italic yellow]")
            else:
                self.console.print(table)

            action_table = Table(show_header=True, header_style="bold magenta")
            action_table.add_column("Option", style="bold yellow", width=8)
            action_table.add_column("Action")
            action_table.add_row("1", "Display Full Document Entry")
            action_table.add_row("2", "Modify Document Entry")
            action_table.add_row("3", "Add New Document Entry")
            action_table.add_row("4", "Clear Vector Store")
            action_table.add_row("5", "Back to Main Menu")

            self.console.print(action_table)
            choice = Prompt.ask(
                "[bold green]Select action[/bold green]",
                choices=["1", "2", "3", "4", "5"],
                default="5",
            )

            if choice == "1":
                if not ids:
                    self.console.print("[yellow]No documents to display.[/yellow]")
                    Prompt.ask("Press Enter to continue")
                    continue
                idx_str = Prompt.ask("Enter document Index to display", default="1")
                if idx_str.isdigit() and 1 <= int(idx_str) <= len(ids):
                    idx = int(idx_str) - 1
                    self.console.clear()
                    self.console.print(f"[bold cyan]ID:[/bold cyan] {ids[idx]}")
                    self.console.print(
                        Panel(documents[idx] if idx < len(documents) else "", title="Page Content")
                    )
                    self.console.print(
                        Panel(
                            json.dumps(metadatas[idx], indent=2) if idx < len(metadatas) else "{}",
                            title="Metadata",
                        )
                    )
                    Prompt.ask("Press Enter to continue")
            elif choice == "2":
                if not ids:
                    self.console.print("[yellow]No documents to modify.[/yellow]")
                    Prompt.ask("Press Enter to continue")
                    continue
                idx_str = Prompt.ask("Enter document Index to modify", default="1")
                if idx_str.isdigit() and 1 <= int(idx_str) <= len(ids):
                    idx = int(idx_str) - 1
                    target_id = ids[idx]
                    current_doc = documents[idx] if idx < len(documents) else ""
                    current_meta = metadatas[idx] if idx < len(metadatas) else {}

                    new_doc = Prompt.ask("New Document Content (press Enter to keep current)", default=current_doc)
                    new_meta_str = Prompt.ask(
                        "New Metadata JSON (press Enter to keep current)", default=json.dumps(current_meta)
                    )

                    try:
                        new_meta = json.loads(new_meta_str)
                    except Exception:
                        new_meta = current_meta

                    try:
                        from langchain_core.documents import Document

                        vector_store.delete(ids=[target_id])
                        doc = Document(page_content=new_doc, metadata=new_meta, id=target_id)
                        vector_store.add_documents([doc], ids=[target_id])
                        self.console.print("[green]Document updated successfully![/green]")
                    except Exception as e:
                        self.console.print(f"[red]Error updating document: {e}[/red]")
                    Prompt.ask("Press Enter to continue")
            elif choice == "3":
                new_doc = Prompt.ask("Enter Document Content")
                meta_json_str = Prompt.ask("Enter Metadata JSON", default="{}")
                try:
                    new_meta = json.loads(meta_json_str)
                except Exception:
                    new_meta = {}
                if new_doc.strip():
                    try:
                        from langchain_core.documents import Document

                        doc = Document(page_content=new_doc, metadata=new_meta)
                        vector_store.add_documents([doc])
                        self.console.print("[green]New document added successfully![/green]")
                    except Exception as e:
                        self.console.print(f"[red]Error adding document: {e}[/red]")
                    Prompt.ask("Press Enter to continue")
            elif choice == "4":
                if Confirm.ask("[bold red]Are you sure you want to clear ALL vector store contents?[/bold red]"):
                    if ids:
                        vector_store.delete(ids=ids)
                    self.console.print("[green]Vector store cleared![/green]")
                    Prompt.ask("Press Enter to continue")
            elif choice == "5":
                break

    def manage_agent_registry(self) -> None:
        while True:
            self.console.clear()
            agent_mgr = AgentManager()
            agents = agent_mgr.agents

            self.console.print(Panel(f"[bold]Registered Agents Count:[/bold] {len(agents)}", border_style="blue"))

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Index", style="bold yellow", width=6)
            table.add_column("Name", style="bold cyan")
            table.add_column("Class", style="green")
            table.add_column("Description")
            table.add_column("Tasks Count", style="magenta")
            table.add_column("Created At", style="dim")

            for i, agent in enumerate(agents):
                name = getattr(agent, "name", "Unnamed")
                cls_name = agent.__class__.__name__
                desc = getattr(agent, "description", "")
                if len(desc) > 40:
                    desc = desc[:37] + "..."
                tasks = getattr(agent, "tasks", [])
                created_at = getattr(agent, "created_at", "-")
                table.add_row(str(i + 1), name, cls_name, desc, str(len(tasks)), created_at)

            self.console.print(table)

            action_table = Table(show_header=True, header_style="bold magenta")
            action_table.add_column("Option", style="bold yellow", width=8)
            action_table.add_column("Action")
            action_table.add_row("1", "Display Agent Details")
            action_table.add_row("2", "Modify Agent Info / Tasks")
            action_table.add_row("3", "Clear Agent Registry")
            action_table.add_row("4", "Back to Main Menu")

            self.console.print(action_table)
            choice = Prompt.ask(
                "[bold green]Select action[/bold green]", choices=["1", "2", "3", "4"], default="4"
            )

            if choice == "1":
                if not agents:
                    self.console.print("[yellow]No agents registered.[/yellow]")
                    Prompt.ask("Press Enter to continue")
                    continue
                idx_str = Prompt.ask("Enter Agent Index to view", default="1")
                if idx_str.isdigit() and 1 <= int(idx_str) <= len(agents):
                    idx = int(idx_str) - 1
                    ag = agents[idx]
                    self.console.clear()
                    self.console.print(
                        Panel(
                            f"[bold]Name:[/bold] {getattr(ag, 'name', '')}\n"
                            f"[bold]Class:[/bold] {ag.__class__.__name__}\n"
                            f"[bold]Created At:[/bold] {getattr(ag, 'created_at', '')}\n"
                            f"[bold]Updated At:[/bold] {getattr(ag, 'updated_at', '')}\n"
                            f"[bold]Description:[/bold] {getattr(ag, 'description', '')}\n"
                            f"[bold]Tasks:[/bold] {json.dumps(getattr(ag, 'tasks', []), indent=2)}",
                            title=f"Agent #{idx + 1} Details",
                            border_style="cyan",
                        )
                    )
                    Prompt.ask("Press Enter to continue")
            elif choice == "2":
                if not agents:
                    self.console.print("[yellow]No agents registered.[/yellow]")
                    Prompt.ask("Press Enter to continue")
                    continue
                idx_str = Prompt.ask("Enter Agent Index to modify", default="1")
                if idx_str.isdigit() and 1 <= int(idx_str) <= len(agents):
                    idx = int(idx_str) - 1
                    ag = agents[idx]

                    new_name = Prompt.ask("New Agent Name (press Enter to keep current)", default=getattr(ag, "name", ""))
                    new_desc = Prompt.ask("New Agent Description (press Enter to keep current)", default=getattr(ag, "description", ""))

                    ag.name = new_name
                    ag.description = new_desc

                    if Confirm.ask("Do you want to add a new task to this agent?"):
                        task_desc = Prompt.ask("Task Description")
                        if task_desc.strip():
                            ag.add_task({"task": task_desc})

                    if Confirm.ask("Do you want to clear tasks for this agent?"):
                        ag.tasks = []

                    agent_mgr.save_agents()
                    self.console.print("[green]Agent updated successfully![/green]")
                    Prompt.ask("Press Enter to continue")
            elif choice == "3":
                if Confirm.ask("[bold red]Are you sure you want to clear the Agent Registry?[/bold red]"):
                    agent_mgr.agents.clear()
                    agent_mgr.save_agents()
                    self.console.print("[green]Agent Registry cleared![/green]")
                    Prompt.ask("Press Enter to continue")
            elif choice == "4":
                break

    def _get_agent_memory(self, agent: Any) -> Optional[Any]:
        if hasattr(agent, "memory") and agent.memory is not None:
            return agent.memory
        elif hasattr(agent, "unified_memory") and agent.unified_memory is not None:
            return agent.unified_memory
        return None

    def manage_conversation_history(self) -> None:
        while True:
            self.console.clear()
            agent_mgr = AgentManager()
            agents = agent_mgr.agents

            if not agents:
                self.console.print(
                    Panel("[italic yellow]No agents registered in AgentManager.[/italic yellow]", border_style="yellow")
                )
                Prompt.ask("Press Enter to return")
                break

            self.console.print(
                Panel("[bold]Select an Agent to view/modify conversation history[/bold]", border_style="blue")
            )

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Option", style="bold yellow", width=8)
            table.add_column("Agent Name", style="bold cyan")
            table.add_column("Messages Count", style="magenta")

            for i, ag in enumerate(agents):
                mem = self._get_agent_memory(ag)
                msg_count = len(mem.conversation_history) if mem else 0
                table.add_row(str(i + 1), getattr(ag, "name", f"Agent_{i}"), str(msg_count))

            table.add_row("ALL", "Clear ALL Agents' Conversation History", "-")
            table.add_row("B", "Back to Main Menu", "-")

            self.console.print(table)
            choice = Prompt.ask("[bold green]Select option[/bold green]", default="B")

            if choice.upper() == "B":
                break
            elif choice.upper() == "ALL":
                if Confirm.ask("[bold red]Are you sure you want to clear conversation history for ALL agents?[/bold red]"):
                    for ag in agents:
                        mem = self._get_agent_memory(ag)
                        if mem:
                            mem.conversation_history.clear()
                    self.console.print("[green]All conversation histories cleared![/green]")
                    Prompt.ask("Press Enter to continue")
            elif choice.isdigit() and 1 <= int(choice) <= len(agents):
                idx = int(choice) - 1
                self._manage_single_agent_history(agents[idx])

    def _manage_single_agent_history(self, agent: Any) -> None:
        mem = self._get_agent_memory(agent)
        if not mem:
            self.console.print("[red]Selected agent does not have a memory instance.[/red]")
            Prompt.ask("Press Enter to continue")
            return

        while True:
            self.console.clear()
            history = mem.conversation_history
            ag_name = getattr(agent, "name", "Agent")

            self.console.print(
                Panel(
                    f"[bold]Conversation History for Agent:[/bold] {ag_name} ({len(history)} messages)",
                    border_style="blue",
                )
            )

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Index", style="bold yellow", width=6)
            table.add_column("Role", style="bold green", width=12)
            table.add_column("Content Preview", style="white")
            table.add_column("Timestamp", style="dim", width=20)

            for i, msg in enumerate(history):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                ts = msg.get("timestamp", "-")
                preview = (content[:80] + "...") if len(content) > 80 else content
                preview = preview.replace("\n", " ")
                table.add_row(str(i + 1), role, preview, ts)

            if not history:
                self.console.print("[italic yellow]Conversation history is currently empty.[/italic yellow]")
            else:
                self.console.print(table)

            action_table = Table(show_header=True, header_style="bold magenta")
            action_table.add_column("Option", style="bold yellow", width=8)
            action_table.add_column("Action")
            action_table.add_row("1", "Display Full Message")
            action_table.add_row("2", "Modify Message")
            action_table.add_row("3", "Append New Message")
            action_table.add_row("4", "Clear History for this Agent")
            action_table.add_row("5", "Back")

            self.console.print(action_table)
            act = Prompt.ask("[bold green]Select action[/bold green]", choices=["1", "2", "3", "4", "5"], default="5")

            if act == "1":
                if not history:
                    self.console.print("[yellow]No messages to display.[/yellow]")
                    Prompt.ask("Press Enter to continue")
                    continue
                m_idx = Prompt.ask("Enter message index to view", default="1")
                if m_idx.isdigit() and 1 <= int(m_idx) <= len(history):
                    msg = history[int(m_idx) - 1]
                    self.console.clear()
                    self.console.print(
                        Panel(
                            f"[bold]Role:[/bold] {msg.get('role')}\n"
                            f"[bold]Timestamp:[/bold] {msg.get('timestamp', '-')}\n\n"
                            f"[bold]Content:[/bold]\n{msg.get('content')}",
                            title=f"Message #{m_idx}",
                            border_style="cyan",
                        )
                    )
                    Prompt.ask("Press Enter to continue")
            elif act == "2":
                if not history:
                    self.console.print("[yellow]No messages to modify.[/yellow]")
                    Prompt.ask("Press Enter to continue")
                    continue
                m_idx = Prompt.ask("Enter message index to modify", default="1")
                if m_idx.isdigit() and 1 <= int(m_idx) <= len(history):
                    msg = history[int(m_idx) - 1]
                    new_role = Prompt.ask("New Role (user/assistant/system)", default=msg.get("role", "user"))
                    new_content = Prompt.ask("New Content (press Enter to keep current)", default=msg.get("content", ""))
                    msg["role"] = new_role
                    msg["content"] = new_content
                    self.console.print("[green]Message updated successfully![/green]")
                    Prompt.ask("Press Enter to continue")
            elif act == "3":
                new_role = Prompt.ask("Role (user/assistant/system)", default="user")
                new_content = Prompt.ask("Content")
                if new_content.strip():
                    mem.add_msg({"role": new_role, "content": new_content})
                    self.console.print("[green]Message appended successfully![/green]")
                    Prompt.ask("Press Enter to continue")
            elif act == "4":
                if Confirm.ask(f"[bold red]Clear history for agent '{ag_name}'?[/bold red]"):
                    history.clear()
                    self.console.print("[green]Conversation history cleared![/green]")
                    Prompt.ask("Press Enter to continue")
            elif act == "5":
                break


def launch_debug_tui() -> None:
    tui = DebugTUI()
    tui.run()