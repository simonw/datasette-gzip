from setuptools import setup
import os

VERSION = "0.1"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-gzip",
    description="Add gzip compression to Datasette",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/datasette-gzip",
    project_urls={
        "Issues": "https://github.com/simonw/datasette-gzip/issues",
        "CI": "https://github.com/simonw/datasette-gzip/actions",
        "Changelog": "https://github.com/simonw/datasette-gzip/releases",
    },
    license="Apache License, Version 2.0",
    classifiers=[
        "Framework :: Datasette",
        "License :: OSI Approved :: Apache Software License",
    ],
    version=VERSION,
    packages=["datasette_gzip"],
    entry_points={"datasette": ["gzip = datasette_gzip"]},
    install_requires=["datasette", "starlette"],
    extras_require={"test": ["pytest", "pytest-asyncio"]},
    python_requires=">=3.7",
)
