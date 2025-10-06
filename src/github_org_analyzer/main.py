import concurrent.futures
import time
from collections import defaultdict

import requests
from token_for_git import tok_name

url = "https://api.github.com/graphql"
GIT_TOKEN = tok_name
org_name = "artsy"


def execute_query(query, variables):
    try:
        response = requests.post(
            url,
            json={"query": query, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GIT_TOKEN}",
            },
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


def get_all_repos():
    all_repos = []
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
        variables = {"org": org_name, "cursor": cursor}
        result = execute_query(query, variables)
        if "data" in result:
            repos_data = result["data"]["organization"]["repositories"]
            all_repos.extend(repos_data["nodes"])
            page_info = repos_data["pageInfo"]
            has_next_page = page_info["hasNextPage"]
            cursor = page_info["endCursor"]
        else:
            raise Exception("Пришел корявый ответ(((")
    return all_repos


def get_all_commits():
    all_repos = get_all_repos()
    all_commits = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_repo = {
            executor.submit(process_repo, repo): repo for repo in all_repos
        }
        for future in concurrent.futures.as_completed(future_to_repo):
            try:
                repo_commits = future.result()
                all_commits.extend(repo_commits)
            except Exception as e:
                print(f"Ошибка при обработке репозитория: {e}!!!")
        return all_commits


def process_repo(repos):
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
            "owner": repos["owner"]["login"],
            "repo": repos["name"],
            "cursor": cursor,
        }

        result = execute_query(query, variables)
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


def get_statistics(top_n):
    commits = get_all_commits()
    statistics = defaultdict(int)
    for commit in commits:
        if commit["message"].startswith("Merge pull request #"):
            continue
        author_email = "unknown"
        if (
                commit.get("author")
                and commit["author"].get("user")
                and commit["author"]["user"].get("email")
        ):
            email = commit["author"]["user"]["email"]
            if email.strip():
                author_email = email
        statistics[author_email] += 1
    return dict(sorted(statistics.items(), key=lambda x: x[1], reverse=True)[:top_n])


top_authors = get_statistics(100)
for author, value in top_authors.items():
    print(f"{author}: {value}")
