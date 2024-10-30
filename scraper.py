import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load the GitHub API token from the .env file
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

headers = {
    "Authorization": f"token {GITHUB_TOKEN}"
}

def get_users_in_basel(min_followers=10):
    url = f"https://api.github.com/search/users?q=location:Basel+followers:>{min_followers}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        users = response.json().get("items", [])
        return users
    else:
        print(f"Failed to fetch users: {response.status_code}")
        return []

def save_users_to_csv(users):
    # Extract the required fields for each user
    users_data = []
    for user in users:
        user_details = requests.get(user['url'], headers=headers).json()
        users_data.append({
            "login": user_details.get("login", ""),
            "name": user_details.get("name", ""),
            "company": clean_company_name(user_details.get("company", "")),
            "location": user_details.get("location", ""),
            "email": user_details.get("email", ""),
            "hireable": user_details.get("hireable", ""),
            "bio": user_details.get("bio", ""),
            "public_repos": user_details.get("public_repos", 0),
            "followers": user_details.get("followers", 0),
            "following": user_details.get("following", 0),
            "created_at": user_details.get("created_at", "")
        })

    # Save to CSV
    df = pd.DataFrame(users_data)
    df.to_csv("users.csv", index=False)

def clean_company_name(company_name):
    # Clean up company name as specified
    if company_name:
        company_name = company_name.strip()
        if company_name.startswith('@'):
            company_name = company_name[1:]
        company_name = company_name.upper()
    return company_name


def get_user_repositories(username, max_repos=500):
    """
    Fetches up to `max_repos` public repositories for a given GitHub username.
    """
    repos = []
    page = 1
    per_page = 100  # GitHub API max items per page is 100

    while len(repos) < max_repos:
        url = f"https://api.github.com/users/{username}/repos?sort=pushed&per_page={per_page}&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch repos for {username}: {response.status_code}")
            break
        
        page_repos = response.json()
        if not page_repos:
            break  # No more repos on further pages
        
        repos.extend(page_repos)
        page += 1

    return repos[:max_repos]

def save_repositories_to_csv(users):
    """
    For each user in the `users.csv`, fetch their repositories and save them to `repositories.csv`.
    """
    repo_data = []

    for user in users:
        username = user["login"]
        repos = get_user_repositories(username)
        for repo in repos:
            license_name = repo.get("license").get("key", "") if repo.get("license") else ""
            repo_data.append({
                "login": username,
                "full_name": repo.get("full_name", ""),
                "created_at": repo.get("created_at", ""),
                "stargazers_count": repo.get("stargazers_count", 0),
                "watchers_count": repo.get("watchers_count", 0),
                "language": repo.get("language", ""),
                "has_projects": repo.get("has_projects", False),
                "has_wiki": repo.get("has_wiki", False),
                "license_name": license_name
            })

    # Save to repositories.csv
    df_repos = pd.DataFrame(repo_data)
    df_repos.to_csv("repositories.csv", index=False)
    print("Repository data saved to repositories.csv.")



if __name__ == "__main__":
    users = get_users_in_basel()
    if users:
        save_users_to_csv(users)
        print("User data saved to users.csv.")

        # Load users data from users.csv to pass to the repositories function
        users_df = pd.read_csv("users.csv")
        save_repositories_to_csv(users_df.to_dict(orient="records"))
    else:
        print("No users found.")

