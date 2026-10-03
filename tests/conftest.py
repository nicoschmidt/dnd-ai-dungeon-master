"""Every test runs on configuration it states, never on the developer's own.

Runs before any test module is imported, which matters: importing
`dungeon_master.api.app` builds the application from `Settings` once.
"""

import os

from dungeon_master.settings import Settings

for name in [n for n in os.environ if n.startswith("DM_")]:
    del os.environ[name]

# Never read the repository's `.env`: it may hold a real API key.
Settings.model_config["env_file"] = None
