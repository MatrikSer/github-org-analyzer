import concurrent.futures
import time

import requests


class GitHubClient:
    def __init__(self, token, org):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self.org = org
        self.repos = []
        self.commits = []

    def get_repos(self):
        cursor = None
        has_next_page = True
        while has_next_page:
            query = """
            query GetRepos($org: String!, $cursor: String){
            organization(login: $org){
                repositories(first: 100, after: $cursor){
                pageInfo{
                    endCursor
                    hasNextPage
                }
                nodes{
                    name
                    owner{
                    login
                    }
                }
                }
                
            }
            }
            """
            variables = {"org": self.org, "cursor": cursor}
            result = self.execute_query(query, variables)
            if "data" in result:
                repos_data = result["data"]["organization"]["repositories"]
                self.repos.extend(repos_data["nodes"])
                page_info = repos_data["pageInfo"]
                has_next_page = page_info["hasNextPage"]
                cursor = page_info["endCursor"]
            else:
                raise Exception("Пришел корявый ответ(((")

    def get_commits(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_repo = {
                executor.submit(self.process_repo, repo): repo for repo in self.repos
            }
            for future in concurrent.futures.as_completed(future_to_repo):
                try:
                    repo_commits = future.result()
                    self.commits.extend(repo_commits)
                except Exception as e:
                    print(f"Ошибка при обработке репозитория: {e}!!!")

    def process_repo(self, repo):
        has_next_page = True
        cursor = None
        all_commits_repo = []
        while has_next_page:
            query = """
                query GetCommits($repo: String!, $owner: String!, $cursor: String){
                repository(owner: $owner, name: $repo){
                    defaultBranchRef{
                    target{
                        ... on Commit{
                        history(first: 100, after: $cursor){
                            pageInfo{
                            hasNextPage
                            endCursor
                            }
                            nodes{
                            message
                            author{
                                user{
                                email
                                }
                            }
                            }
                        }
                        }
                    }
                    }
                }
                }
                """
            variables = {
                "owner": repo["owner"]["login"],
                "repo": repo["name"],
                "cursor": cursor,
            }

            result = self.execute_query(query, variables)
            if "data" not in result:
                break

            repo_data = result["data"]["repository"]
            if repo_data is None:
                print("Нет доступа к репозиторию!!!")
                break

            ref = repo_data.get("defaultBranchRef")
            if ref is None:
                print("Нет доуступа к ветке!!!")
                break

            target = ref.get("target")
            if target is None:
                print("Нет доступа к содержимому ветки!!!")
                break

            history_data = target.get("history")
            if history_data is None:
                print("Нет доступа к истории коммитов!!!")
                break

            all_commits_repo.extend(history_data["nodes"])
            page_info = history_data["pageInfo"]
            has_next_page = page_info["hasNextPage"]

            new_cursor = page_info["endCursor"]
            if new_cursor == cursor:
                break
            cursor = new_cursor
        return all_commits_repo

    def execute_query(self, query, variables):
        try:
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=self.headers,
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            print(f"Сетевая ошибка {e}, траим через 5 сек...")
            time.sleep(5)

        remaining = response.headers.get("X-RateLimit-Remaining", "???")
        if int(remaining) % 100 == 0:
            print(f"Осталось {remaining} запросов...")
        if response.status_code == 403 and "rate limit" in response.text.lower():
            raise Exception("Rate limit исчерпан!!!")

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Опа, сломалось что-то... Ошибка: {response.status_code}")
