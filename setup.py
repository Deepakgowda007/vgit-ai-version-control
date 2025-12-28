from setuptools import setup

setup(
    name="vgit",
    version="0.1.0",
    py_modules=["vgit_cli", "vgit_database"],
    install_requires=[
        "sentence-transformers",
        "chromadb",
        "sqlite3; python_version < '3.12'", # sqlite3 is usually built-in
    ],
    entry_points={
        "console_scripts": [
            "vgit=vgit_cli:main",
        ],
    },
)
