"""
Pytest configuration for CESARops tests.

Handles optional dependencies and mocking for test isolation.
"""

import sys
from unittest.mock import MagicMock

# Mock optional dependencies that may not be installed
# Must be done before importing cesarops
opendrift_mock = MagicMock()
opendrift_models = MagicMock()
oceanDrift_mock = MagicMock()
OceanDrift_mock = MagicMock()

sys.modules['opendrift'] = opendrift_mock
sys.modules['opendrift.models'] = opendrift_models
sys.modules['opendrift.models.oceanDrift'] = oceanDrift_mock
sys.modules['opendrift.models.oceanDrift'].OceanDrift = OceanDrift_mock

# Also mock other potential dependencies only if they're not installed
def _maybe_mock(module_name, submodules=None):
	try:
		__import__(module_name)
		return
	except Exception:
		sys.modules[module_name] = MagicMock()
		if submodules:
			for s in submodules:
				sys.modules[f"{module_name}.{s}"] = MagicMock()

_maybe_mock('netCDF4')
_maybe_mock('cartopy')
_maybe_mock('sklearn', submodules=['ensemble', 'preprocessing'])
