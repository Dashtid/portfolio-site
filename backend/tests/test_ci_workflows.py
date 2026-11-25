"""The CI workflows keep the guards their deploy and backup jobs rely on.

Each workflow under .github/workflows is parsed with PyYAML. The tests pin
the settings that decide which branch deploys, which job holds which token
scope, and what a deploy job checks before and after it ships.
"""

import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"


def _load(name: str) -> dict[Any, Any]:
    workflow = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    assert isinstance(workflow, dict), name
    return workflow


def _triggers(workflow: dict[Any, Any]) -> dict[str, Any]:
    # YAML 1.1 reads the bare key `on` as the boolean True.
    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict)
    return triggers


def _condition(job: dict[str, Any]) -> str:
    """A job's `if:` with its line breaks and indentation folded to single spaces."""
    return " ".join(str(job["if"]).split())


def test_the_pipeline_runs_for_main_only() -> None:
    triggers = _triggers(_load("ci-cd.yml"))
    assert {event: triggers[event]["branches"] for event in triggers} == {
        "push": ["main"],
        "pull_request": ["main"],
        "merge_group": ["main"],
    }


def test_deploys_and_push_e2e_runs_accept_main_only() -> None:
    jobs = _load("ci-cd.yml")["jobs"]
    for name in ("e2e-tests", "deploy-frontend", "deploy-backend"):
        condition = _condition(jobs[name])
        assert "github.ref == 'refs/heads/main'" in condition, name
        assert condition.count("github.ref") == 1, name


def test_the_rebake_deploys_from_main_only() -> None:
    rebake = _load("rebake-frontend.yml")["jobs"]["rebake"]
    assert _condition(rebake) == "github.ref == 'refs/heads/main'"


def test_only_the_backup_keepalive_job_holds_actions_write() -> None:
    # actions: write can delete the backup artifacts, so it stays out of the
    # jobs that hold the Fly tokens and the database password.
    backup = _load("db-backup.yml")
    assert backup["permissions"] == {"contents": "read"}
    holders = [
        name
        for name, job in backup["jobs"].items()
        if (job.get("permissions") or {}).get("actions") == "write"
    ]
    assert holders == ["keepalive"]
    keepalive = backup["jobs"]["keepalive"]
    assert keepalive["permissions"] == {"actions": "write"}
    [step] = keepalive["steps"]
    assert "uses" not in step
    assert "db-backup.yml/enable" in step["run"]
    assert "secrets." not in yaml.safe_dump(keepalive)
    # No `needs` either way: a failed enable call must not stop the dumps.
    assert all("needs" not in job for job in backup["jobs"].values())


def _uses(job: dict[str, Any], action: str) -> list[dict[str, Any]]:
    """The steps of `job` that run `action` (owner/repo), at any pinned ref."""
    return [step for step in job["steps"] if str(step.get("uses", "")).startswith(f"{action}@")]


@pytest.mark.parametrize(
    ("workflow", "job"), [("ci-cd.yml", "deploy-frontend"), ("rebake-frontend.yml", "rebake")]
)
def test_vercel_deploy_jobs_restore_no_npm_cache(workflow: str, job: str) -> None:
    # The npm cache is written by the jobs that run the frontend's test and
    # build tooling; the deploy jobs hold VERCEL_TOKEN and must not unpack it.
    [setup_node] = _uses(_load(workflow)["jobs"][job], "actions/setup-node")
    settings = setup_node["with"]
    assert "cache" not in settings
    assert "cache-dependency-path" not in settings
    assert settings["package-manager-cache"] is False


def test_no_checkout_leaves_the_job_token_on_disk() -> None:
    # No later step pushes or fetches with the job token, so a persisted copy
    # would only serve dependency code that reads it.
    checkouts = {
        f"{path.name}:{name}": step
        for path in sorted(WORKFLOWS.glob("*.yml"))
        for name, job in _load(path.name)["jobs"].items()
        for step in _uses(job, "actions/checkout")
    }
    assert len(checkouts) >= 13
    kept = [
        where
        for where, step in checkouts.items()
        if step.get("with", {}).get("persist-credentials") is not False
    ]
    assert kept == []


