# rayzOSS GitHub Client & Mock Client
# Credits: rayzien (https://github.com/rayzien) & pheonix14 (https://github.com/pheonix14)
import urllib.request
import urllib.error
import urllib.parse
import json
import base64
import hashlib

class GitHubClient:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.github.com"

    def request(self, method, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "rayzOSS"
        }
        
        req_data = None
        if data is not None:
            req_data = json.dumps(data).encode('utf-8')
            headers["Content-Type"] = "application/json"
            
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req) as response:
                resp_body = response.read()
                return response.status, json.loads(resp_body) if resp_body else {}
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read()
                return e.code, json.loads(err_body)
            except Exception:
                return e.code, {}
        except urllib.error.URLError as e:
            return 500, {"error": str(e)}

    def create_private_repo(self, name):
        data = {
            "name": name,
            "private": True,
            "auto_init": True
        }
        return self.request('POST', '/user/repos', data)

    def get_user_repos(self):
        status, resp = self.request('GET', '/user/repos?type=owner&per_page=100')
        if status == 200 and isinstance(resp, list):
            return [r['name'] for r in resp]
        return []

    def get_file_info(self, repo, path):
        encoded_path = urllib.parse.quote(path.strip("/"))
        endpoint = f"/repos/{repo}/contents/{encoded_path}"
        return self.request('GET', endpoint)

    def list_dir(self, repo, path=""):
        encoded_path = urllib.parse.quote(path.strip("/"))
        endpoint = f"/repos/{repo}/contents/{encoded_path}" if path else f"/repos/{repo}/contents"
        return self.request('GET', endpoint)

    def write_file(self, repo, path, content_bytes, message="Update from rayzOSS"):
        clean_path = path.strip("/")
        encoded_path = urllib.parse.quote(clean_path)
        endpoint = f"/repos/{repo}/contents/{encoded_path}"
        
        status, info = self.get_file_info(repo, clean_path)
        
        data = {
            "message": message,
            "content": base64.b64encode(content_bytes).decode('utf-8')
        }
        if status == 200 and isinstance(info, dict) and 'sha' in info:
            data['sha'] = info['sha']
        elif status == 200 and isinstance(info, list):
            return 400, {"message": "Target path is an existing directory, not a file."}
        
        return self.request('PUT', endpoint, data)

    def read_file(self, repo, path):
        clean_path = path.strip("/")
        status, info = self.get_file_info(repo, clean_path)
        if status == 200 and isinstance(info, dict) and 'content' in info:
            cleaned_b64 = "".join(info['content'].split())
            return True, base64.b64decode(cleaned_b64)
        return False, None

    def delete_file(self, repo, path, message="Delete from rayzOSS"):
        clean_path = path.strip("/")
        encoded_path = urllib.parse.quote(clean_path)
        endpoint = f"/repos/{repo}/contents/{encoded_path}"
        
        status, info = self.get_file_info(repo, clean_path)
        if status != 200 or not isinstance(info, dict) or 'sha' not in info:
            return False, "File not found"
        
        data = {
            "message": message,
            "sha": info['sha']
        }
        del_status, resp = self.request('DELETE', endpoint, data)
        return del_status == 200, resp


class MockGitHubClient:
    """
    In-memory simulation of the GitHub API for local self-testing and offline operation.
    """
    def __init__(self, token="mock-token-rayzoss", user="rayzien"):
        self.token = token
        self.user = user
        # repos structure: { "owner/repo": { "path/to/file": (bytes, sha) } }
        self.repos = {}

    def request(self, method, endpoint, data=None):
        if endpoint == "/user":
            return 200, {"login": self.user, "name": "rayzOSS Test User"}
        if endpoint.startswith("/user/repos"):
            if method == 'GET':
                user_repos = [{"name": r.split("/")[1]} for r in self.repos if r.startswith(f"{self.user}/")]
                return 200, user_repos
            elif method == 'POST':
                name = data.get("name", "oss1")
                full_name = f"{self.user}/{name}"
                if full_name not in self.repos:
                    self.repos[full_name] = {}
                return 201, {"name": name, "full_name": full_name}
        return 404, {"message": "Not Found in Mock"}

    def create_private_repo(self, name):
        full_name = f"{self.user}/{name}"
        self.repos[full_name] = {}
        return 201, {"name": name, "full_name": full_name}

    def get_user_repos(self):
        return [r.split("/")[1] for r in self.repos if r.startswith(f"{self.user}/")]

    def _calc_sha(self, content_bytes):
        return hashlib.sha1(b"blob " + str(len(content_bytes)).encode('utf-8') + b"\0" + content_bytes).hexdigest()

    def get_file_info(self, repo, path):
        clean_path = path.strip("/")
        if repo not in self.repos:
            return 404, {"message": "Repository not found"}
        
        repo_files = self.repos[repo]
        if clean_path in repo_files:
            content, sha = repo_files[clean_path]
            return 200, {
                "type": "file",
                "path": clean_path,
                "sha": sha,
                "size": len(content),
                "content": base64.b64encode(content).decode('utf-8')
            }
        
        # Check if it represents a directory
        prefix = clean_path + "/" if clean_path else ""
        sub_items = [f for f in repo_files if f.startswith(prefix)]
        if sub_items:
            return self.list_dir(repo, clean_path)
            
        return 404, {"message": "File not found"}

    def list_dir(self, repo, path=""):
        clean_path = path.strip("/")
        if repo not in self.repos:
            return 404, {"message": "Repository not found"}
            
        repo_files = self.repos[repo]
        prefix = clean_path + "/" if clean_path else ""
        
        entries = {}
        for file_path in repo_files:
            if prefix and not file_path.startswith(prefix):
                continue
            rel = file_path[len(prefix):]
            parts = rel.split("/", 1)
            name = parts[0]
            if len(parts) > 1:
                # directory
                entries[name] = {"type": "dir", "path": f"{prefix}{name}".strip("/"), "name": name}
            else:
                # file
                content, sha = repo_files[file_path]
                entries[name] = {
                    "type": "file",
                    "path": file_path,
                    "name": name,
                    "sha": sha,
                    "size": len(content)
                }
        return 200, list(entries.values())

    def write_file(self, repo, path, content_bytes, message="Update from rayzOSS"):
        clean_path = path.strip("/")
        if repo not in self.repos:
            self.repos[repo] = {}
            
        sha = self._calc_sha(content_bytes)
        self.repos[repo][clean_path] = (content_bytes, sha)
        return 200, {"content": {"path": clean_path, "sha": sha}}

    def read_file(self, repo, path):
        clean_path = path.strip("/")
        if repo in self.repos and clean_path in self.repos[repo]:
            return True, self.repos[repo][clean_path][0]
        return False, None

    def delete_file(self, repo, path, message="Delete from rayzOSS"):
        clean_path = path.strip("/")
        if repo in self.repos and clean_path in self.repos[repo]:
            del self.repos[repo][clean_path]
            return True, {"message": "Deleted"}
        return False, {"message": "File not found"}
