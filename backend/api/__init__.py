'''
backend/api/__init__.py

Marks the backend/api/ directory as a Python package, which is what makes the 
relative import from . import elo_service in main.py work. Without it, Python 
wouldn't treat api/ as a package and the import would fail.
'''