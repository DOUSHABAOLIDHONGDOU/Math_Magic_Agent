"""Math Magic workflow agent — modular implementation.

This package was extracted from the previously monolithic ``agentctl.py``.
``agentctl.py`` now serves as the CLI entry point and delegates to the
modules in this package.

Module layout
-------------

- ``_paths``: project path constants and dispatch directory helpers.
- ``_util``: I/O primitives, formatting, console helpers, CLI argument helpers.
- ``_state``: workflow state default/load/save/migrate plus the file lock.
- ``_topic``: stale-topic detection helpers used by archive.
- ``_archive``: stale-artifact archival logic.
- ``_data``: data scanning into data_dictionary.md.
- ``_briefs``: scheme/approval/model-confirmation brief renderers.
- ``_workorder``: Claude workorder + Claude prompt builders.
- ``_dispatch``: dispatch-claude / watch-claude / monitor scripts.
- ``_paper``: LaTeX compile, layout check, question-section writers.
- ``_review``: Codex review templates, mark-reviewed, scheme comparison.
- ``_env``: env-check / doctor / VS Code task installer.
- ``_commands``: thin wrappers (``command_*``) for the CLI.
"""

from . import _paths  # noqa: F401
from . import _util  # noqa: F401
from . import _state  # noqa: F401
