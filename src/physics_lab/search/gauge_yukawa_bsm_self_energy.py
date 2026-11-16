"""Public W18 entry point for the BSM self-energy backend.

The implementation lives in :mod:`gauge_yukawa_bsm_self_energy_backend` so
that the backend name remains explicit in the source tree.  This module is the
stable public import used by tests, tools and the package registry.
"""

from physics_lab.search.gauge_yukawa_bsm_self_energy_backend import *
from physics_lab.search.gauge_yukawa_bsm_self_energy_backend import __all__
