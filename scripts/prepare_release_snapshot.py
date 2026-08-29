#!/usr/bin/env python3
"""Copy commit-eligible files into a clean, isolated local validation repository.

Does not commit, stage, fetch, push or tag in the user's checkout. The resulting
local snapshot commit is evidence, not a public release commit. Ignored data
cannot accidentally make a fresh-clone test pass. No historical Git objects
or ignored caches are copied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def prepare(root=ROOT):
    destination = Path(tempfile.mkdtemp(prefix="cubedynamics-rc-source-"))
    # Git supplies unchanged bytes, including cloud-placeholder files that are
    # present in the commit but not hydrated in the desktop filesystem.
    process = subprocess.Popen(["git", "archive", "HEAD"], cwd=root, stdout=subprocess.PIPE)
    with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
        for member in archive:
            if member.name.startswith("/") or ".." in Path(member.name).parts or member.issym() or member.islnk():
                raise RuntimeError("Unsafe archive member")
            archive.extract(member, destination)
    if process.wait() != 0:
        raise RuntimeError("Could not export committed source")
    names = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD", "-z"], cwd=root
    ).decode().split("\0")
    names += subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=root
    ).decode().split("\0")
    hashes = {}
    for name in sorted(set(names) - {""}):
        source = root / name
        if not source.exists():
            (destination / name).unlink(missing_ok=True)
            continue
        if source.is_symlink() or not source.is_file():
            raise RuntimeError(f"Unexpected release input: {name}")
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    hashes = {str(p.relative_to(destination)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(destination.rglob("*")) if p.is_file()}
    subprocess.run(["git", "init", "-q", destination], check=True)
    # Explicit path list includes tracked exceptions that match an ignore rule.
    subprocess.run(["git", "add", "-f", "--", *hashes], cwd=destination, check=True)
    subprocess.run(["git", "-c", "user.name=CubeDynamics release validation",
                    "-c", "user.email=release-validation@localhost", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "Isolated RC validation snapshot; not a public release"],
                   cwd=destination, check=True)
    result = {"source_checkout": str(root), "snapshot": str(destination),
              "base_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
              "snapshot_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=destination, text=True).strip(),
              "files": hashes, "publication": "NONE; local validation snapshot only"}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = prepare()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(record["snapshot"])
