# rayzOSS Virtual File System
# Credits: rayzien (https://github.com/rayzien) & pheonix14 (https://github.com/pheonix14)
import os
from app.core.github import GitHubClient
from app.core.sharding import ShardManager
from app.core.compression import RayzCompressor

class VirtualFileSystem:
    def __init__(self, token, shards, client=None):
        self.github = client if client else GitHubClient(token)
        self.shard_manager = ShardManager(shards)
        self.compressor = RayzCompressor()

    def upload(self, local_path, remote_path, compress=True):
        if not os.path.exists(local_path):
            return False, f"Local file not found: {local_path}"
            
        with open(local_path, 'rb') as f:
            content = f.read()
            
        if compress:
            content = self.compressor.compress(content)

        shard = self.shard_manager.get_shard(remote_path)
        target_path = f"fs/{remote_path.strip('/')}"
        
        status, resp = self.github.write_file(shard, target_path, content, f"FS UPLOAD {remote_path}")
        if status in [200, 201]:
            return True, f"Uploaded to shard: {shard} (path: {target_path})"
        return False, resp.get('message', str(resp))

    def download(self, remote_path, local_path, decompress=True):
        shard = self.shard_manager.get_shard(remote_path)
        target_path = f"fs/{remote_path.strip('/')}"
        
        success, content = self.github.read_file(shard, target_path)
        if success:
            if decompress:
                try:
                    content = self.compressor.decompress(content)
                except Exception as e:
                    return False, f"Decompression error: {e}"

            target_dir = os.path.dirname(os.path.abspath(local_path))
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(content)
            return True, f"Downloaded from shard: {shard} to {local_path}"
        return False, "File not found on remote."
