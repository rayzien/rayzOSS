# rayzOSS Directory Watcher & Sync Manager
# Credits: rayzien (https://github.com/rayzien) & pheonix14 (https://github.com/pheonix14)
import os
import time
import json
from app.core.github import GitHubClient
from app.core.compression import RayzCompressor
from app.core.config import load_config, save_config

BACKUP_DIR = os.path.expanduser("~/backup")
DOWN_DIR = os.path.expanduser("~/down")

class SyncManager:
    def __init__(self, token=None, client=None, backup_dir=None, down_dir=None):
        self.config = load_config()
        self.token = token or self.config.get("token")
        self.github = client if client else GitHubClient(self.token)
        self.compressor = RayzCompressor()
        self.backup_dir = backup_dir or BACKUP_DIR
        self.down_dir = down_dir or DOWN_DIR

    def get_or_create_repo(self):
        repo = self.config.get("sync_repo")
        owner = self.config.get("github_username")
        
        if not owner:
            status, resp = self.github.request('GET', '/user')
            if status == 200 and isinstance(resp, dict) and 'login' in resp:
                owner = resp['login']
                self.config["github_username"] = owner
                save_config(self.config)
            else:
                print("Failed to get github user info. Make sure your token has the 'repo' scope.")
                return None

        if not repo:
            repos = self.github.get_user_repos()
            repo_idx = 1
            while f"oss{repo_idx}" in repos:
                repo_idx += 1
            
            new_repo_name = f"oss{repo_idx}"
            print(f"Auto-generating private repository: {new_repo_name}...")
            status, resp = self.github.create_private_repo(new_repo_name)
            if status in [201, 200]:
                repo = f"{owner}/{new_repo_name}"
                self.config["sync_repo"] = repo
                save_config(self.config)
                print(f"Created private repository {repo}.")
                time.sleep(1)
            else:
                print("Failed to create repo:", resp)
                return None
                
        return repo

    def sync_once(self, repo=None):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)
            
        repo = repo or self.get_or_create_repo()
        if not repo:
            return False, "No repository available"

        state_file = os.path.expanduser("~/.rayzoss/sync_state.json")
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
        except Exception:
            state = {}

        synced_count = 0
        for root, dirs, files in os.walk(self.backup_dir):
            for file in files:
                local_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_path, self.backup_dir)
                remote_path = rel_path.replace("\\", "/")
                
                mtime = os.path.getmtime(local_path)
                
                if str(mtime) != state.get(local_path):
                    print(f"Syncing (Compressing & Uploading): {rel_path}")
                    with open(local_path, 'rb') as f:
                        data = f.read()
                    
                    compressed_data = self.compressor.compress(data)
                    ratio = (len(compressed_data) / len(data) * 100) if len(data) > 0 else 100.0
                    print(f"Crisp lossless compression: {len(data)}B -> {len(compressed_data)}B ({ratio:.1f}%)")
                    
                    status, resp = self.github.write_file(repo, remote_path, compressed_data, f"Sync {rel_path}")
                    if status in [200, 201]:
                        state[local_path] = str(mtime)
                        synced_count += 1
                        print(f"Successfully mirrored: {rel_path} -> {repo}")
                    else:
                        print(f"Failed to upload {rel_path}: {resp}")
        
        if synced_count > 0:
            os.makedirs(os.path.dirname(state_file), exist_ok=True)
            with open(state_file, 'w') as f:
                json.dump(state, f)

        return True, f"Synced {synced_count} file(s)"

    def run_sync(self):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)
            print(f"Created tracking directory {self.backup_dir}")
            
        repo = self.get_or_create_repo()
        if not repo:
            return

        print(f"Starting auto-sync daemon for {self.backup_dir} -> {repo}")
        print("Waiting for file changes... (Press Ctrl+C to stop)")

        try:
            while True:
                self.sync_once(repo)
                time.sleep(3)
        except KeyboardInterrupt:
            print("\nStopping auto-sync daemon.")

    def _download_recursive(self, repo, remote_path, local_base):
        status, items = self.github.list_dir(repo, remote_path)
        downloaded = 0
        if status == 200:
            if isinstance(items, dict) and 'type' in items and items['type'] == 'file':
                items = [items]
            elif isinstance(items, dict) and 'content' in items:
                items = [{"type": "file", "path": remote_path}]
                
            for item in items:
                if item['type'] == 'dir':
                    downloaded += self._download_recursive(repo, item['path'], local_base)
                elif item['type'] == 'file':
                    local_path = os.path.join(local_base, item['path'])
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    
                    print(f"Downloading {item['path']}...")
                    succ, compressed_content = self.github.read_file(repo, item['path'])
                    if succ:
                        try:
                            content = self.compressor.decompress(compressed_content)
                            with open(local_path, 'wb') as f:
                                f.write(content)
                            print(f"Crisp decompression verified and saved: {item['path']}")
                            downloaded += 1
                        except Exception as e:
                            print(f"Failed to decompress {item['path']}, saving raw: {e}")
                            with open(local_path, 'wb') as f:
                                f.write(compressed_content)
                            downloaded += 1
                    else:
                        print(f"Failed to read {item['path']}")
        return downloaded

    def download_all(self, repo=None):
        repo = repo or self.config.get("sync_repo")
        if not repo:
            print("No sync repository found in config. Have you run the sync daemon yet?")
            return 0
            
        if not os.path.exists(self.down_dir):
            os.makedirs(self.down_dir, exist_ok=True)
            
        print(f"Downloading everything from {repo} to {self.down_dir}...")
        total = self._download_recursive(repo, "", self.down_dir)
        print(f"Download complete: {total} file(s) restored.")
        return total
