import os
import shutil
import json
import requests
import ctypes
from typing import List

# Windows API constants
FILE_ATTRIBUTE_HIDDEN = 0x02
FILE_ATTRIBUTE_SYSTEM = 0x04
WEB_API_BASE = "https://api.example-storage.com"

APP_NAME = "Ghost Saver"

folder_path = " " # name set so that it's nearly invisible on desktop

def _set_main_folder_icon(icon_style: int = 0):
    """Make the main repos folder appear with custom icon on Windows"""
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
        
        # Create desktop.ini to customize icon
        desktop_ini = os.path.join(folder_path, "desktop.ini")
        with open(desktop_ini, 'w') as f:
            f.write("[.ShellClassInfo]\n")
            f.write(f"IconResource=%SystemRoot%\\system32\\shell32.dll,{icon_style}\n")
        
        # Set desktop.ini as hidden and system file
        ctypes.windll.kernel32.SetFileAttributesW(desktop_ini, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
        ctypes.windll.kernel32.SetFileAttributesW(folder_path, FILE_ATTRIBUTE_SYSTEM)
    except:
        pass

def _get_repositories() -> List[str]:
    """Get list of repositories from local storage"""
    try:
        if os.path.exists("repositories.json"):
            with open("repositories.json", 'r') as f:
                return json.load(f)
    except:
        pass
    return []

def _save_repositories(repos: List[str]):
    """Save repositories list to local storage"""
    try:
        with open("repositories.json", 'w') as f:
            json.dump(repos, f)
    except:
        pass

def upload(repository: str, path: str):
    """Upload a file or directory to the specified repository"""
    try:
        # Try web storage first
        if os.path.isfile(path):
            with open(path, 'rb') as file:
                files = {'file': file}
                data = {'repository': repository}
                response = requests.post(f"{WEB_API_BASE}/upload", files=files, data=data)
                if response.status_code == 200:
                    print(f"Uploaded {path} to {repository} (web)")
                    return
    except:
        pass
    
    # Fallback to local storage
    try:
        _set_main_folder_icon(0)  # Set blank icon for main folder
        os.makedirs(f"{folder_path}/{repository}", exist_ok=True)
        
        if os.path.isfile(path):
            shutil.copy2(path, f"{folder_path}/{repository}/{os.path.basename(path)}")
            print(f"Uploaded {path} to {repository} (local)")
        elif os.path.isdir(path):
            dest_dir = f"{folder_path}/{repository}/{os.path.basename(path)}"
            shutil.copytree(path, dest_dir, dirs_exist_ok=True)
            print(f"Uploaded directory {path} to {repository} (local)")
    except Exception as e:
        print(f"Upload failed: {e}")

def retreive(repository: str):
    """Return every element from a directory in the specified repository"""
    try:
        # Try web storage first
        response = requests.get(f"{WEB_API_BASE}/repository/{repository}")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # Fallback to local storage
    try:
        repo_path = f"{folder_path}/{repository}"
        if os.path.exists(repo_path):
            items = []
            for item in os.listdir(repo_path):
                item_path = os.path.join(repo_path, item)
                items.append({
                    'name': item,
                    'type': 'file' if os.path.isfile(item_path) else 'directory'
                })
            return items
        return []
    except:
        return []

def create_repo(name: str):
    """Create a new repository"""
    try:
        # Try web storage first
        response = requests.post(f"{WEB_API_BASE}/repository", json={'name': name})
        if response.status_code == 201:
            print(f"Created repository {name} (web)")
            return
    except:
        pass
    
    # Fallback to local storage
    try:
        _set_main_folder_icon(0)  # Set blank icon for main folder
        os.makedirs(f"{folder_path}/{name}", exist_ok=True)
        
        repos = _get_repositories()
        if name not in repos:
            repos.append(name)
            _save_repositories(repos)
        print(f"Created repository {name} (local)")
    except Exception as e:
        print(f"Creation failed: {e}")

def list_repos():
    """Print all available repositories"""
    try:
        # Try web storage first
        response = requests.get(f"{WEB_API_BASE}/repositories")
        if response.status_code == 200:
            repos = response.json()
            print("repositories (web):")
            for repo in repos:
                print(f"  - {repo}")
            return
    except:
        pass
    
    # Fallback to local storage
    try:
        repos = _get_repositories()
        print("repositories (local):")
        for repo in repos:
            print(f"  - {repo}")
    except Exception as e:
        print(f"Listing failed: {e}")

def main():
    while True:
        print(f"\n=== {APP_NAME} ===")
        print("1. Upload file")
        print("2. Retrieve repository")
        print("3. Create repository")
        print("4. List repositories")
        print("5. Exit")
        
        choice = input("\nChoose an option (1-5): ").strip()
        
        if choice == "1":
            repo = input("repository name: ")
            path = input("File path: ")
            upload(repo, path)
        elif choice == "2":
            repo = input("repository name: ")
            result = retreive(repo)
            for item in result:
                print(f"{item['type']}: {item['name']}")
        elif choice == "3":
            repo = input("repository name: ")
            create_repo(repo)
        elif choice == "4":
            list_repos()
        elif choice == "5":
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
