import urllib.request
import json

# GitHub APIでリポジトリの情報を取得
try:
    api_url = 'https://api.github.com/repos/Longtran2404/mcp-google-drive'
    response = urllib.request.urlopen(api_url)
    repo_data = json.loads(response.read().decode('utf-8'))
    print(f"Repository: {repo_data.get('full_name')}")
    print(f"Default branch: {repo_data.get('default_branch')}")
    print(f"Description: {repo_data.get('description')}")
    print(f"URL: {repo_data.get('html_url')}")
    print()
except Exception as e:
    print(f"API Error: {e}")

# READMEを取得
branches = ['main', 'master', 'v1.6.2']
found = False

for branch in branches:
    try:
        url = f'https://raw.githubusercontent.com/Longtran2404/mcp-google-drive/{branch}/README.md'
        response = urllib.request.urlopen(url)
        content = response.read().decode('utf-8')
        print(f"=== Found README in {branch} branch ===")
        print(content[:4000])
        found = True
        break
    except Exception as e:
        continue

if not found:
    print("README not found in common branches")
    print("Trying to get package.json or source code...")
    
    # package.jsonを試す
    try:
        url = 'https://raw.githubusercontent.com/Longtran2404/mcp-google-drive/main/package.json'
        response = urllib.request.urlopen(url)
        pkg_data = json.loads(response.read().decode('utf-8'))
        print("\n=== Package.json ===")
        print(json.dumps(pkg_data, indent=2))
    except:
        pass


