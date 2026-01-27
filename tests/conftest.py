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

# Also mock other potential dependencies
sys.modules['netCDF4'] = MagicMock()
sys.modules['cartopy'] = MagicMock()
sys.modules['sklearn'] = MagicMock()
sys.modules['sklearn.ensemble'] = MagicMock()
