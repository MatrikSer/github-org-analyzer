from github_org_analyzer.api.github import GitHubClient
from github_org_analyzer.core.analyzer import Analyzer
from github_org_analyzer.utils.parser import CLIParser

def main():
    parser = CLIParser()
    args = parser.parse_args()
    github_client = GitHubClient(args.token, args.org)
    github_client.get_repos()
    github_client.get_commits()
    analyzer = Analyzer(github_client, args.count)
    analyzer.calculate_statistics()
    for author, value in analyzer.get_top_authors().items():
        print(f"{author}: {value}")