@pytest.mark.parametrize("name", ["deploy-frontend", "deploy-backend"])
def test_deploys_wait_for_the_security_scan_and_the_dependency_review(name: str) -> None:
    job = _load("ci-cd.yml")["jobs"][name]
    assert {"security-scan", "dependency-review"} <= set(job["needs"])
    condition = _condition(job)
    # Without !cancelled() a skipped dependency-review would skip the deploy.
    assert condition.startswith("!cancelled() && ")
    assert "needs.security-scan.result == 'success'" in condition
    assert (
        "(needs.dependency-review.result == 'success'"
        " || needs.dependency-review.result == 'skipped')"
    ) in condition


def test_dependency_review_also_checks_the_range_a_push_adds() -> None:
    review = _load("ci-cd.yml")["jobs"]["dependency-review"]
    assert _condition(review) == (
        "github.event_name == 'pull_request' || (github.event_name == 'push' && "
        "!github.event.forced && "
        "github.event.before != '0000000000000000000000000000000000000000')"
    )
    [step] = _uses(review, "actions/dependency-review-action")
    assert step["with"]["base-ref"] == (
        "${{ github.event_name == 'push' && github.event.before || '' }}"
    )
    assert step["with"]["head-ref"] == "${{ github.event_name == 'push' && github.sha || '' }}"


def test_frontend_deploys_and_rebakes_share_one_concurrency_group() -> None:
    # Group names span every workflow in the repository, so the two jobs that
    # run `vercel deploy --prod` wait for each other instead of overlapping.
    deploy = _load("ci-cd.yml")["jobs"]["deploy-frontend"]
    rebake_workflow = _load("rebake-frontend.yml")
    rebake = rebake_workflow["jobs"]["rebake"]
    group = {"group": "production-frontend", "cancel-in-progress": False}
    assert deploy["concurrency"] == group
    assert rebake["concurrency"] == group
    assert "concurrency" not in rebake_workflow
    assert isinstance(rebake["timeout-minutes"], int)


HEADER_CHECK = (
    "python3 scripts/check-live-headers.py frontend/vercel.json "
    "https://dashti.se/ https://dashti.se/colophon https://dashti.se/admin"
)


@pytest.mark.parametrize(
    ("workflow", "job"), [("ci-cd.yml", "deploy-frontend"), ("rebake-frontend.yml", "rebake")]
)
def test_frontend_deploys_end_by_holding_served_headers_to_vercel_json(
    workflow: str, job: str
) -> None:
    steps = _load(workflow)["jobs"][job]["steps"]
    assert steps[-1]["name"] == "Post-deploy security-header smoke"
    assert HEADER_CHECK in " ".join(steps[-1]["run"].replace("\\\n", " ").split())


def _path_filters() -> dict[str, list[str]]:
    filters = yaml.safe_load(_load("ci-cd.yml")["jobs"]["changes"]["env"]["PATH_FILTERS"])
    assert isinstance(filters, dict)
    return filters


def test_a_header_check_change_runs_its_tests_and_a_frontend_deploy() -> None:
    filters = _path_filters()
    assert "scripts/check-live-headers.py" in filters["frontend"]
    assert "scripts/check-live-headers.py" in filters["backend"]


def test_a_pin_check_change_runs_its_tests() -> None:
    assert "scripts/verify_action_pins.py" in _path_filters()["backend"]


def test_scorecard_runs_only_after_its_image_digest_check() -> None:
    jobs = _load("scorecard.yml")["jobs"]
    gate, analysis = jobs["image-pin"], jobs["analysis"]
    assert analysis["needs"] == "image-pin"
    assert gate["permissions"] == {"contents": "read"}
    [check] = [step for step in gate["steps"] if "run" in step]
    assert check["run"] == "python3 scripts/verify_action_pins.py --only ossf/scorecard-action"
    assert check["env"] == {"GITHUB_TOKEN": "${{ github.token }}"}
    # Publishing results takes an analysis job of `uses:` steps only, and an
    # id-token grant in no other job.
    assert all("uses" in step and "run" not in step for step in analysis["steps"])
    holders = [name for name, job in jobs.items() if "id-token" in job.get("permissions", {})]
    assert holders == ["analysis"]


