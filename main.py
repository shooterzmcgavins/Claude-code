#!/usr/bin/env python3
import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from config import Config, HAIKU, SONNET, OPUS
from agent import Agent

MODEL_ALIASES = {
    "haiku": HAIKU,
    "sonnet": SONNET,
    "opus": OPUS,
}


def build_config(args: argparse.Namespace) -> Config:
    cfg = Config()
    if args.max_model:
        cfg.max_model = MODEL_ALIASES.get(args.max_model, args.max_model)
    return cfg


def run_cli(agent: Agent, args: argparse.Namespace) -> None:
    force_model = MODEL_ALIASES.get(args.model, args.model) if args.model else None

    if args.interactive:
        print("Interactive mode. Type 'exit' or Ctrl+C to quit, 'cost' to see token usage, 'reset' to clear history.\n")
        while True:
            try:
                task = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n{agent.cost_summary()}")
                break
            if not task:
                continue
            if task.lower() == "exit":
                print(agent.cost_summary())
                break
            if task.lower() == "cost":
                print(agent.cost_summary())
                continue
            if task.lower() == "reset":
                agent.reset()
                print("History cleared.")
                continue
            agent.run(task, force_model=force_model)
            print(f"\n[{agent.cost_summary()}]\n")
    elif args.task:
        agent.run(args.task, force_model=force_model)
        print(f"\n[{agent.cost_summary()}]")
    else:
        print("No task provided. Use --interactive / -i or pass a task as an argument.", file=sys.stderr)
        sys.exit(1)


async def run_platform(agent: Agent, platform_name: str, config: Config) -> None:
    async def handler(user_id: str, message: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, agent.run, message)

    if platform_name == "slack":
        if not config.slack_token:
            print("SLACK_BOT_TOKEN not set", file=sys.stderr)
            sys.exit(1)
        from platforms import SlackPlatform
        platform = SlackPlatform(config.slack_token)

    elif platform_name == "discord":
        if not config.discord_token:
            print("DISCORD_BOT_TOKEN not set", file=sys.stderr)
            sys.exit(1)
        from platforms import DiscordPlatform
        platform = DiscordPlatform(config.discord_token)

    elif platform_name == "telegram":
        if not config.telegram_token:
            print("TELEGRAM_BOT_TOKEN not set", file=sys.stderr)
            sys.exit(1)
        from platforms import TelegramPlatform
        platform = TelegramPlatform(config.telegram_token)

    else:
        print(f"Unknown platform: {platform_name}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting {platform_name} bot...")
    await platform.start(handler)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Token-efficient AI agent — an OpenClaw alternative",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Search for the latest Python news"
  python main.py -i
  python main.py --model sonnet "Implement a binary search in Python"
  python main.py --platform telegram
        """,
    )
    parser.add_argument("task", nargs="?", help="Task for the agent to complete")
    parser.add_argument(
        "--model", "-m",
        choices=["haiku", "sonnet", "opus"],
        help="Force a specific model (overrides auto-routing)",
    )
    parser.add_argument(
        "--max-model",
        choices=["haiku", "sonnet", "opus"],
        default="sonnet",
        help="Maximum model tier for auto-routing (default: sonnet)",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start an interactive REPL session",
    )
    parser.add_argument(
        "--platform",
        choices=["slack", "discord", "telegram"],
        help="Run as a bot on the specified platform",
    )

    args = parser.parse_args()
    config = build_config(args)
    agent = Agent(config)

    if args.platform:
        asyncio.run(run_platform(agent, args.platform, config))
    else:
        run_cli(agent, args)


if __name__ == "__main__":
    main()
