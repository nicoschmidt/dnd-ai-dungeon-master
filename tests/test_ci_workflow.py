"""The main ruleset requires one check, `CI passed`, and nothing else.

That only holds if the `ci-passed` job waits for every other job and runs
even when one of them failed. Forgetting either would make a job optional
without anybody noticing, so both are checked here.
"""

from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci.yml"
GATE = "ci-passed"


def _jobs() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())["jobs"]


def test_the_gate_waits_for_every_other_job() -> None:
    jobs = _jobs()
    others = set(jobs) - {GATE}

    missing = sorted(others - set(jobs[GATE]["needs"]))

    assert not missing, (
        f"Jobs not listed in `{GATE}.needs` in {WORKFLOW.name}, so not required "
        f"for a merge: {', '.join(missing)}"
    )


def test_the_gate_runs_even_when_a_job_failed() -> None:
    assert _jobs()[GATE]["if"] == "always()"
