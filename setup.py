from setuptools import setup, find_packages

setup(
    name="dcm_conversion",
    version="0.3.2",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "dcm_conversion=dcm_conversion.cli:main",
        ]
    },
    install_requires=[
        "nibabel==4.0.1",
        "numpy==1.23.1",
        "pandas==1.4.3",
        "pydeface==2.0.2",
        "pytest==7.1.2",
        "setuptools==45.2.0",
    ],
)
