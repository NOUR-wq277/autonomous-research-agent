"""Main entrypoint supporting interactive CLI and FastAPI server modes."""

import argparse
import os
import sys
from pathlib import Path
import uvicorn
from dotenv import load_dotenv

# Ensure project root is in sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Configure UTF-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Load environment variables
load_dotenv()

from src.config.settings import get_settings
from src.services.research_service import ResearchService
from src.utils.logging import logger


def run_cli(question: str, mock_mode: bool = False, output_file: str = None):
    """Execute autonomous research from CLI and display results."""
    print("\n" + "=" * 60)
    print("  AUTONOMOUS AI RESEARCH AGENT")
    print("=" * 60)
    print(f"\n[?] Research Topic: {question}")
    print(f"[*] Initializing Multi-Agent Research Pipeline (Mock Mode: {mock_mode})...\n")

    service = ResearchService(mock_mode=mock_mode)

    try:
        response = service.run_research(question=question)

        print("\n" + "=" * 60)
        print("  FINAL RESEARCH REPORT")
        print("=" * 60 + "\n")
        print(response.report.full_markdown)
        print("\n" + "=" * 60)
        print("  RESEARCH METRICS & PROVENANCE")
        print("=" * 60)
        print(f"Total Sources Discovered: {response.sources_count}")
        print(f"Verified Evidence Points: {response.evidence_count}")
        print(f"Research Iterations:      {response.metadata.get('iterations', 1)}")
        print(f"Total Duration:           {response.metadata.get('duration_seconds', 0)}s")
        print(f"Model Used:               {response.metadata.get('primary_model')}")
        print("=" * 60 + "\n")

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response.report.full_markdown)
            print(f"[+] Saved report to '{output_file}'\n")

    except Exception as e:
        logger.error(f"Research execution failed: {e}", exc_info=True)
        print(f"\n[!] Error: {e}")
        sys.exit(1)


def main():
    """Parse arguments and route to CLI or Server."""
    parser = argparse.ArgumentParser(
        description="Autonomous AI Research Agent - Multi-Agent Intelligence System"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        help="Research topic or question to investigate.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the FastAPI REST backend server.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host address for the FastAPI server (default: from settings).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port number for the FastAPI server (default: from settings).",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in offline mock mode without making live API calls.",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Optional path to save the generated markdown report.",
    )

    args = parser.parse_args()
    settings = get_settings()

    if args.serve:
        host = args.host or settings.api_host
        port = args.port or settings.api_port
        logger.info(f"Starting FastAPI server on http://{host}:{port}")
        uvicorn.run("src.api.routes:app", host=host, port=port, reload=False)
    elif args.question:
        run_cli(question=args.question, mock_mode=args.mock, output_file=args.output)
    else:
        # Interactive CLI prompt
        print("\n" + "=" * 60)
        print("  AUTONOMOUS AI RESEARCH AGENT")
        print("=" * 60)
        try:
            user_input = input("\nEnter your research question: ").strip()
            if not user_input:
                print("No question entered. Exiting.")
                sys.exit(0)
            run_cli(question=user_input, mock_mode=args.mock, output_file=args.output)
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user.")
            sys.exit(0)


if __name__ == "__main__":
    main()
