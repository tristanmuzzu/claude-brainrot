# Brainrot renderer and overlay

Read docs/ARCHITECTURE.md for subsystem changes, docs/PROBES.md for relevant
measurement, docs/LANDMINES.md for symptoms, and docs/OUTSTANDING.md for the
backlog. FINDINGS.md is the defect ledger. Historical CLAUDE.md carries detailed
probe command examples; verify flags and versions before reusing them.

Claude is the default integration; optional local Codex/ChatGPT hooks are explicit
choices through --agent. Do not change the default or install an integration
merely because an agent is developing the project. Do not add always-running overlay daemons or
session hooks as incidental migration work. Use brainrot doctor for instance
identity before diagnosing flicker; competing daemons/compositors can cause it.
Changes to the GNOME extension may require a later user login to validate.

Keep seeded generation reproducible, scenes independent of windowing/hooks,
and draw() free of state advancement. Shared test windows must not be resized
or duplicated. Drawing order, alpha/depth behavior and allocator ownership matter;
software-renderer skips are not GPU validation. Use brainrot shoot and visual
inspection alongside the relevant numerical probes. After asset rebuilds, run
assets/measure.py; Blender scripts need a nonzero Python failure exit code.

Use the existing project environment and python -m pytest tests/ before committing
implementation changes. Verify platform-specific skips and changed generation
worlds. Do not replace the live renderer with software mode globally just to
make a test convenient. Preserve editable asset sources and measured evidence.
