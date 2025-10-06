import argparse


class CLIParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="GitHub Org Analyzer")
        self.parser.add_argument(
            "-c",
            "--count",
            type=int,
            default=100,
            help="Number of top authors to display",
        )
        self.parser.add_argument(
            "-t", "--token", type=str, default="", help="GitHub token"
        )
        self.parser.add_argument(
            "-o", "--org", type=str, default="artsy", help="GitHub organization name"
        )

    def parse_args(self):
        return self.parser.parse_args()
