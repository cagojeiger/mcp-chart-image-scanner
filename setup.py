from setuptools import setup, find_packages

setup(
    name="mcp-chart-image-scanner",
    version="0.1.0",
    description="MCP server for extracting Docker images from Helm charts",
    author="cagojeiger",
    author_email="cagojeiger89@gmail.com",
    url="https://github.com/cagojeiger/mcp-chart-image-scanner",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "mcp>=1.9.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.25.0",
            "pytest-cov>=4.1.0",
        ],
        "sse": [
            "uvicorn>=0.23.2",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
