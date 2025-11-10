import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils.logger import setup_logging
from extractors.query_builder import build_search_query
from extractors.linkedin_parser import find_profile

@dataclass
class SearchResult:
    name: str
    linkedinUrl: Optional[str]
    position: Optional[str]
    company: Optional[str]
    language: Optional[str]
    searchQuery: str
    status: str

    @classmethod
    def from_profile(
        cls,
        name: str,
        search_query: str,
        status: str,
        profile: Optional[Dict[str, Any]],
        preferred_language: Optional[str],
    ) -> "SearchResult":
        profile = profile or {}
        return cls(
            name=name,
            linkedinUrl=profile.get("linkedinUrl"),
            position=profile.get("position"),
            company=profile.get("company"),
            language=profile.get("language") or preferred_language,
            searchQuery=search_query,
            status=status,
        )

def load_settings(root: Path) -> Dict[str, Any]:
    settings_path = root / "src" / "config" / "settings.json"
    if not settings_path.is_file():
        raise FileNotFoundError(f"Settings file not found at {settings_path}")
    with settings_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_names(input_path: Path, logger: logging.Logger) -> List[Tuple[str, Optional[str], Optional[str]]]:
    """
    Load names from a text file.

    Each non-empty, non-comment line can be:
        - "Name"
        - "Name|Company"
        - "Name|Company|Position"
    """
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found at {input_path}")

    entries: List[Tuple[str, Optional[str], Optional[str]]] = []

    with input_path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 1:
                name, company, position = parts[0], None, None
            elif len(parts) == 2:
                name, company = parts
                position = None
            else:
                name, company, position = parts[0], parts[1], "|".join(parts[2:]).strip()

            if not name:
                logger.warning("Skipping empty name at line %d", line_no)
                continue

            entries.append((name, company or None, position or None))

    logger.info("Loaded %d entries from %s", len(entries), input_path)
    return entries

def write_results(output_path: Path, results: List[SearchResult], logger: logging.Logger) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = [asdict(r) for r in results]
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    logger.info("Wrote %d result records to %s", len(results), output_path)

def process_entry(
    name: str,
    company: Optional[str],
    position: Optional[str],
    preferred_language: Optional[str],
    logger: logging.Logger,
) -> SearchResult:
    # Build a human-readable search query (simulated; no real web calls are performed).
    search_query = build_search_query(
        name=name,
        company=company,
        position=position,
        language=preferred_language,
    )

    profile, status = find_profile(
        name=name,
        company=company,
        language=preferred_language,
        search_query=search_query,
        logger=logger,
    )

    return SearchResult.from_profile(
        name=name,
        search_query=search_query,
        status=status,
        profile=profile,
        preferred_language=preferred_language,
    )

def run(
    root: Path,
    input_file: Optional[str] = None,
    output_file: Optional[str] = None,
    language: Optional[str] = None,
    max_workers: Optional[int] = None,
) -> None:
    # Load configuration
    settings = load_settings(root)

    cfg_input = input_file or settings.get("input_file", "data/input_names.txt")
    cfg_output = output_file or settings.get("output_file", "data/results.json")
    cfg_log_file = settings.get("log_file", "data/logs/run_2025-11-11.log")

    preferred_language = language or settings.get("default_language")
    worker_count = max_workers or int(settings.get("max_workers", 4))

    input_path = root / cfg_input
    output_path = root / cfg_output
    log_path = root / cfg_log_file

    # Ensure log directory exists and configure logging
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(log_path)
    logger.info("Starting LinkedIn People URL - Mass Profile Finder (simulated)")
    logger.debug("Configuration: input=%s, output=%s, language=%s, workers=%d", cfg_input, cfg_output, preferred_language, worker_count)

    try:
        entries = load_names(input_path, logger)
    except Exception as exc:
        logger.exception("Failed to load input names: %s", exc)
        raise SystemExit(1) from exc

    results: List[SearchResult] = []
    if not entries:
        logger.warning("No valid entries found in %s", input_path)
        write_results(output_path, results, logger)
        return

    # Process entries in parallel
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(process_entry, name, company, position, preferred_language, logger): (name, company)
            for name, company, position in entries
        }

        for future in as_completed(future_map):
            name, company = future_map[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(
                    "Processed '%s'%s -> status=%s",
                    name,
                    f" @ {company}" if company else "",
                    result.status,
                )
            except Exception as exc:
                logger.exception("Error while processing '%s': %s", name, exc)
                results.append(
                    SearchResult(
                        name=name,
                        linkedinUrl=None,
                        position=None,
                        company=company,
                        language=preferred_language,
                        searchQuery=f"lookup:{name}",
                        status="error",
                    )
                )

    write_results(output_path, results, logger)
    logger.info("Run completed successfully")

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LinkedIn People URL - Mass Profile Finder (simulation without real web scraping)."
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input_file",
        help="Path to the input names file (default from config).",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        help="Path to the output JSON file (default from config).",
    )
    parser.add_argument(
        "-l",
        "--language",
        dest="language",
        help="Preferred profile language (overrides config).",
    )
    parser.add_argument(
        "-w",
        "--workers",
        dest="workers",
        type=int,
        help="Maximum number of concurrent workers (overrides config).",
    )
    return parser

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = build_arg_parser()
    args = parser.parse_args()

    run(
        root=root,
        input_file=args.input_file,
        output_file=args.output_file,
        language=args.language,
        max_workers=args.workers,
    )

if __name__ == "__main__":
    main()