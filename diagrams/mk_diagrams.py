# %%
from diagrams import Cluster, Diagram, Edge

# %%
from diagrams.aws.compute import Compute, EC2Instance
from diagrams.aws.database import Database
from diagrams.aws.devtools import CommandLineInterface
from diagrams.aws.general import General
from diagrams.programming.language import Bash


# %%
with Diagram("imports", direction="TB", show=True):

    with Cluster("cli"):
        cli_nki = General("run_nki")
        cli_emo = General("run_emorep")

    with Cluster("workflows"):
        wf_emo = General("BuildEmoRep")
        wf_nki = General("build_nki")

    with Cluster("resources"):
        emo = General("emorep")
        bids = General("bidsify")
        proc = General("process")
        beh = General("behavior")
        unq = General("unique_cases")

    with Cluster("bin"):
        org = Bash("org_dcms")

    with Cluster("reference_files"):
        rf = General("unique_fmaps")

    cli_nki << wf_nki
    cli_emo << bids
    cli_emo << wf_emo << emo << org
    emo << bids << unq << rf
    emo << proc
    emo << beh << unq


# %%
graph_attr = {
    "layout": "dot",
    "compound": "true",
    }

with Diagram("process", graph_attr=graph_attr):
    with Cluster("cli"):
        cli_nki = CommandLineInterface("run_nki")
        cli_emo = CommandLineInterface("run_emorep")

    with Cluster("workflows"):
        wf_nki = Compute("build_nki")
        wf_emo = General("BuildEmoRep")

    with Cluster("nki_proc"):
        nk_py = Database("NKI pull")
        nk_clean = Compute("clean")

    with Cluster("BuildEmoRep"):
        conv_mri = Compute("convert_mri")
        conv_beh = Compute("convert_beh")
        conv_rate = Compute("convert_rate")
        conv_phys = Compute("convert_phys")

        with Cluster("emorep.ProcessMri"):
            make_nii = Compute("make_niftis")
            with Cluster("bidsify_niftis"):
                bids_nii = Compute("BIDS NIfTIs")
                up_func = Compute("Update func")
                up_fmap = Compute("Update fmap")
            deface_nii = Compute("deface")

    cli_nki >> wf_nki >> Edge(lhead='cluster_nki_proc') >> nk_py
    nk_py >> nk_clean
    cli_emo >> wf_emo >> Edge(lhead='cluster_BuildEmoRep') >> conv_mri
    conv_mri >> Edge(lhead='cluster_emorep.ProcessMri') >> make_nii
    make_nii >> Edge(lhead='cluster_bidsify_niftis') >> bids_nii
    bids_nii >> up_func >> up_fmap
    up_fmap >> Edge(ltail='cluster_bidsify_niftis') >> deface_nii




# %%
