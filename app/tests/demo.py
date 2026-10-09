# rayzOSS End-to-End Live Demo Runner
# Credits: rayzien (https://github.com/rayzien) & pheonix14 (https://github.com/pheonix14)
import os
import hashlib
from app.core.github import MockGitHubClient
from app.sync.watcher import SyncManager
from app.tests.test_suite import create_synthetic_bmp

def run_demo():
    print("=" * 65)
    print("  rayzOSS LIVE DEMO: ~/backup -> Cloud Shard -> ~/down")
    print("  Engineered by: rayzien & pheonix14")
    print("=" * 65)
    
    backup_dir = os.path.expanduser("~/backup")
    down_dir = os.path.expanduser("~/down")
    os.makedirs(os.path.join(backup_dir, "gallery"), exist_ok=True)
    os.makedirs(os.path.join(backup_dir, "documents"), exist_ok=True)
    
    # 1. Create realistic sample image and document in ~/backup
    bmp_path = os.path.join(backup_dir, "gallery", "crystal_gradient.bmp")
    txt_path = os.path.join(backup_dir, "documents", "system_manifest.txt")
    
    bmp_bytes = create_synthetic_bmp(160, 160)
    with open(bmp_path, "wb") as f:
        f.write(bmp_bytes)
        
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("rayzOSS Distributed Storage Manifest\nArchitects: rayzien & pheonix14\nLossless Compression: Enabled\nIntegrity Check: CRC-32 + SHA-256\n")
        
    print(f"\n[STEP 1] Real Sample Files Staged in {backup_dir}:")
    print(f"  * gallery/crystal_gradient.bmp:  {len(bmp_bytes):>6} bytes (24-bit RGB)")
    print(f"  * documents/system_manifest.txt: {os.path.getsize(txt_path):>6} bytes")
    
    # 2. Run Sync
    print(f"\n[STEP 2] Running Sync Engine (Lossless LZMA Compression & Sharding)...")
    mock_client = MockGitHubClient(user="rayzien")
    syncer = SyncManager(client=mock_client, backup_dir=backup_dir, down_dir=down_dir)
    repo = syncer.get_or_create_repo()
    print(f"  * Bound Cloud Repository: {repo}")
    
    syncer.sync_once(repo)
    
    # 3. Run Download
    print(f"\n[STEP 3] Running Restore Engine (Decompression & Integrity Verification)...")
    syncer.download_all(repo)
    
    # 4. Compare ~/backup and ~/down
    print(f"\n[STEP 4] Bit-for-Bit Verification of Restored Files in {down_dir}:")
    restored_bmp = os.path.join(down_dir, "gallery", "crystal_gradient.bmp")
    restored_txt = os.path.join(down_dir, "documents", "system_manifest.txt")
    
    with open(bmp_path, "rb") as f1, open(restored_bmp, "rb") as f2:
        b1, b2 = f1.read(), f2.read()
        bmp_match = (b1 == b2)
        h1, h2 = hashlib.sha256(b1).hexdigest(), hashlib.sha256(b2).hexdigest()
        
    with open(txt_path, "rb") as f1, open(restored_txt, "rb") as f2:
        t1, t2 = f1.read(), f2.read()
        txt_match = (t1 == t2)
        
    print(f"  * gallery/crystal_gradient.bmp:")
    print(f"      Original SHA-256:  {h1}")
    print(f"      Restored SHA-256:  {h2}")
    print(f"      Integrity Status:  {'100% IDENTICAL CRISP [PASS]' if bmp_match else 'FAILED'}")
    print(f"  * documents/system_manifest.txt: {'100% IDENTICAL [PASS]' if txt_match else 'FAILED'}")
    
    print("\n" + "=" * 65)
    print("  LIVE DEMO COMPLETE: Restored files verified in ~/down")
    print("=" * 65 + "\n")
    return True
