# %%
from diagrams import Cluster, Diagram, Edge

# %%
from diagrams.aws.analytics import DataPipeline
from diagrams.aws.compute import Compute
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

with Diagram("process", graph_attr=graph_attr, show=False):
    with Cluster("cli"):
        cli_nki = CommandLineInterface("run_nki")
        cli_emo = CommandLineInterface("run_emorep")

    with Cluster("workflows"):
        wf_nki = Compute("build_nki")
        with Cluster("BuildEmoRep"):
            conv_mri = DataPipeline("convert_mri")
            conv_beh = DataPipeline("convert_beh")
            conv_rate = DataPipeline("convert_rate")
            conv_phys = DataPipeline("convert_phys")

    with Cluster("nki_proc"):
        nk_py = Database("NKI pull")
        nk_clean = Compute("clean")

    with Cluster("emorep.ProcessMri"):
        with Cluster("make_niftis"):
            with Cluster("process"):
                make_nii = Compute("dcm2niix")
        with Cluster("bidsify_niftis"):
            with Cluster("bidsify.BidsifyNii"):
                bids_nii = Compute("bids_nii")
                up_func = Compute("update_func")
                up_fmap = Compute("update_fmap")
        with Cluster("deface_anat"):
            with Cluster("process"):
                deface_nii = Compute("deface")

    with Cluster("emorep.ProcessBeh"):
        with Cluster("make_events"):
            with Cluster("behavior"):
                ev_tsv = Compute("events_tsv")
                ev_json = Compute("events_json")

    with Cluster("emorep.ProcessRate"):
        with Cluster("make_rate"):
            with Cluster("behavior"):
                rest_tsv = Compute("rest_ratings")

    with Cluster("emorep.ProcessPhys"):
        with Cluster("make_physio"):
            phys_txt = Compute("neurokit2")

    with Cluster("unique_cases"):
        fix_wash = Compute("wash_issue")
        fix_fmap = Compute("fmap_issue")


    # NKI workflow
    cli_nki >> wf_nki >> Edge(lhead='cluster_nki_proc') >> nk_py
    nk_py >> nk_clean

    # Start EmoRep
    cli_emo >> Edge(lhead='cluster_BuildEmoRep') >> conv_mri

    # MRI workflow
    conv_mri >> Edge(lhead='cluster_emorep.ProcessMri') >> make_nii
    make_nii >> Edge(
        lhead='cluster_bidsify_niftis', ltail='cluster_make_niftis'
        ) >> bids_nii
    bids_nii >> up_func >> up_fmap
    up_fmap >> Edge(ltail='cluster_bidsify_niftis', lhead='cluster_deface_anat') >> deface_nii
    up_fmap << fix_fmap

    # Behavior, rest ratings, and physio
    conv_beh >> Edge(lhead='cluster_emorep.ProcessBeh') >> ev_tsv
    ev_tsv >> ev_json
    ev_tsv << fix_wash
    conv_rate >> Edge(lhead='cluster_emorep.ProcessRate') >> rest_tsv
    conv_phys >> Edge(lhead='cluster_emorep.ProcessPhys') >> phys_txt



# %%
