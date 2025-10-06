import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class Analyzer:
    def __init__(self, github_client, count):
        self.github_client = github_client
        self.count = count
        self.statistics = defaultdict(int)

    def calculate_statistics(self):
        commits = self.github_client.commits
        for commit in commits:
            try:
                message = commit.get("message", "")
                if message.startswith("Merge pull request #"):
                    continue
                author_email = "unknown"
                if (
                    commit.get("author")
                    and commit["author"].get("user")
                    and commit["author"]["user"].get("email")
                ):
                    email = commit["author"]["user"]["email"]
                    if email and email.strip():
                        author_email = email
                self.statistics[author_email] += 1
            except (KeyError, AttributeError, TypeError) as e:
                logger.warning(f"Ошибка при обработке коммита: {e}, пропускаем коммит")

    def get_top_authors(self):
        return dict(
            sorted(self.statistics.items(), key=lambda x: x[1], reverse=True)[
                : self.count
            ]
        )
