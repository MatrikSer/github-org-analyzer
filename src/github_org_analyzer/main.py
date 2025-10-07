import logging
import sys

from github_org_analyzer.api.github import GitHubAPIError, GitHubClient
from github_org_analyzer.core.analyzer import Analyzer
from github_org_analyzer.utils.parser import CLIParser
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        parser = CLIParser()
        args = parser.parse_args()

        if not args.token:
            logger.error("Не указан GitHub token. Используйте --token")
            sys.exit(1)

        github_client = GitHubClient(args.token, args.org)
        logger.info(f"Начинаем анализ организации: {args.org}")

        github_client.get_repos()
        logger.info(f"Найдено репозиториев: {len(github_client.repos)}")

        github_client.get_commits()
        logger.info(f"Получено коммитов: {len(github_client.commits)}")

        analyzer = Analyzer(github_client, args.count)
        analyzer.calculate_statistics()

        top_authors = analyzer.get_top_authors()
        logger.info(f"Топ {len(top_authors)} авторов:")
        for (author, count_commits) in top_authors.items():
            logger.info(f"{author}: {count_commits}")
        data = pd.DataFrame({"Author": [author for author in top_authors.keys()],
                             "Count commits": [count_commits for count_commits in top_authors.values()]})
        plt.figure(figsize=(12,16))
        plt.barh(data["Author"], data["Count commits"])
        plt.xlabel("Commits")
        plt.title("Commits of 100 authors")
        plt.tight_layout()
        plt.show()

    except GitHubAPIError as e:
        logger.error(f"Ошибка GitHub API: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        sys.exit(1)
