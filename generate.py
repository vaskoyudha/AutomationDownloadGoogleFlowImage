#!/usr/bin/env python3
"""Google Flow Image Generator — CLI entry point."""

from src.config import parse_args, load_config, merge_config


def main():
    """Main entry point."""
    args = parse_args()
    config = load_config(args.config) if args.config else load_config(None)
    config = merge_config(config, args)
    print("Google Flow Image Generator - setup complete")
    print(f"Config: output_dir={config['output_dir']}")


if __name__ == "__main__":
    main()
