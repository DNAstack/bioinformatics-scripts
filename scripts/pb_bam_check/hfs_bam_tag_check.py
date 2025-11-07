#!/usr/bin/env python3

import argparse as ap
import json
import logging
import pysam
import os
from collections import Counter
from os.path import basename


def init_args():
    """
    Initialize command line arguments.

    Arguments:
        None

    Returns:
        argparse object
    """
    parser = ap.ArgumentParser()
    parser.add_argument('-b', '--bam', required=True, help="BAM file")
    parser.add_argument('-n', '--num_reads', type=int, default=10000, help='number of reads to process (default: 10000)')
    return parser.parse_args()


def check_kinetics_tags(read):
    """
    Check reads for tags matching kinetics tags.

    Arguments:
        * read:    a PySAM read object

    Returns:
        Dictionary containing tag counts for kinetics

    Ref:
    https://pacbiofileformats.readthedocs.io/en/11.0/BAM.html#encoding-of-kinetics-pulse-features
    """
    # all tags associated with kinetics pulse info for base modification
    # processing
    kinetics_tags = ['fi', 'ri', 'fp', 'rp', 'fn', 'rn']

    # get all the tags in the read
    read_tags = [tag for tag, value in read.get_tags()]
    
    # compare all the tags, need to determine exactly which are required to perform
    # base modification processing
    return all(tag in set(read_tags) for tag in kinetics_tags)


def check_methylation_tags(read):
    """
    Check reads for tags matching methylation/base modification tags.

    Arguments:
        * read:    a PySAM read object

    Returns:
        Dictionary containing tag counts for methylation

    Ref:
    https://pacbiofileformats.readthedocs.io/en/11.0/BAM.html#use-of-read-tags-for-per-read-base-base-modifications
    """
    methylation_tags = ['MM', 'ML']
    read_tags = [tag for tag, value in read.get_tags()]
    return all(tag in set(read_tags) for tag in methylation_tags)
    

def main():
    """
    Main program
    """
    args = init_args()
    data = [] 
    kinetics_count = 0
    methylation_count = 0
    total_reads = 0

    bam_fh = pysam.AlignmentFile(args.bam, "rb", check_sq=False)

    for read in bam_fh:
        total_reads += 1
        if check_kinetics_tags(read=read):
            kinetics_count += 1
        if check_methylation_tags:
            methylation_count += 1
        if total_reads >= args.num_reads:
            break

    data.append({"bam": args.bam,
                 "total_reads": total_reads,
                 "kinetics_count": kinetics_count,
                 "methylation_count": methylation_count})

    fn, _ = os.path.splitext(basename(args.bam))
    outfile = fn + ".json"
    with open(outfile, 'w') as ofh:
        print(json.dump(data, ofh, indent=2))
    ofh.close()


if __name__ == '__main__':
    main()


# __END__

