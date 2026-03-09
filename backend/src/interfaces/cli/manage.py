"""Management CLI — run Celery tasks and maintenance commands manually.

Inspired by Django's `manage.py`. Each subcommand maps to a Celery task or
maintenance operation.

Usage (inside the backend container or with Poetry):
    python -m backend.src.interfaces.cli.manage <command> [options]
    poetry run manage <command> [options]

Available commands:
    collect-feeds           Fetch RSS feeds from all active sources
    run-ai-pipeline         Process unanalyzed articles through the AI pipeline
    send-alerts             Check recent articles for keyword matches and send emails
    send-digest             Compile and send the daily news digest email
    update-weights          Recalculate implicit interest weights from read history
    compute-trends          Aggregate trending keywords and sentiment for the last N hours
    seed                    Seed default sources and admin user into the database

Examples:
    poetry run manage collect-feeds
    poetry run manage run-ai-pipeline --batch-size 50
    poetry run manage compute-trends --hours 48
    poetry run manage send-alerts
"""

from __future__ import annotations

import argparse
import sys


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------


def cmd_collect_feeds(args: argparse.Namespace) -> None:
    """Trigger the collect_feeds_task synchronously."""
    from backend.src.infrastructure.messaging.tasks.collect_feeds import collect_feeds_task

    print("▶  Running collect-feeds task…")
    result = collect_feeds_task.apply()
    data = result.get()
    print(f"✔  Done — collected={data.get('collected')}, skipped={data.get('skipped')}, errors={data.get('errors')}")


def cmd_run_ai_pipeline(args: argparse.Namespace) -> None:
    """Trigger the run_ai_pipeline_task synchronously."""
    from backend.src.infrastructure.messaging.tasks.run_ai_pipeline import run_ai_pipeline_task

    print(f"▶  Running AI pipeline (batch_size={args.batch_size})…")
    result = run_ai_pipeline_task.apply(kwargs={"batch_size": args.batch_size})
    data = result.get()
    print(f"✔  Done — processed={data.get('processed')}, skipped={data.get('skipped')}, errors={data.get('errors')}")


def cmd_send_alerts(args: argparse.Namespace) -> None:
    """Trigger the send_alerts_task synchronously."""
    from backend.src.infrastructure.messaging.tasks.send_alerts import send_alerts_task

    print("▶  Running send-alerts task…")
    result = send_alerts_task.apply()
    data = result.get()
    print(f"✔  Done — matched={data.get('matched')}, sent={data.get('sent')}, skipped={data.get('skipped')}")


def cmd_send_digest(args: argparse.Namespace) -> None:
    """Trigger the send_daily_digest_task synchronously."""
    from backend.src.infrastructure.messaging.tasks.send_daily_digest import send_daily_digest_task

    print("▶  Running send-digest task…")
    result = send_daily_digest_task.apply()
    data = result.get()
    print(f"✔  Done — total_articles={data.get('total_articles')}, sent={data.get('sent')}")


def cmd_update_weights(args: argparse.Namespace) -> None:
    """Trigger the update_implicit_weights_task synchronously."""
    from backend.src.infrastructure.messaging.tasks.update_implicit_weights import update_implicit_weights_task

    print("▶  Running update-weights task…")
    result = update_implicit_weights_task.apply()
    data = result.get()
    print(f"✔  Done — updated={data.get('updated')}")


def cmd_compute_trends(args: argparse.Namespace) -> None:
    """Trigger the compute_trends_task synchronously."""
    from backend.src.infrastructure.messaging.tasks.compute_trends import compute_trends_task

    print(f"▶  Running compute-trends task (hours={args.hours})…")
    result = compute_trends_task.apply(kwargs={"hours": args.hours})
    data = result.get()
    print(f"✔  Done — total_articles={data.get('total_articles')}")
    if data.get("top_keywords"):
        kws = ", ".join(f"{k}({c})" for k, c in data["top_keywords"][:5])
        print(f"   Top keywords: {kws}")
    if data.get("top_categories"):
        cats = ", ".join(f"{k}({c})" for k, c in data["top_categories"][:5])
        print(f"   Top categories: {cats}")


def cmd_seed(args: argparse.Namespace) -> None:
    """Run the seed script (sources + admin user)."""
    import asyncio
    from backend.src.interfaces.cli.seed_sources import _seed

    print("▶  Running seed…")
    asyncio.run(_seed())
    print("✔  Seed complete.")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage",
        description="News Scraper management CLI — run tasks and maintenance commands.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    # collect-feeds
    subparsers.add_parser("collect-feeds", help="Fetch RSS feeds from all active sources")

    # run-ai-pipeline
    p_ai = subparsers.add_parser("run-ai-pipeline", help="Process unanalyzed articles through the AI pipeline")
    p_ai.add_argument("--batch-size", type=int, default=20, metavar="N", help="Number of articles per batch (default: 20)")

    # send-alerts
    subparsers.add_parser("send-alerts", help="Check recent articles for keyword matches and send emails")

    # send-digest
    subparsers.add_parser("send-digest", help="Compile and send the daily news digest email")

    # update-weights
    subparsers.add_parser("update-weights", help="Recalculate implicit interest weights from read history")

    # compute-trends
    p_trends = subparsers.add_parser("compute-trends", help="Aggregate trending keywords and sentiment")
    p_trends.add_argument("--hours", type=int, default=24, metavar="N", help="Look-back window in hours (default: 24)")

    # seed
    subparsers.add_parser("seed", help="Seed default sources and admin user into the database")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_COMMANDS = {
    "collect-feeds": cmd_collect_feeds,
    "run-ai-pipeline": cmd_run_ai_pipeline,
    "send-alerts": cmd_send_alerts,
    "send-digest": cmd_send_digest,
    "update-weights": cmd_update_weights,
    "compute-trends": cmd_compute_trends,
    "seed": cmd_seed,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = _COMMANDS[args.command]
    try:
        handler(args)
    except KeyboardInterrupt:
        print("\n⚠  Interrupted.")
        sys.exit(1)
    except Exception as exc:
        print(f"✖  Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
