from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="codeagents",
    version="0.1.0",
    author="CodeAgents Team",
    description="A lightweight multi-agent framework for code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/luckysun001/codeagents",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=[
        "openai>=1.0.0",
    ],
    extras_require={
        "all": [
            "openai>=1.0.0",
            "anthropic>=0.18.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pytest>=7.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "black>=23.0.0",
        ],
        "anthropic": ["anthropic>=0.18.0"],
    },
    entry_points={
        "console_scripts": [
            "codeagents=codeagents.cli:main",
        ],
    },
)