def test_codeql_analyzes_the_workflows_as_well_as_the_code() -> None:
    analyze = _load("codeql.yml")["jobs"]["analyze"]
    assert analyze["strategy"]["matrix"]["language"] == [
        "actions",
        "javascript-typescript",
        "python",
    ]
    [init] = _uses(analyze, "github/codeql-action/init")
    assert init["with"]["languages"] == "${{ matrix.language }}"
    # One analysis per language, so each keeps its own alerts.
    [step] = _uses(analyze, "github/codeql-action/analyze")
    assert step["with"]["category"] == "/language:${{ matrix.language }}"


def test_every_artifact_upload_sets_its_retention_and_lighthouse_uploads_none() -> None:
    # Without retention-days an artifact stays for the repository default.
    uploads = [
        (key, step)
        for key, job in _all_jobs().items()
        for step in _uses(job, "actions/upload-artifact")
    ]
    assert len(uploads) >= 6
    unset = [
        key for key, step in uploads if not isinstance(step["with"].get("retention-days"), int)
    ]
    assert unset == []
    # The Lighthouse action's own upload takes no retention setting, so its
    # reports go only to temporary public storage.
    [lighthouse] = _uses(_load("ci-cd.yml")["jobs"]["lighthouse"], "treosh/lighthouse-ci-action")
    assert lighthouse["with"]["uploadArtifacts"] is False
    assert lighthouse["with"]["temporaryPublicStorage"] is True


def test_the_image_scan_reads_the_runtime_base_weekly_and_gates_no_deploy() -> None:
    workflow = _load("image-scan.yml")
    triggers = _triggers(workflow)
    assert set(triggers) == {"schedule", "push", "pull_request", "workflow_dispatch"}
    for event in ("push", "pull_request"):
        assert triggers[event]["branches"] == ["main"]
        assert triggers[event]["paths"] == [
            "backend/Dockerfile",
            ".github/workflows/image-scan.yml",
        ]
    assert workflow["permissions"] == {"contents": "read"}
    # Not security-scan, the check main's ruleset requires: a base with a
    # fixable vulnerability must not hold up unrelated pull requests.
    [(name, job)] = workflow["jobs"].items()
    assert name == "image-scan"
    assert job["permissions"] == {"contents": "read", "security-events": "write"}
    assert "needs" not in job
    assert "secrets." not in yaml.safe_dump(workflow)
    # The scanner image is pinned by digest.
    image = job["env"]["GRYPE_IMAGE"]
    assert re.fullmatch(r"ghcr\.io/anchore/grype:v\d+\.\d+\.\d+@sha256:[0-9a-f]{64}", image)
    steps = {step["name"]: step for step in job["steps"]}
    scan = steps["Scan the base image"]
    assert scan["env"] == {"IMAGE_REF": "${{ steps.base.outputs.ref }}"}
    run = " ".join(scan["run"].replace("\\\n", " ").split())
    assert '"${GRYPE_IMAGE}" "registry:${IMAGE_REF}" --platform linux/amd64 --only-fixed' in run
    [upload] = _uses(job, "github/codeql-action/upload-sarif")
    assert upload["with"] == {
        "sarif_file": "${{ runner.temp }}/grype/high.sarif",
        "category": "grype-image",
    }
    # The gate runs last, after the upload.
    names = list(steps)
    assert names.index(upload["name"]) == len(names) - 2
    assert names[-1] == "Fail while a High or Critical match has a fix"


