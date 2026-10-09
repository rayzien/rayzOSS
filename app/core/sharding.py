import hashlib

class ShardManager:
    def __init__(self, shards):
        self.shards = sorted(shards)

    def get_shard(self, key):
        if not self.shards:
            raise ValueError("No shards configured.")
        hash_val = int(hashlib.sha256(key.encode('utf-8')).hexdigest(), 16)
        shard_index = hash_val % len(self.shards)
        return self.shards[shard_index]
