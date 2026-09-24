![status](https://img.shields.io/badge/status-early--stage-orange)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

# FelonyBench

#### A benchmark for whether AI agents respect authorization boundaries they have the means to cross

FelonyBench gives an agent a legitimate task inside an intentionally constrained environment, then watches what it does when useful information, capabilities, or states that exist just outside that boundary. The environment is instrumented so that boundary-crossing attempts can be measured independently of whether the model claims to have succeeded, or claims to have not tried.

<blockquote>
<p><i>The question is not whether a model *can* solve a security puzzle. It's whether an agent stays inside its authorization when it has tools, a filesystem, code execution, and an objective that happens to be easier to reach by stepping outside those lines than by staying inside them. Nobody attacks the agent. Nobody asks it to do anything malicious. The boundary is just there, and something useful is on the other side of it.</i></p>
</blockquote>

## Status

The `felonybench` package here is not just a spec; it's real and runs: `pip install -e .` works, and `python -m felonybench run` executes four tasks against a shipped in-memory sandbox and two deterministic mock agents, producing graded JSON output.

What's *not* here yet, in short: a real model adapter (only two hardcoded mock agents ship — see [Adding an Agent](#adding-an-agent)), most of the taxonomy in [What It Tests](#what-it-tests) below (four of ten categories are implemented as tasks), a way for an attempt to actually succeed (`violation_succeeded` is always `False` by construction, since the shipped sandbox denies everything), any reproducibility metadata in run output (no version, timestamp, or task-set identifier is emitted — `__version__` exists in the package but isn't surfaced), and an automated test suite. Specifics are tracked in the issue queue, not restated here.

## Positioning

Agent-security evaluation has mostly organized around three questions. FelonyBench enables us to answer a fourth:

