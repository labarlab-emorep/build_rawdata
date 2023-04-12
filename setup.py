from setuptools import setup, find_packages

exec(open("build_rawdata/_version.py").read())

setup(
    name="build_rawdata",
    version=__version__,  # noqa: F821
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "build_rawdata=build_rawdata.entrypoint:main",
            "build_emorep=build_rawdata.cli.run_emorep:main",
            "build_nki=build_rawdata.cli.run_nki:main",
        ]
    },
    scripts=["build_rawdata/bin/org_dcms.sh"],
    include_package_data=True,
    package_data={"": ["reference_files/*.json"]},
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
