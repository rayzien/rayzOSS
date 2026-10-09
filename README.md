# rayzOSS

An amazing distributed file system, auto-sync daemon, and database architecture built entirely on top of GitHub repositories. No servers needed. Zero dependencies.

### Credits
Designed and engineered by:
* **[rayzien](https://github.com/rayzien)**
* **[pheonix14](https://github.com/pheonix14)**

**Please STAR the repository and give credit to both rayzien and pheonix14 if you use this code! Contributions are highly welcomed.**

---

### Showcase
*(Terminal Interface)*
![REPL Interface](https://via.placeholder.com/800x400.png?text=rayzOSS+Terminal+Interface)

*(Sync Daemon in Action)*
![Sync Daemon](https://via.placeholder.com/800x400.png?text=Auto+Sync+Daemon+Running)

### Key Architectural Features
* **Modular Library:** Can be directly imported into any external application (`from app import VirtualFileSystem, DocumentDatabase, SyncManager`).
* **Lossless Crisp Compression Engine:** Custom wrapping with CRC-32 integrity and size verification headers. Guarantees 100% bit-for-bit quality preservation for images, graphics, and datasets.
* **Consistent Shard Routing:** Deterministically balances storage across arbitrary numbers of GitHub repository shards.
* **NoSQL Document Database:** JSON document storage, retrieval, and deletion distributed across shards.
* **Auto-Sync Mirroring Daemon:** Watches `~/backup`, automatically provisions private repositories named `oss1`, mirrors folder trees, and downloads everything into `~/down`.

### CLI & Interactive App Usage
You can run `oss` directly as an interactive application or execute commands straight from your terminal:

```bash
# 1. Run the built-in comprehensive test suite
oss test

# 2. Start the interactive REPL shell (keeps running like an app)
oss

# 3. Direct CLI commands
oss config token <YOUR_GITHUB_TOKEN>
oss sync start
oss sync download
oss fs upload ./local_file.png remote/path.png
oss fs download remote/path.png ./downloaded.png
oss db put users 101 '{"name": "Alice", "role": "engineer"}'
oss db get users 101
```

### Embed in Any Python Project
```python
import sys
sys.path.append('/data/data/com.termux/files/home/rayzOSS')

from app import VirtualFileSystem, DocumentDatabase, RayzCompressor

# Lossless compression
compressed = RayzCompressor.compress(raw_bytes)
original = RayzCompressor.decompress(compressed)

# Distributed Virtual File System
vfs = VirtualFileSystem(token="YOUR_TOKEN", shards=["owner/shard1", "owner/shard2"])
vfs.upload("image.png", "media/image.png")
```
