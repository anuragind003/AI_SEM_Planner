from __future__ import annotations

import argparse
import sys

from .pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI-Powered SEM Strategy Generator")
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    parser.add_argument("--out", default="outputs", help="Output directory")
    parser.add_argument("--max-serp-queries", type=int, default=10)
    parser.add_argument("--extra-seeds", default="", help="Comma-separated extra seeds")
    parser.add_argument("--llm-context", default="", help="Business context to guide LLM filtering/clustering")
    args = parser.parse_args(argv)

    extra_seeds = [s.strip() for s in args.extra_seeds.split(",") if s.strip()] if args.extra_seeds else None

    run_pipeline(
        config_path=args.config,
        outputs_dir=args.out,
        max_serp_queries=args.max_serp_queries,
        extra_seeds=extra_seeds,
        llm_context=args.llm_context or None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


