version 1.0


workflow pb_bam_check {
  input {
    File bam
    Int num_reads = 10000
  }

  # call tasks
  call bam_tag_check {
    input:
      bam = bam,
      num_reads = num_reads
  }
  output {
    Array[File] json_files = bam_tag_check.json_output
  }
}


task bam_tag_check {
  meta {
    description: "Parse a BAM file and count the number of reads with kinetics and methylation tags"
  }

  input {
    File bam
    Int num_reads
  }

  # Constants
  Int cpu = 2
  Int mem_gb = 4
  Int disk_size = ceil(size(bam, "GB") * 2 + 20)

  command <<<
    set -euo pipefail

    echo "Processing BAM file: ~{bam}"

    hfs_bam_tag_check.py --bam "~{bam}" --num_reads "~{num_reads}"

    echo "Completed processing ~{num_reads} reads"
  >>>

  output {
    Array[File] json_output = glob("*.json")
  }

  runtime {
    docker: "bam_check:0.0.1"
    cpu: "~{cpu}"
    memory: "~{mem_gb} GB"
    disk: "~{disk_size} GB"
    disks: "local-disk ~{disk_size} HDD"
    preemptible: 3
  }

  parameter_meta {
    bam: {
      help: "BAM file to process"
    }
    num_reads: {
      help: "Number of reads to process in a BAM file"
    }
  }
}
