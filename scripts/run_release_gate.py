#!/usr/bin/env python3
"""Non-publishing release gate: build, isolate, reproduce, and record evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MANDATORY = {
    "build", "twine", "contents", "create-environment", "upgrade-installer", "install-wheel", "pip-check",
    "package-only", "readme", "candidate-wheel", "install-vignette-extra", "wheel-vignettes",
    "offline", "streaming", "vignettes", "publication", "source-qa", "decision-qa",
    "visuals", "references", "noun-figures", "streamflow-notebook", "source-projects",
    "docs", "links", "browser", "repository-size", "diff-check",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def release_inputs():
    paths = [ROOT / n for n in ("pyproject.toml", "MANIFEST.in", "CITATION.cff", "README.md")]
    paths += [p for p in (ROOT / "src").rglob("*") if p.is_file() and (p.suffix in {".py", ".html", ".json"})]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}


def write_candidate(output):
    from source_lifecycle_evidence import release_manifest
    from check_release_artifact import artifact_info
    gate = json.loads((output / "gate.json").read_text())
    steps = gate["steps"]
    if gate["status"] != "PASS" or not MANDATORY <= steps.keys() or any(v["exit_code"] != 0 for v in steps.values()):
        raise RuntimeError("Every mandatory release gate must pass before recording a ready candidate")
    if gate["release_inputs"] != release_inputs():
        raise RuntimeError("Release inputs changed since validation; rerun the complete gate")
    installed = json.loads((output / "installed.json").read_text())
    notebooks = json.loads((output / "wheel-notebooks/execution.json").read_text())
    wheel = ROOT / "dist" / installed["wheel"]["filename"]
    sdist = ROOT / "dist" / installed["sdist"]["filename"]
    if artifact_info(wheel) != installed["wheel"] or artifact_info(sdist) != installed["sdist"]:
        raise RuntimeError("Distribution changed after the installed-wheel test")
    destination = ROOT / "manifests/releases/v0.1.0-candidate.json"
    result = release_manifest(destination, reports=[output / "offline.xml", output / "streaming.xml", output / "browser.xml"],
                              qa_roots=[output / "source_qa", output / "decision_qa"])
    if {r["notebook"] for r in notebooks} != set(result["supported_notebooks"]):
        raise RuntimeError("Wheel execution did not cover every supported notebook")
    if any(r["installed_wheel"]["wheel"]["sha256"] != installed["wheel"]["sha256"] for r in notebooks):
        raise RuntimeError("Notebooks used different wheels")
    result.update(
        target_version="0.1.0", maturity="first public alpha; not published",
        readiness="READY FOR v0.1.0rc1", artifact_version="0.1.0",
        rc_label_note="Review readiness only; no rc tag/version was created.",
        artifacts={"wheel": installed["wheel"], "sdist": installed["sdist"]},
        tested_python_versions=sorted({gate["python"], installed["installation"]["python"]}),
        tested_platform=gate["platform"], configured_matrix_note="Other CI Python targets are not claimed as locally exercised.",
        candidate_adapters={"usgs": "cubedynamics.data.usgs.streamflow", "usgs_3dep": "cubedynamics.data.three_dep.elevation",
                            "overture": "cubedynamics.data.roads.roads", "osm": "cubedynamics.data.roads.roads"},
        candidate_serving_revision=None, known_blocked_sources=["daymet"], live_source_checks="NOT_RUN; no new live PASS claimed",
        source_qa_status=json.loads((output / "source_qa/manifest.json").read_text())["status"],
        publication_status=json.loads((output / "validation/suite_manifest.json").read_text())["status"],
        decision_qa_status=json.loads((output / "decision_qa/result.json").read_text())["status"],
        package_only=installed["package_only"], canonical_example=installed["readme_example"],
        wheel_vignettes=[{"notebook": r["notebook"], "plots": r["plots"]} for r in notebooks],
        release_gate={"path": str((output / "gate.json").relative_to(ROOT)), "sha256": sha(output / "gate.json"),
                      "steps": {k: v["exit_code"] for k, v in steps.items()}},
        known_caveats=["Base commit plus recorded working-tree overlay, not a tagged release.",
                      "Provider availability and scientific suitability are separate from offline fixture QA.",
                      "Candidate APIs remain unpromoted; coaching/report schemas may evolve.",
                      "Broad base dependencies retained; full matrix and lower-bound dependency coverage are CI/future work.",
                      "No DOI assigned; no permission, tag, publication or source-promotion action performed."],
    )
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/release-0.1.0")
    parser.add_argument("--record-only", action="store_true", help="Refresh curated manifest from already passed, unchanged artifact evidence")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.record_only:
        write_candidate(output)
        return
    output.mkdir(parents=True, exist_ok=True)
    environment = Path(tempfile.mkdtemp(prefix="cubedynamics-wheel-")) / "venv"
    wheel_python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    py = sys.executable
    env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHONHOME"}}
    env.update(MPLCONFIGDIR=str(output / "matplotlib"), MPLBACKEND="Agg", PYTHONUNBUFFERED="1")
    gate = {"status": "RUNNING", "python": platform.python_version(), "platform": platform.platform(),
            "started": datetime.now(timezone.utc).isoformat(), "environment": str(environment),
            "release_inputs": release_inputs(), "steps": {}}
    def save():
        (output / "gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    def run(name, command, cwd=ROOT):
        print(f"RUN {name}", flush=True)
        log = output / f"{name}.log"
        with log.open("w") as stream:
            completed = subprocess.run([str(p) for p in command], cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
        gate["steps"][name] = {"command": [str(p) for p in command], "cwd": str(cwd), "exit_code": completed.returncode,
                               "log": str(log.relative_to(ROOT)), "log_sha256": sha(log)}
        save()
        if completed.returncode:
            raise RuntimeError(f"{name} failed; inspect {log}")
        print(f"PASS {name}", flush=True)
    save()
    try:
        run("build", [py, "-m", "build"])
        wheel = ROOT / "dist/cubedynamics-0.1.0-py3-none-any.whl"
        sdist = ROOT / "dist/cubedynamics-0.1.0.tar.gz"
        run("twine", [py, "-m", "twine", "check", wheel, sdist])
        checker = ROOT / "scripts/check_release_artifact.py"
        run("contents", [py, checker, "--wheel", wheel, "--sdist", sdist, "--inspect-only", "--output", output / "distributions.json"])
        run("create-environment", [py, "-m", "venv", environment])
        # venv seeds pip independently of the build interpreter. Old seeds can
        # omit direct_url archive hashes, which the identity check must reject.
        run("upgrade-installer", [wheel_python, "-m", "pip", "install", "--upgrade", "pip"], environment.parent)
        run("install-wheel", [wheel_python, "-m", "pip", "install", wheel], environment.parent)
        run("pip-check", [wheel_python, "-m", "pip", "check"], environment.parent)
        run("base-resolution", [wheel_python, "-m", "pip", "freeze", "--all"], environment.parent)
        run("package-only", [wheel_python, "-I", checker, "--wheel", wheel, "--sdist", sdist, "--output", output / "package-only.json"], environment.parent)
        run("readme", [wheel_python, "-I", checker, "--wheel", wheel, "--sdist", sdist, "--repo-example", "--output", output / "installed.json"], environment.parent)
        run("candidate-wheel", [wheel_python, "-I", ROOT / "scripts/check_candidate_wheel.py"], environment.parent)
        run("install-vignette-extra", [wheel_python, "-m", "pip", "install", str(wheel) + "[vignettes]"], environment.parent)
        run("vignette-resolution", [wheel_python, "-m", "pip", "freeze", "--all"], environment.parent)
        run("wheel-vignettes", [py, "scripts/run_vignettes.py", "--wheel", wheel, "--kernel-python", wheel_python,
                                "--output-dir", output / "wheel-notebooks"])
        run("offline", [py, "-m", "pytest", "-m", "not integration and not online", "-q", "--junitxml", output / "offline.xml"])
        from source_lifecycle_evidence import STREAMING
        run("streaming", [py, "-m", "pytest", *STREAMING, "-q", "--junitxml", output / "streaming.xml"])
        run("vignettes", [py, "scripts/run_vignettes.py", "--output-dir", output / "checkout-notebooks"])
        run("publication", [py, "scripts/run_validation.py", "--run-vignettes", "--output", output / "validation"])
        run("source-qa", [py, "scripts/run_source_qa.py", "--output", output / "source_qa"])
        run("decision-qa", [py, "scripts/run_decision_qa.py", "--output", output / "decision_qa"])
        for name, script in (("visuals", "build_visual_docs"), ("references", "build_reference_docs"),
                             ("noun-figures", "build_source_vignettes"), ("streamflow-notebook", "build_streamflow_vignette"),
                             ("source-projects", "build_source_project_docs")):
            run(name, [py, f"scripts/{script}.py", "--check"])
        run("docs", [py, "-m", "mkdocs", "build", "--strict"])
        run("links", [py, "scripts/check_site_links.py", "site"])
        run("browser", [py, "-m", "pytest", "tests/browser", "-m", "browser", "--site-dir", "site", "--browser", "chromium",
                        "--tracing", "retain-on-failure", "--output", output / "browser", "--junitxml", output / "browser.xml", "-q"])
        run("repository-size", [py, "scripts/check_repository_size.py", "--mode", "tracked"])
        run("diff-check", ["git", "diff", "--check"])
        gate["status"] = "PASS"
        save()
        write_candidate(output)
    except Exception:
        gate["status"] = "FAIL"
        save()
        raise


if __name__ == "__main__":
    main()
