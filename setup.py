from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="mcp-chart-image-scanner",
    version="0.1.0",
    description="MCP server for extracting Docker images from Helm charts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Cagojeiger",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "mcp[server]>=1.9.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.23.2",
        "python-multipart",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-chart-image-scanner=mcp_chart_image_scanner.main:main",
        ],
    },
)
