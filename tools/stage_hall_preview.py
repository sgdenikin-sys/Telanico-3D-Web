"""Prepare standalone Hall GLB from private approved delivery without changing the game."""
import hashlib
import io
import os
from pathlib import Path
import urllib.request
import zipfile

REPO = "sgdenikin-sys/Telanico-3D-Lab"
COMMIT = "13e14ac7716be7b04d401cf873806e866d90c3a3"
ARCHIVE = "artifacts/settlements_hall/v2-animated/settlements_hall_asset_pack.zip"
ZIP_SHA256 = "8bae1eb0be21ddc33e503bda8aecbf01ed37c58869b5104af00020476de0a404"
GLB_SHA256 = "2356bf19576414afaf6a9a96bac18d4a09fbba30af236867b58ed0c861ecd57e"

def main():
    token = os.environ.get("TELANICO_LAB_ARTIFACT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Existing TELANICO_LAB_ARTIFACT_TOKEN unavailable; refusing to stage an incomplete viewer")
    url = f"https://api.github.com/repos/{REPO}/contents/{ARCHIVE}?ref={COMMIT}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.raw+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Telanico-Hall-Pages",
    })
    with urllib.request.urlopen(req, timeout=90) as res:
        data = res.read()
    if hashlib.sha256(data).hexdigest() != ZIP_SHA256:
        raise RuntimeError(f"Model package SHA mismatch; refusing to publish {len(data)} bytes")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        matches = [n for n in z.namelist() if n.endswith("/settlements_hall.glb") or n == "settlements_hall.glb"]
        if len(matches) != 1:
            raise RuntimeError(f"Expected 1 model, got {matches}")
        glb = z.read(matches[0])
    if hashlib.sha256(glb).hexdigest() != GLB_SHA256:
        raise RuntimeError("Unverified GLB contents")
    dest = Path("site/hall/settlements_hall.glb")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(glb)
    print(f"SETTLEMENTS_HALL_WEB_READY {dest} {len(glb)} bytes")

if __name__ == "__main__":
    main()
