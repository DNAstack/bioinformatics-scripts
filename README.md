# Bioinformatics scripts

Miscellaneous scripts and documenation from the DNAstack bioinformatics team.


## Scripts

### [Build docker images](scripts/build_docker_images)

Recursively build docker images in a given directory.

Each target image should have at minimum two files at the same directory level: a `Dockerfile`, and a `build.env` file.

The `build.env` file is used to specify the name and version tag for the docker image defined by the corresponding `Dockerfile`. It must contain at minimum the following variable:

- `IMAGE_NAME`
- `IMAGE_TAG`

Additional variables can be added to the `build.env` file; all variables defined here will be made available as build arguments when the docker image is being built.

The `IMAGE_TAG` variable can be built using other variables defined in the `build.env` file, as long as those other variables are defined before the `IMAGE_TAG` definition. For example, the following `IMAGE_TAG` would be set to 0.7.8_1.15:

```
IMAGE_NAME=bwa_samtools
BWA_VERSION=0.7.8
SAMTOOLS_VERSION=1.15
IMAGE_TAG=${BWA_VERSION}_${SAMTOOLS_VERSION}
```

The variable `NOBUILD` can be set to `true` to enable skipping the associated Docker image build when running the `build_docker_images` script.


### Usage

```bash
# build docker images found in a directory (and its subdirectories)
./build_docker_images -d some/path

# tag images using the provided container registry
./build_docker_images -c dnastack

# build and push docker images to the provided container registry
./build_docker_images -c dnastack -p
```
