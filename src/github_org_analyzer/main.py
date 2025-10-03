import requests
from token_for_git import tok_name

url = "https://api.github.com/graphql"
GIT_TOKEN = tok_name


def execute_query(query, variables):
    response = requests.post(
        url,
        json={"query": query, "variables": variables},
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GIT_TOKEN}",
        },
    )
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Опа, сломалось что-то... Ошибка: {response.status_code}")


def get_all_repos(org_name):
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