def test_both_dockerfile_stages_share_one_base_pinned_by_digest() -> None:
    # The image scan reads the last FROM; production runs the runtime stage.
    dockerfile = (WORKFLOWS.parents[1] / "backend" / "Dockerfile").read_text(encoding="utf-8")
    bases = [line.split()[1] for line in dockerfile.splitlines() if line.startswith("FROM ")]
    assert len(bases) == 2
    assert bases[0] == bases[1]
    assert re.fullmatch(r"[^@\s]+@sha256:[0-9a-f]{64}", bases[-1])
    # The scan covers the base alone: an OS package the runtime stage
    # installed would reach production unscanned.
    runtime = dockerfile[dockerfile.rindex("\nFROM ") :]
    assert "apt-get" not in runtime


def test_the_changes_job_needs_no_fetch_after_checkout() -> None:
    # With full history the filters find their base commits locally; a
    # depth-1 clone would make them fetch, and without credentials.
    [checkout] = _uses(_load("ci-cd.yml")["jobs"]["changes"], "actions/checkout")
    assert checkout["with"] == {"fetch-depth": 0, "persist-credentials": False}


def test_a_push_also_filters_the_range_since_each_half_last_deployed() -> None:
    jobs = _load("ci-cd.yml")["jobs"]
    changes = jobs["changes"]
    assert changes["permissions"] == {"contents": "read", "deployments": "read"}
    steps = {step["id"]: step for step in changes["steps"] if "id" in step}
    # One copy of the path rules for the push's own range and both drift ranges.
    for step_id in ("filter", "frontend-drift", "backend-drift"):
        assert steps[step_id]["uses"] == steps["filter"]["uses"]
        assert steps[step_id]["with"]["filters"] == "${{ env.PATH_FILTERS }}"
    assert "scripts/deployed-commits.py" in _path_filters()["backend"]

    deployed = steps["deployed"]
    assert deployed["if"] == "github.event_name == 'push'"
    assert deployed["continue-on-error"] is True
    run = " ".join(deployed["run"].replace("\\\n", " ").split())
    # The script looks deploys up by the environment and URLs the deploy jobs
    # declare, and a rebake declares deploy-frontend's.
    frontend, backend = (
        jobs["deploy-frontend"]["environment"],
        jobs["deploy-backend"]["environment"],
    )
    rebake = _load("rebake-frontend.yml")["jobs"]["rebake"]["environment"]
    assert frontend["name"] == backend["name"] == rebake["name"]
    assert rebake["url"] == frontend["url"]
    assert run == (
        f"python3 scripts/deployed-commits.py {frontend['name']} "
        f"frontend={frontend['url']} backend={backend['url']}"
    )
    for half in ("frontend", "backend"):
        drift = steps[f"{half}-drift"]
        assert drift["if"] == f"steps.deployed.outputs.{half} != ''"
        assert drift["continue-on-error"] is True
        assert drift["with"]["base"] == f"${{{{ steps.deployed.outputs.{half} }}}}"
        # Anything but an explicit 'false' from the drift filter runs the half.
        assert " ".join(changes["outputs"][half].split()) == (
            f"${{{{ steps.filter.outputs.{half} == 'true' || (github.event_name == 'push' && "
            f"steps.{half}-drift.outputs.{half} != 'false') }}}}"
        )


def _all_jobs() -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (path.name, name): job
        for path in sorted(WORKFLOWS.glob("*.yml"))
        for name, job in _load(path.name)["jobs"].items()
    }


FLYCTL_JOBS = [
    ("ci-cd.yml", "deploy-backend"),
    ("db-backup.yml", "backup"),
    ("db-backup.yml", "uploads"),
]


