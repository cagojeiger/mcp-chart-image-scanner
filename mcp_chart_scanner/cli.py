"""Command-line interface for extracting Docker images from Helm charts."""

import argparse
import json
import logging
import pathlib
import sys

from mcp_chart_scanner.extract import extract_images_from_chart
from mcp_chart_scanner.utils import (
    ERROR_HELM_INSTALL_GUIDE,
    ERROR_HELM_NOT_INSTALLED,
    check_helm_cli,
)


def parse_cli_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Extract Docker images used by a Helm chart archive or directory.",
    )
    parser.add_argument(
        "chart",
        type=pathlib.Path,
        help="Path to the .tgz Helm chart archive or unpacked chart directory",
    )
    parser.add_argument(
        "-f",
        "--values",
        type=pathlib.Path,
        action="append",
        default=[],
        help="Additional values.yaml file(s)",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress log messages (stderr)"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON array")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output raw image names without normalization",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for the CLI."""
    args = parse_cli_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)

    if not check_helm_cli():
        print(ERROR_HELM_NOT_INSTALLED)
        print(ERROR_HELM_INSTALL_GUIDE)
        sys.exit(1)
        return

    try:
        images = extract_images_from_chart(
            chart_path=args.chart,
            values_files=args.values,
            normalize=not args.raw,
        )

        if images:
            if args.json:
                print(json.dumps(images))
            else:
                print("\n".join(images))
        else:
            logging.error("No image fields found")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
