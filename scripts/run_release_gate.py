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
    "docs", "links", "browser", "repository-size", "diff-check", "hero-examples", "source-identity", "external-quickstart",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def release_inputs():
    # Bind docs, tests, workflows and fixtures too, not only packaged Python.
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).decode().split("\0")
    return {name: sha(ROOT / name) if (ROOT / name).is_file() else "deleted"
            for name in sorted(set(names)) if name and name != "manifests/releases/v0.1.0rc1-candidate.json"}


def check_commit(gate):
    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if current != gate["git_sha"]:
        raise RuntimeError("Source commit changed since validation")


def step_environment(base, name):
    """Headless plots for scripts; inline MIME outputs for the website's kernels."""
    result = dict(base)
    if name == "docs":
        # Agg alone makes plt.show() a no-op in MkDocs-Jupyter. The separate
        # notebook runner already selects inline, but the website executes its
        # own kernels and must emit actual PNGs too.
        result["MPLBACKEND"] = "module://matplotlib_inline.backend_inline"
    return result


def write_candidate(output):
    from source_lifecycle_evidence import release_manifest
    from check_release_artifact import artifact_info
    gate = json.loads((output / "gate.json").read_text())
    steps = gate["steps"]
    if gate["status"] != "PASS" or not MANDATORY <= steps.keys() or any(v["exit_code"] != 0 for v in steps.values()):
        raise RuntimeError("Every mandatory release gate must pass before recording a ready candidate")
    if not gate["release_inputs"] or gate["release_inputs"] != release_inputs():
        raise RuntimeError("Release inputs changed since validation; rerun the complete gate")
    check_commit(gate)
    installed = json.loads((output / "installed.json").read_text())
    notebooks = json.loads((output / "wheel-notebooks/execution.json").read_text())
    wheel = ROOT / "dist" / installed["wheel"]["filename"]
    sdist = ROOT / "dist" / installed["sdist"]["filename"]
    if artifact_info(wheel) != installed["wheel"] or artifact_info(sdist) != installed["sdist"]:
        raise RuntimeError("Distribution changed after the installed-wheel test")
    destination = ROOT / "manifests/releases/v0.1.0rc1-candidate.json"
    result = release_manifest(destination, reports=[output / "offline.xml", output / "streaming.xml", output / "browser.xml"],
                              qa_roots=[output / "source_qa", output / "decision_qa"])
    if {r["notebook"] for r in notebooks} != set(result["supported_notebooks"]):
        raise RuntimeError("Wheel execution did not cover every supported notebook")
    if any(r["installed_wheel"]["wheel"]["sha256"] != installed["wheel"]["sha256"] for r in notebooks):
        raise RuntimeError("Notebooks used different wheels")
    result.update(
        target_version="0.1.0rc1", maturity="first release candidate; not published",
        readiness="LOCAL GATE PASS; publication requires reviewed commit and matrix evidence",
        artifact_version="0.1.0rc1",
        rc_label_note="Real prerelease version; no tag or publication performed.",
        tested_git_sha=gate["git_sha"], tested_tree_sha=gate["git_tree"],
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
        known_caveats=["Prepared source snapshot is not a public tag or release.",
                      "Provider availability and scientific suitability are separate from offline fixture QA.",
                      "Candidate APIs remain unpromoted; coaching/report schemas may evolve.",
                      "Broad base dependencies retained; full matrix and lower-bound dependency coverage are CI/future work.",
                      "No DOI assigned; no permission, tag, publication or source-promotion action performed."],
    )
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/release-0.1.0rc1")
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
            "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "git_tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True).strip(),
            "started": datetime.now(timezone.utc).isoformat(), "environment": str(environment),
            "release_inputs": release_inputs(), "steps": {}}
    def save():
        (output / "gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    def run(name, command, cwd=ROOT):
        print(f"RUN {name}", flush=True)
        log = output / f"{name}.log"
        with log.open("w") as stream:
            completed = subprocess.run([str(p) for p in command], cwd=cwd, env=step_environment(env, name), stdout=stream, stderr=subprocess.STDOUT)
        gate["steps"][name] = {"command": [str(p) for p in command], "cwd": str(cwd), "exit_code": completed.returncode,
                               "log": str(log.relative_to(ROOT)), "log_sha256": sha(log)}
        save()
        if completed.returncode:
            raise RuntimeError(f"{name} failed; inspect {log}")
        print(f"PASS {name}", flush=True)
    save()
    try:
        run("source-identity", [py, "scripts/check_release_source.py"])
        run("build", [py, "-m", "build"])
        wheel = ROOT / "dist/cubedynamics-0.1.0rc1-py3-none-any.whl"
        sdist = ROOT / "dist/cubedynamics-0.1.0rc1.tar.gz"
        run("twine", [py, "-m", "twine", "check", wheel, sdist])
        (ROOT / "dist/SHA256SUMS").write_text("".join(f"{sha(p)}  {p.name}\n" for p in (wheel, sdist)))
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
        run("external-quickstart", [wheel_python, "-I", ROOT / "scripts/check_external_quickstart.py", "--wheel", wheel,
                                    "--output", output / "external-quickstart.json"], environment.parent)
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
                             ("source-projects", "build_source_project_docs"), ("hero-examples", "build_real_data_assets")):
            run(name, [py, f"scripts/{script}.py", "--check"])
        run("docs", [py, "-m", "mkdocs", "build", "--strict"])
        run("links", [py, "scripts/check_site_links.py", "site"])
        run("browser", [py, "-m", "pytest", "tests/browser", "-m", "browser", "--site-dir", "site", "--browser", "chromium",
                        "--tracing", "retain-on-failure", "--output", output / "browser", "--junitxml", output / "browser.xml", "-q"])
        run("repository-size", [py, "scripts/check_repository_size.py", "--mode", "tracked"])
        run("diff-check", ["git", "diff", "--check"])
        if gate["release_inputs"] != release_inputs():
            raise RuntimeError("Release inputs changed during validation")
        check_commit(gate)
        gate["status"] = "PASS"
        save()
        write_candidate(output)
    except Exception:
        gate["status"] = "FAIL"
        save()
        raise


if __name__ == "__main__":
    main()
