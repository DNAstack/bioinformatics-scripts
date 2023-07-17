# Bioinformatics scripts

Miscellaneous scripts and documenation from the DNAstack bioinformatics team.


## Scripts

### [Build Docker images](scripts/build_docker_images)

Recursively build Docker images in a given directory.

Each target image is defined via the presence of a `build.env` file, which is used to specify the name and version tag for the corresponding Docker image. It must contain at minimum the following variables:

- `IMAGE_NAME`
- `IMAGE_TAG`

All variables defined in the `build.env` file will be made available as build arguments during Docker image build.

The `IMAGE_TAG` variable can be built using other variables defined in the `build.env` file, as long as those other variables are defined before the `IMAGE_TAG` definition. For example, the following `IMAGE_TAG` would be set to `0.7.8_1.15`:

```
# Tool verisons
BWA_VERSION=0.7.8
SAMTOOLS_VERSION=1.15

# Image info
IMAGE_NAME=bwa_samtools
IMAGE_TAG=${BWA_VERSION}_${SAMTOOLS_VERSION}
```

The `Dockerfile` corresponding to a `build.env` must either:
1. Be named `Dockerfile` and exist in the same directory as the `build.env` file, or
2. Be specified using the `DOCKERFILE` variable in the `build.env` file (e.g. for image builds that reuse a common Dockerfile). The path to the Dockerfile should be relative to the directory containing the `build.env` file.


#### Special variables

These variables have special meanings when the Docker image is being built. † specifies that the variable is required.

- `IMAGE_NAME`†: specifies the name of the built image
- `IMAGE_TAG`†: specifies the tag of the built image
- `NOBUILD`: When set to `true`, skip building this image
- `DOCKERFILE`: Specify an alternate path to a Dockerfile, relative to the `build.env` file. If left undefined, the Dockerfile must be named `Dockerfile` and be present at the same directory level as the corresponding `build.env` file.
- `CONDA_ENVIRONMENT_TEMPLATE`: For conda-based images, set this to the path (relative to the `build.env` file) to the conda environment template file. This file may have variables set in place of tool versions and will be populated with the variables from `build.env` at build time.


#### Usage

```bash
# build Docker images found in a directory (and its subdirectories)
./build_docker_images -d docker/some/path

# build all Docker images defined in the `docker` directory using the provided container registry
./build_docker_images -d docker -c dnastack

# build and push all Docker images defined in the `docker` directory to the provided container registry
./build_docker_images -d docker -c dnastack -p
```

## [Cromwell interaction scripts](scripts/cromwell)

### [getIDs](scripts/cromwell/getIDs)

Get the status for recently run workflows. Interacts with Cromwell running in server mode. Set and export `CROMWELL_URL` to change the location where your Cromwell is running in server mode (defaults to `localhost:8000`).

The output columns are workflow name, workflow ID, and workflow status.

#### Usage

```bash
# Use a different Cromwell URL (default: localhost:8000)
export CROMWELL_URL=localhost:9000

# Get information about the last 10 workflows to run
getIDs

# Get information about the last 30 workflows to run
getIDs 30

# Get information about the last 5 workflows that are currently running (there may not be 5 running currently)
getIDs -r 5
```


### [getMeta](scripts/cromwell/getMeta)

Get metadata for a Cromwell workflow run. Interacts with Cromwell running in server mode. Set and export `CROMWELL_URL` to change the location where your Cromwell is running in server mode (defaults to `localhost:8000`).

#### Usage

```bash
# Use a different Cromwell URL (default: localhost:8000)
export CROMWELL_URL=localhost:9000
# set this to a specific workflow ID you want info about, e.g. check the output of getIDs
workflow_id=1c0c4711-c5d6-46dc-b176-c52fb612c1c6

# Get information about a workflow
getMeta ${workflow_id}

# Save the metadata from a workflow to a file (named ${workflow_id}.meta.json)
getMeta -s ${workflow_id}

# Get raw metadata; retrieve workflow inputs using `jq`
getMeta -r ${workflow_id} | jq '.inputs'

# Get workflow status
getMeta -r ${workflow_id} | jq '.status'

# List task calls
getMeta -r ${workflow_id} | jq '.calls | keys'

# Get information about a specific call
# Note that the call key must be double quoted since it contains a `.` character
# The format of call keys is workflow_name.task_name
getMeta -r ${workflow_id} | jq '.calls."hello_world.say_hello"'

# Get the location of the stderr file for a specific call
getMeta -r ${workflow_id} | jq '.calls."hello_world.say_hello"[0].stderr'
```
