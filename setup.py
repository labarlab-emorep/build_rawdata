# develop: python setup.py develop
# install: python setup.py install
from setuptools import setup, find_packages

setup(
    name="dcm_conversion",
    version="0.2",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "dcm_conversion=dcm_conversion.cli:main",
        ]
    },
)
