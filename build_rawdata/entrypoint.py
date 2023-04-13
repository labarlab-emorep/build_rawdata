"""Print entrypoint help."""
import build_rawdata._version as ver


def main():
    print(
        f"""

    Version : {ver.__version__}

    The package build_rawdata consists of sub-packages that can be accessed
    from their respective entrypoints:

        build_emorep    : convert sourcedata to rawdata for Exp2_Compute_Emotion
        build_nki       : build rawdata from NKI Rockland Archival data
                            for Exp3_Classify_Archival

    """
    )


if __name__ == "__main__":
    main()
