#!/usr/bin/env python
# AUTHOR: Ryan Y
# EMAIL:  ryoung-at-brandeis-edu
# Purpose: Converts phy clusters back to the mountainsort medium

import os

def firings_mda(spike_clusters:str):
    pass

def metrics_json(cluster_groups:str):
    pass

def phy_to_mountainsort(folder:str):
    pass


if __name__ == "__main__":

    import argparse
    parse = argparse.ArgumentParser(prog="phy to mountainsort",
                                    desc='converts phy clustered data back to'
                                         'types expected by mountainsort',
                                    usage="phy_to_mountainsort {folder}")
    parse.add_argument("folder", default="", type=str,
                       help="the phy folder path -- assumes mountainsort "
                            "files live a folder above")
    Opt = parse.parse_args()

    if Opt.folder == "" or Opt.folder == "pwd":
        Opt.folder = os.getcwd()
