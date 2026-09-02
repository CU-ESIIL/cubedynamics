"""Runtime identity for notebooks, installed artifacts, and source checkouts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import metadata
import json
from pathlib import Path
from typing import Any

from .version import __version__


@dataclass(frozen=True)
class RuntimeInfo:
    """Inspect which CubeDynamics code the current Python process imported."""

    version: str
    package_location: str
    distribution_location: str | None
    artifact_kind: str
    source_identity: str
    git_sha: str | None = None
    source_url: str | None = None
    editable: bool = False

    @property
    def development(self) -> bool:
        """Whether the import comes from development/VCS source metadata."""

        return self.artifact_kind in {"development checkout", "VCS installation"}

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-serializable record."""

        result = asdict(self)
        result["development"] = self.development
        return result

    def __str__(self) -> str:
        lines = [
            f"CubeDynamics {self.version}",
            f"Artifact: {self.artifact_kind}",
            f"Code: {self.source_identity}",
            f"Imported from: {self.package_location}",
        ]
        if self.distribution_location:
            lines.append(f"Distribution: {self.distribution_location}")
        return "\n".join(lines)


def version_info() -> RuntimeInfo:
    """Return package version, import location, and source/release identity.

    The semantic version can intentionally remain unchanged while work
    continues on ``main``. This helper therefore reports the imported path and
    a Git/VCS commit when available. It performs no network access.
    """

    package_location = Path(__file__).resolve().parent
    distribution_location: str | None = None
    source_url: str | None = None
    direct_commit: str | None = None
    editable = False
    direct_url: dict[str, Any] = {}
    try:
        dist = metadata.distribution("cubedynamics")
        distribution_location = str(Path(dist.locate_file("")).resolve())
        text = dist.read_text("direct_url.json")
        if text:
            direct_url = json.loads(text)
    except (metadata.PackageNotFoundError, OSError, ValueError, json.JSONDecodeError):
        pass

    if direct_url:
        source_url = direct_url.get("url")
        editable = bool(direct_url.get("dir_info", {}).get("editable", False))
        direct_commit = direct_url.get("vcs_info", {}).get("commit_id")

    git_root = _find_git_root(package_location)
    checkout_sha = _read_git_sha(git_root) if git_root else None
    git_sha = checkout_sha or direct_commit
    if git_root is not None:
        artifact_kind = "development checkout"
        source_identity = f"git:{git_sha or 'commit unavailable'}"
        source_url = source_url or str(git_root)
    elif direct_commit or direct_url.get("vcs_info"):
        artifact_kind = "VCS installation"
        source_identity = f"git:{git_sha or 'commit unavailable'}"
    else:
        artifact_kind = "published or built distribution"
        source_identity = f"cubedynamics=={__version__}"

    return RuntimeInfo(
        version=__version__,
        package_location=str(package_location),
        distribution_location=distribution_location,
        artifact_kind=artifact_kind,
        source_identity=source_identity,
        git_sha=git_sha,
        source_url=source_url,
        editable=editable,
    )


def _find_git_root(path: Path) -> Path | None:
    for parent in (path, *path.parents):
        if (parent / ".git").exists():
            return parent
    return None


def _read_git_sha(root: Path) -> str | None:
    git_entry = root / ".git"
    git_dir = git_entry
    try:
        if git_entry.is_file():
            pointer = git_entry.read_text(encoding="utf-8").strip()
            if not pointer.startswith("gitdir:"):
                return None
            git_dir = (root / pointer.split(":", 1)[1].strip()).resolve()
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
        if not head.startswith("ref:"):
            return head or None
        ref = head.split(":", 1)[1].strip()
        loose = git_dir / ref
        if loose.exists():
            return loose.read_text(encoding="utf-8").strip() or None
        packed = git_dir / "packed-refs"
        if packed.exists():
            for line in packed.read_text(encoding="utf-8").splitlines():
                if line and not line.startswith(("#", "^")):
                    sha, name = line.split(" ", 1)
                    if name == ref:
                        return sha
    except (OSError, ValueError):
        return None
    return None


__all__ = ["RuntimeInfo", "version_info"]
