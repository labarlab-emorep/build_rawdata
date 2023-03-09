from setuptools import setup, find_packages

exec(open("dcm_conversion/_version.py").read())

setup(
    name="dcm_conversion",
    version=__version__,  # noqa: F821
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "dcm_conversion=dcm_conversion.cli:main",
        ]
    },
    scripts=["dcm_conversion/bin/org_dcms.sh"],
    install_requires=[
        "bioread>=3.0.0",
        "neurokit2>=0.2.1",
        "nibabel>=4.0.1",
        "numpy>=1.23.1",
        "pandas>=1.4.3",
        "pydeface>=2.0.2",
        "pytest>=7.1.2",
        "setuptools>=65.5.1",
    ],
)
