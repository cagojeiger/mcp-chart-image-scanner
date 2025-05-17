from setuptools import setup, find_packages

setup(
    name="mcp-chart-image-scanner",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "mcp[cli]>=1.9.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.23.2",
        "python-multipart",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-chart-image-scanner=main:main",
        ],
    },
)
