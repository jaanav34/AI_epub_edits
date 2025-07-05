# main.py
"""
AI_epub_edits - Main Entry Point

This script orchestrates the entire EPUB rewriting process using a modular,
project-based architecture.

USAGE:
1. Create a new project:
   python main.py new --name "MyBookProject" --epub "/path/to/your/book.epub" --style_ref "/path/to/style.txt"

2. Run the rewriting pipeline:
   python main.py run --name "MyBookProject"
   (Optional: override config)
   python main.py run --name "MyBookProject" --provider openai --model gpt-4o --start 1 --end 5 --max_chapters 3

3. Package the final EPUB:
   python main.py package --name "MyBookProject"

4. Get project status:
   python main.py status --name "MyBookProject"
"""

import argparse
import asyncio
import os
import sys
from core.project_manager import ProjectManager
from core.config_manager import ConfigManager
from core.orchestrator import Orchestrator

def handle_new_project(args):
    """Handles the 'new' command to create a project."""
    if not os.path.exists(args.epub):
        print(f"Error: EPUB file not found at '{args.epub}'")
        sys.exit(1)
    if not os.path.exists(args.style_ref):
        print(f"Error: Style reference file not found at '{args.style_ref}'")
        sys.exit(1)

    print(f"Creating new project '{args.name}'...")
    project = ProjectManager(args.name)
    project.create_new_project(args.epub, args.style_ref)
    print(f"Project created successfully at: {project.project_dir}")
    print("Run 'python main.py run --name \"{args.name}\"' to start processing.")

async def handle_run_project(args):
    """Handles the 'run' command to process a project."""
    project = ProjectManager(args.name)
    if not project.project_exists():
        print(f"Error: Project '{args.name}' not found. Create it first with the 'new' command.")
        sys.exit(1)

    print(f"Running project '{args.name}'...")
    config = ConfigManager()

    # Apply command-line overrides
    overrides = {
        'provider': args.provider,
        'model': args.model,
        'max_chapters_per_run': args.max_chapters
    }
    # Filter out None values so we don't override with nothing
    active_overrides = {k: v for k, v in overrides.items() if v is not None}

    orchestrator = Orchestrator(project, config, active_overrides)
    await orchestrator.run_pipeline(start_chapter=args.start, end_chapter=args.end)
    print(f"Processing run for '{args.name}' complete.")
    print("You can now package the final epub with 'python main.py package --name \"{args.name}\"'")

def handle_package_project(args):
    """Handles the 'package' command to create the final EPUB."""
    project = ProjectManager(args.name)
    if not project.project_exists():
        print(f"Error: Project '{args.name}' not found.")
        sys.exit(1)

    print(f"Packaging final EPUB for project '{args.name}'...")
    project.package_final_epub()
    print(f"Final EPUB created at: {project.get_final_epub_path()}")

def handle_status(args):
    """Handles the 'status' command to show project progress."""
    project = ProjectManager(args.name)
    if not project.project_exists():
        print(f"Error: Project '{args.name}' not found.")
        sys.exit(1)
    
    project.display_status()

def main():
    """Main function to parse arguments and delegate tasks."""
    parser = argparse.ArgumentParser(description="AI_epub_edits: A tool for AI-powered EPUB rewriting.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # 'new' command
    parser_new = subparsers.add_parser("new", help="Create a new rewriting project.")
    parser_new.add_argument("--name", required=True, help="A unique name for the project.")
    parser_new.add_argument("--epub", required=True, help="Path to the source EPUB file.")
    parser_new.add_argument("--style_ref", required=True, help="Path to a .txt file containing the style reference text.")
    parser_new.set_defaults(func=handle_new_project)

    # 'run' command
    parser_run = subparsers.add_parser("run", help="Run the rewriting pipeline on a project.")
    parser_run.add_argument("--name", required=True, help="The name of the project to run.")
    parser_run.add_argument("--provider", help="Override the AI provider (e.g., 'openai').")
    parser_run.add_argument("--model", help="Override the AI model (e.g., 'gpt-4o').")
    parser_run.add_argument("--max_chapters", type=int, help="Limit the number of chapters to process in this run.")
    parser_run.add_argument("--start", type=int, default=1, help="Start chapter number (inclusive)")
    parser_run.add_argument("--end", type=int, default=0, help="End chapter number (inclusive); 0 means 'to the end'")
    parser_run.set_defaults(func=lambda args: asyncio.run(handle_run_project(args)))

    # 'package' command
    parser_package = subparsers.add_parser("package", help="Package the rewritten text into a new EPUB file.")
    parser_package.add_argument("--name", required=True, help="The name of the project to package.")
    parser_package.set_defaults(func=handle_package_project)
    
    # 'status' command
    parser_status = subparsers.add_parser("status", help="Display the status and progress of a project.")
    parser_status.add_argument("--name", required=True, help="The name of the project to check.")
    parser_status.set_defaults(func=handle_status)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()