"""
Tests initialization module.
"""

import os

# Create __init__.py files for test packages
test_dir = os.path.dirname(__file__)
open(os.path.join(test_dir, '__init__.py'), 'w').close()
open(os.path.join(test_dir, 'unit', '__init__.py'), 'w').close()
open(os.path.join(test_dir, 'integration', '__init__.py'), 'w').close()
