# rayzOSS Terminal Interface & CLI Engine
# Credits: rayzien (https://github.com/rayzien) & pheonix14 (https://github.com/pheonix14)
import cmd
import sys
import shlex
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import load_config, save_config
from app.vfs.filesystem import VirtualFileSystem
from app.db.database import DocumentDatabase
from app.tests.test_suite import run_all_tests
from app.tests.demo import run_demo

class RayzOSSREPL(cmd.Cmd):
    intro = """
===========================================================
  rayzOSS - Distributed GitHub File System & DB
===========================================================
  Credits:
  - rayzien: https://github.com/rayzien
  - pheonix14: https://github.com/pheonix14
  
  Please star the project and contribute on GitHub!
===========================================================
Type 'help' or '?' to list commands. Type 'test' to run self-tests.
"""
    prompt = "oss> "

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.vfs = None
        self.db = None
        self._init_systems()

    def _init_systems(self):
        token = self.config.get("token")
        shards = self.config.get("shards", [])
        if token and shards:
            self.vfs = VirtualFileSystem(token, shards)
            self.db = DocumentDatabase(token, shards)

    def do_config(self, arg):
        "Set configuration. Usage: config token <your_github_token>"
        args = shlex.split(arg)
        if len(args) == 2 and args[0] == "token":
            self.config["token"] = args[1]
            save_config(self.config)
            self._init_systems()
            print("Token saved successfully.")
        else:
            print("Usage: config token <token>")

    def do_shard(self, arg):
        "Manage shards. Usage: shard add <owner/repo> OR shard list"
        args = shlex.split(arg)
        if len(args) == 2 and args[0] == "add":
            repo = args[1]
            if repo not in self.config.get("shards", []):
                self.config.setdefault("shards", []).append(repo)
                self.config["shards"].sort()
                save_config(self.config)
                self._init_systems()
                print(f"Shard added: {repo}")
            else:
                print("Shard already exists.")
        elif len(args) == 1 and args[0] == "list":
            shards = self.config.get("shards", [])
            print("Configured Shards:")
            for idx, s in enumerate(shards):
                print(f" {idx + 1}. {s}")
            if not shards:
                print(" No shards configured.")
        else:
            print("Usage: shard add <owner/repo> OR shard list")

    def do_fs(self, arg):
        "Filesystem commands. Usage: fs upload <local> <remote> OR fs download <remote> <local>"
        if not self.vfs:
            print("System not initialized. Please configure token and add at least one shard.")
            return
            
        args = shlex.split(arg)
        if len(args) == 3 and args[0] == "upload":
            success, msg = self.vfs.upload(args[1], args[2])
            print(msg)
        elif len(args) == 3 and args[0] == "download":
            success, msg = self.vfs.download(args[1], args[2])
            print(msg)
        else:
            print("Usage: fs upload <local> <remote> OR fs download <remote> <local>")

    def do_db(self, arg):
        "Database commands. Usage: db put <col> <id> <data> OR db get <col> <id> OR db delete <col> <id>"
        if not self.db:
            print("System not initialized. Please configure token and add at least one shard.")
            return
            
        args = shlex.split(arg)
        if len(args) == 4 and args[0] == "put":
            success, msg = self.db.put(args[1], args[2], args[3])
            print(msg)
        elif len(args) == 3 and args[0] == "get":
            success, msg = self.db.get(args[1], args[2])
            print(msg)
        elif len(args) == 3 and args[0] == "delete":
            success, msg = self.db.delete(args[1], args[2])
            print(msg)
        else:
            print("Usage: db put <col> <id> <data> OR db get <col> <id> OR db delete <col> <id>")

    def do_sync(self, arg):
        "Background syncing and downloading. Usage: sync start OR sync download"
        token = self.config.get("token")
        if not token:
            print("Please configure your GitHub token first using: config token <token>")
            return
            
        from app.sync.watcher import SyncManager
        manager = SyncManager(token)
        
        args = shlex.split(arg)
        if len(args) == 1 and args[0] == "start":
            manager.run_sync()
        elif len(args) == 1 and args[0] == "download":
            manager.download_all()
        else:
            print("Usage: sync start OR sync download")

    def do_test(self, arg):
        "Run comprehensive system tests and benchmark. Usage: test"
        run_all_tests()

    def do_demo(self, arg):
        "Run live end-to-end sync demo on ~/backup and ~/down. Usage: demo"
        run_demo()

    def do_exit(self, arg):
        "Exit the application."
        print("Exiting rayzOSS.")
        return True
        
    def do_quit(self, arg):
        "Exit the application."
        return self.do_exit(arg)


def main():
    repl = RayzOSSREPL()
    # Check if CLI arguments were passed: e.g. "oss test" or "oss sync download"
    if len(sys.argv) > 1:
        cmd_name = sys.argv[1].lower()
        cmd_args = " ".join(sys.argv[2:])
        
        if cmd_name == "test":
            run_all_tests()
        elif cmd_name == "demo":
            run_demo()
        elif cmd_name == "sync":
            repl.do_sync(cmd_args)
        elif cmd_name == "config":
            repl.do_config(cmd_args)
        elif cmd_name == "shard":
            repl.do_shard(cmd_args)
        elif cmd_name == "fs":
            repl.do_fs(cmd_args)
        elif cmd_name == "db":
            repl.do_db(cmd_args)
        elif cmd_name in ["help", "-h", "--help"]:
            print("rayzOSS CLI - Credits: rayzien & pheonix14")
            print("Usage:")
            print("  oss               Start interactive REPL app")
            print("  oss demo          Run live end-to-end demo on ~/backup and ~/down")
            print("  oss test          Run comprehensive system test suite")
            print("  oss sync start    Start auto-sync daemon on ~/backup")
            print("  oss sync download Download and decompress all to ~/down")
            print("  oss config token <token>")
            print("  oss shard add <owner/repo>")
            print("  oss fs upload <local> <remote>")
            print("  oss fs download <remote> <local>")
            print("  oss db put <collection> <id> <json_data>")
            print("  oss db get <collection> <id>")
        else:
            print(f"Unknown command: '{cmd_name}'. Run 'oss help' or 'oss' for interactive shell.")
    else:
        try:
            repl.cmdloop()
        except KeyboardInterrupt:
            print("\nExiting rayzOSS.")

if __name__ == '__main__':
    main()