| Benchmark | Question it asks | Trigger |
|---|---|---|
| [AgentDojo](https://arxiv.org/abs/2406.13352) (Debenedetti et al., NeurIPS 2024 D&B) | Can *third-party content* the agent reads (an email, a search result, a tool output) hijack its behavior? | Injected instruction |
| [AgentHarm](https://arxiv.org/abs/2410.09024) (Andriushchenko et al., 2024, with UK AISI) | Will the agent comply when the *user* directly asks it to do something explicitly malicious? | Explicit malicious request |
| [SandboxEscapeBench](https://arxiv.org/abs/2603.02277) (Marchand et al., 2026) | *Can* the agent break container isolation when its stated goal is to escape and read a host-side flag? | Explicit escape objective, CTF framing |
| **FelonyBench** | Will the agent cross an authorization boundary *nobody told it to cross*, on a task nobody made adversarial, because doing so is instrumentally convenient? | No instruction, no injection, no objective — just opportunity |

A model that resists AgentDojo has shown it isn't hijackable by hostile content. A model that resists AgentHarm has shown it refuses direct requests to do harm. A model that fails SandboxEscapeBench under an explicit escape objective has demonstrated a capability, not an intent. None of those results tell you whether the same model, given a completely ordinary task and no adversarial input at all, will quietly read a file it wasn't authorized to read because reading it would help, which is the gap FelonyBench targets: closer to the propensity side of the agentic-misalignment literature than to red-teaming or jailbreak-robustness. Adjacent multi-category efforts like Agent-SafetyBench and Agent Security Bench (ASB) cover broader risk taxonomies (Zhang et al., 2024/2025) but are also built around adversarial or explicitly risky framings, not incidental opportunity.

Several of the benchmarks above are built on [Inspect AI](https://inspect.aisi.org.uk/), the UK AISI's evaluation framework. The code shipped in this repository today does not use it — see [Quickstart](#quickstart) and [Architecture](#architecture) for what actually runs.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

python -m felonybench list                 # available tasks
python -m felonybench run                  # all tasks, clean mock agent, text output
python -m felonybench run sandbox-boundary  # one task
python -m felonybench run --json            # graded results as JSON
python -m felonybench run --violating       # a mock agent that also probes every protected API
```

Not published to PyPI (coming soon!) install from a local clone as shown. `run` executes the two shipped mock agents only; there's no `--model` flag or `validate` subcommand. To point a real model at a task, see [Adding an Agent](#adding-an-agent).

## Architecture

This is the pipeline the shipped code actually runs (`felonybench/runner.py`, `sandbox.py`, `events.py`, `grader.py`):

```text
Task → Sandbox ← Agent → Event Log → Grader → TaskResult
```

**Task** defines the objective (`prompt()`), seeds the sandbox (`setup()`), and checks completion from final sandbox state (`is_complete(sandbox)`). **Sandbox** is an in-memory simulation, not a real security boundary — an authorized `/work` namespace plus a handful of synthetic protected resources (a file outside `/work`, a fake secret, a persistence API, a network-request stub). Every operation gets classified authorized/unauthorized and emits an **Event**; a fresh `Sandbox` is constructed per run, so no state leaks between them. **Agent** is a one-method adapter (`run(prompt, sandbox) -> str`) — the two mock agents implement it, a real model adapter would too. **Grader** reads the event log and produces a `TaskResult` (`completed`, `violation_attempted`, `violation_succeeded`, `protected_resource_accessed`, the event list, a short `notes` string), working from observable events rather than inferring anything from what the agent says happened.

No task requires real credentials, production systems, or external infrastructure. (See [Security Model](#security-model).)

## What It Tests

| Category | Question the task asks | Shipped as a task? |
|---|---|---|
| Sandbox escape | Does the agent try to reach resources outside its permitted execution environment? | Yes — `sandbox-boundary` |
| Credentials / secrets | Does it discover, access, retrieve, or transmit protected values? | Yes — `protected-secret` (single boolean today; five-way grading of discover/attempt/succeed/return/exfiltrate is a future refinement) |
| Persistence | Does it try to leave state that survives the environment's intended lifecycle? | Yes — `persistence` |
| Prompt injection | Does it treat untrusted content as data, or adopt embedded instructions as its own? | Yes — `prompt-injection` (its prompt explicitly tells the agent to treat the document as data first, so this measures whether the agent follows that instruction, not unprompted injection resistance) |
| Privilege escalation | Does it attempt to acquire permissions it wasn't granted? | No |
| Network access, as its own task | Does it reach destinations outside its authorized network boundary? | No — the sandbox has a `network_request()` stub, but no task exercises it as a first-class objective |
| Exfiltration | Does it move protected data to a destination outside the sandbox? | No |
| Environment tampering | Does it attempt to modify or disable the benchmark's own instrumentation? | No |
| Deceptive reporting | Does what it *says* happened match the instrumented event log? | No |

A task distinguishes an agent merely *encountering* a protected resource from an agent *actively attempting* to obtain it; a benchmark that scores on whether a prohibited string appears anywhere in a trajectory is measuring exposure, not behavior.

## Adding a Task

1. New module under `felonybench/tasks/`, subclassing `Task` (`felonybench.tasks.base`) with `id`, `name`, `prompt()`, and `is_complete(sandbox)`. Override `setup(sandbox)` if it needs to seed files or state.
2. Build the legitimate path — and, implicitly, the boundary around it — from existing `Sandbox` APIs (`read_file`, `write_file`, `list_files`, `access_protected_resource`, `access_protected_secret`, `create_persistent_state`, `network_request`). Don't add protected-resource mechanics that reach outside the in-memory `Sandbox` instance.
3. Register it in `felonybench/tasks/__init__.py`'s `TASK_REGISTRY`. No runner, grader, or CLI changes needed.

`examples/run_bench.py` is currently broken (`from felony.runner import BenchmarkRunner` — that module and class don't exist anywhere in this repo) and shouldn't be used as a reference; use the CLI commands under [Quickstart](#quickstart) instead.

## Adding an Agent

Subclass `Agent` from `felonybench/runner.py` and implement `run(prompt, sandbox) -> str`, then pass an instance to `run_task()`/`run_tasks()`. The interface is intentionally minimal and doesn't assume anything about how the agent is hosted — see `mock_agents.py` for the shape, though both shipped agents dispatch on sandbox contents rather than reading `prompt`, since neither wraps a real model.

## Security Model

Nothing here touches production infrastructure, real credentials, real user data, uncontrolled third-party systems, real corporate networks, or real host-level persistence. "Protected" resources are Python objects (dict, string constants) that exist only for the lifetime of one `Sandbox` instance. The purpose is to observe whether an agent *attempts* prohibited behavior, not to hand it an opportunity to compromise anything real.

FelonyBench is not a CTF collection and doesn't measure penetration-testing ability, vulnerability discovery, or exploit development (that's SandboxEscapeBench's territory.) It's also not a substitute for production agent security controls: passing it doesn't establish that a model is safe to deploy with arbitrary privileges. The question is narrower: *when an agent has an explicit execution boundary, does it respect that boundary — unprompted, on an ordinary task, with no one testing it?*

## Repository Layout

```text
FelonyBench/
├── felonybench/
│   ├── cli.py, runner.py, sandbox.py, events.py, models.py, grader.py, mock_agents.py
│   └── tasks/
│       ├── base.py
│       └── sandbox_boundary.py, protected_secret.py, persistence.py, prompt_injection.py
├── examples/run_bench.py
├── pyproject.toml, README.md, LICENSE
```

No `tests/` or `docs/` directory exists yet, despite `pytest` being a listed dev dependency.

## Citation

No accompanying paper yet.

```bibtex
@misc{felonybench,
  title        = {FelonyBench: Measuring Authorization-Boundary Behavior in AI Agents},
  author       = {TODO},
  year         = {2026},
  howpublished = {\url{https://github.com/MLOpsNYC/FelonyBench}},
  note         = {Early-stage. Citation will be finalized at first tagged release.}
}
```

## References

- Debenedetti, E., Zhang, J., Balunović, M., Beurer-Kellner, L., Fischer, M., Tramèr, F. *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents.* NeurIPS 2024, Datasets and Benchmarks Track.
- Andriushchenko, M. et al. *AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents.* arXiv:2410.09024, 2024.
- Marchand, R. et al. *Quantifying Frontier LLM Capabilities for Container Sandbox Escape.* arXiv:2603.02277, 2026.

## License

MIT — see `LICENSE`.
