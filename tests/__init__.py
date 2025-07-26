"""
AI-Driven Stock Trade Advisor - Test Package

Organized test suite for the application.
"""

import sys
import os

# Ensure src directory is in path for all tests
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path) 