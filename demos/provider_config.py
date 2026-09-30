"""Compatibility import for shared provider configuration."""

import sys
from gentis_ai import providers

sys.modules[__name__] = providers
