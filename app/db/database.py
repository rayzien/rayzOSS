# rayzOSS Document Database
# Credits: rayzien (https://github.com/rayzien) & pheonix14 (https://github.com/pheonix14)
from app.core.github import GitHubClient
from app.core.sharding import ShardManager
import json

class DocumentDatabase:
    def __init__(self, token, shards, client=None):
        self.github = client if client else GitHubClient(token)
        self.shard_manager = ShardManager(shards)

    def put(self, collection, doc_id, data_str):
        try:
            parsed = json.loads(data_str)
            # Normalize JSON formatting
            normalized_str = json.dumps(parsed, indent=2)
        except ValueError:
            return False, "Invalid JSON data format."
            
        key = f"{collection.strip('/')}/{doc_id.strip('/')}"
        shard = self.shard_manager.get_shard(key)
        target_path = f"db/{key}.json"
        
        status, resp = self.github.write_file(shard, target_path, normalized_str.encode('utf-8'), f"DB PUT {key}")
        if status in [200, 201]:
            return True, f"Saved document '{key}' to shard: {shard}"
        return False, resp.get('message', str(resp))

    def get(self, collection, doc_id):
        key = f"{collection.strip('/')}/{doc_id.strip('/')}"
        shard = self.shard_manager.get_shard(key)
        target_path = f"db/{key}.json"
        
        success, content = self.github.read_file(shard, target_path)
        if success:
            return True, content.decode('utf-8')
        return False, "Document not found."

    def delete(self, collection, doc_id):
        key = f"{collection.strip('/')}/{doc_id.strip('/')}"
        shard = self.shard_manager.get_shard(key)
        target_path = f"db/{key}.json"
        
        success, resp = self.github.delete_file(shard, target_path, f"DB DELETE {key}")
        if success:
            return True, f"Deleted document '{key}' from shard: {shard}"
        return False, resp