def test_flyctl_comes_from_a_committed_sha256_wherever_it_runs() -> None:
    # flyctl's release assets can be replaced, and setup-flyctl downloads the
    # URL api.fly.io names without checking a hash.
    jobs = _all_jobs()
    runs_flyctl = [
        key
        for key, job in jobs.items()
        if any(
            "flyctl " in str(step.get("run", ""))
            for step in job.get("steps", [])
            if step.get("name") != "Install flyctl"
        )
    ]
    assert sorted(runs_flyctl) == FLYCTL_JOBS
    used = [
        step["uses"] for job in jobs.values() for step in job.get("steps", []) if "uses" in step
    ]
    assert not [ref for ref in used if ref.startswith("superfly/")]

    installs = []
    for key in FLYCTL_JOBS:
        steps = jobs[key]["steps"]
        [install] = [step for step in steps if step.get("name") == "Install flyctl"]
        tokens = [i for i, step in enumerate(steps) if "FLY_API_TOKEN" in step.get("env", {})]
        assert tokens, key
        assert steps.index(install) < min(tokens), key
        installs.append(install)
    # One version and one hash: the three copies move together.
    assert installs[0] == installs[1] == installs[2]
    env = installs[0]["env"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", env["FLYCTL_VERSION"])
    assert re.fullmatch(r"[0-9a-f]{64}", env["FLYCTL_SHA256"])
    run = installs[0]["run"]
    assert run.startswith("set -euo pipefail\n")
    check = run.index('echo "${FLYCTL_SHA256}  ${ARCHIVE}" | sha256sum --check --strict')
    assert check < run.index('tar -xzf "${ARCHIVE}" flyctl') < run.index('>> "${GITHUB_PATH}"')


def test_apt_trusts_only_the_pgdg_key_with_the_published_fingerprint() -> None:
    steps = _load("db-backup.yml")["jobs"]["backup"]["steps"]
    [step] = [s for s in steps if s.get("name") == "Install postgresql client"]
    # The fingerprint postgresql.org publishes for its ACCC4CF8.asc key.
    assert step["env"] == {"PGDG_FINGERPRINT": "B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8"}
    run = step["run"]
    assert run.startswith("set -euo pipefail\n")
    # No dearmor of the fetched file: that would trust every key it holds.
    assert "--dearmor" not in run
    export = run.index('gpg --batch --export "${PGDG_FINGERPRINT}"')
    only_primary = run.index('test "${PRIMARY}" = "${PGDG_FINGERPRINT}"')
    keyring = run.index("sudo install -m 0644")
    assert export < only_primary < keyring < run.index("apt-get update")


TOOLS = WORKFLOWS.parent / "tools" / "vercel"
NATIVE = "@vercel/vc-native-linux-x64"
LOCKED_CLI = f'"${{RUNNER_TEMP}}/vercel-cli/node_modules/{NATIVE}/bin/vercel"'
INSTALL = "bash .github/tools/vercel/install.sh"


def _vercel_install(steps: list[dict[str, Any]]) -> dict[str, Any]:
    [install] = [step for step in steps if step.get("name") == "Install Vercel CLI"]
    return install


@pytest.mark.parametrize(
    ("workflow", "job"), [("ci-cd.yml", "deploy-frontend"), ("rebake-frontend.yml", "rebake")]
)
def test_the_token_step_runs_the_vercel_cli_installed_from_its_lock(
    workflow: str, job: str
) -> None:
    steps = _load(workflow)["jobs"][job]["steps"]
    install = _vercel_install(steps)
    [deploy] = [step for step in steps if "VERCEL_TOKEN" in step.get("env", {})]
    assert steps.index(install) < steps.index(deploy)
    assert deploy["run"].startswith(f"{LOCKED_CLI} deploy --prod --yes")
    # One install script for both production paths.
    assert install["run"] == INSTALL


def test_the_vercel_cli_install_takes_only_the_lock_and_checks_the_binary_version() -> None:
    script = (TOOLS / "install.sh").read_text(encoding="utf-8")
    assert script.startswith("#!/usr/bin/env bash\n")
    assert "npm install" not in script
    in_order = [
        "set -euo pipefail",
        'target="${RUNNER_TEMP}/vercel-cli"',
        'cp "${here}/package.json" "${here}/package-lock.json" "${target}/"',
        'cd "${target}"',
        "npm ci --ignore-scripts --no-audit --no-fund",
        f"cli=node_modules/{NATIVE}\n",
        'test -x "${cli}/bin/vercel"',
        """want=$(node -p "require('./${cli}/package.json').version")""",
        '"${cli}/bin/vercel" --version | tee version.txt',
        'grep -qxF "${want}" version.txt',
    ]
    positions = [script.index(line) for line in in_order]
    assert positions == sorted(positions)
    # The binary prints its bare version on stdout; the banner on stderr has
    # changed shape between releases.
    assert "2>&1" not in script


def test_pull_requests_run_the_vercel_cli_install_without_secrets() -> None:
    workflow = _load("ci-cd.yml")
    job = workflow["jobs"]["vercel-cli"]
    assert job["needs"] == "changes"
    assert _condition(job) == (
        "github.event_name == 'pull_request' && needs.changes.outputs.frontend == 'true'"
    )
    # The workflow's contents: read, and nothing a deploy holds.
    assert "permissions" not in job
    assert workflow["permissions"] == {"contents": "read"}
    assert "secrets." not in yaml.safe_dump(job)
    assert _vercel_install(job["steps"])["run"] == INSTALL
    [setup_node] = _uses(job, "actions/setup-node")
    deploy = _load("ci-cd.yml")["jobs"]["deploy-frontend"]
    assert setup_node["with"] == _uses(deploy, "actions/setup-node")[0]["with"]


def test_the_vercel_cli_lock_holds_only_the_native_binary_from_the_registry() -> None:
    package = json.loads((TOOLS / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((TOOLS / "package-lock.json").read_text(encoding="utf-8"))
    # Deploy tooling, like the frontend's build tools: scanners scope it as
    # development, not as code the site serves.
    assert "dependencies" not in package
    assert list(package["devDependencies"]) == [NATIVE]
    version = package["devDependencies"][NATIVE]
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    assert lock["packages"][""]["devDependencies"] == package["devDependencies"]
    # The binary's package alone: no launcher and no JavaScript fallback tree.
    entries = {path: meta for path, meta in lock["packages"].items() if path}
    assert list(entries) == [f"node_modules/{NATIVE}"]
    [meta] = entries.values()
    assert meta["version"] == version
    assert meta["resolved"] == (
        f"https://registry.npmjs.org/{NATIVE}/-/vc-native-linux-x64-{version}.tgz"
    )
    assert meta["integrity"].startswith("sha512-")
    assert meta["dev"] is True
    assert (meta["os"], meta["cpu"], meta["libc"]) == (["linux"], ["x64"], ["glibc"])
    assert not {"dependencies", "optionalDependencies", "hasInstallScript", "bin"} & set(meta)


def test_vercel_cli_bumps_wait_out_the_cooldown_and_run_the_frontend_half() -> None:
    config = yaml.safe_load((WORKFLOWS.parent / "dependabot.yml").read_text(encoding="utf-8"))
    [entry] = [u for u in config["updates"] if u["directory"] == "/.github/tools/vercel"]
    assert entry["package-ecosystem"] == "npm"
    assert entry["cooldown"] == {"default-days": 7}
    assert ".github/tools/vercel/**" in _path_filters()["frontend"]


FRONTEND = WORKFLOWS.parents[1] / "frontend"


def test_ci_and_vercel_use_the_node_major_that_package_json_declares() -> None:
    package = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((FRONTEND / "package-lock.json").read_text(encoding="utf-8"))
    # Vercel builds production with engines.node and takes a major only.
    node = package["engines"]["node"]
    assert re.fullmatch(r"\d+\.x", node)
    assert lock["packages"][""]["engines"] == package["engines"]
    # Type definitions for a newer Node major describe APIs the runtime lacks.
    major = node.removesuffix(".x")
    assert re.fullmatch(rf"\^{major}\.\d+\.\d+", package["devDependencies"]["@types/node"])
    setups = [
        (key, step) for key, job in _all_jobs().items() for step in _uses(job, "actions/setup-node")
    ]
    assert len(setups) >= 4
    for key, step in setups:
        assert step["with"]["node-version-file"] == "frontend/package.json", key
        assert "node-version" not in step["with"], key
