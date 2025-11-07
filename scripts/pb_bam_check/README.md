# `pb_check_bam` -- README

PacBio BAM files have a large footprint and are costly.  To reduce
this, PB BAM files are being marked for deletion.  One of the factors
associated with retaining BAMs is the availability of methylation 
and kinetic information per read.  This can be done by observing
specific tags within reads as per the following:

https://pacbiofileformats.readthedocs.io/en/11.0/BAM.html#use-of-read-tags-for-per-read-base-base-modifications

https://pacbiofileformats.readthedocs.io/en/11.0/BAM.html#use-of-read-tags-for-hifi-per-read-base-kinetic-information

The Python script searches reads in a BAM file for the following tags:

* base modification: MM, ML

* kinetics: fi, fp, ri, rp, rn, fn

Base modification reads and kinetics reads are counts separated.  To
be counted, a read must have all base modification TAGs and
subsequently all kinetics TAGs.

The output will is a JSON file as follows:

```
[
  {
    "bam": "/cromwell-executions/bam_check/f1bf28e3-c8e4-4951-9457-c13d715df59e/call-bam_tag_check/inputs/1921261145/all.u.fixed.bam",
    "total_reads": 166746,
    "kinetics_count": 0,
    "methylation_count": 166746
  }
]
```

By default, the first 10000 will be processed but can be modified as an input
to the workflow.
