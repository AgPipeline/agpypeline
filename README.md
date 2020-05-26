
# Docker support
This repo is used for developing base Docker images that can be used for further development of code.

We are providing these to promote the development of code/container templates to reduce the cost of adding functionality to the processing pipeline.

It is expected that all derived docker images will have their own repositories instead of residing here.
See [Contributing](#contributing) below for more information on how to name your derived repos.

## Contributing <a name="contributing" />
We welcome the addition of other base docker images to this repo.

**But first**, if you are finding that the code provided in the `base-image` folder is not meeting your needs, please file an [feature request](https://github.com/AgPipeline/computing-pipeline/issues/new/choose) first so that we can try and address your needs.

Please be sure to clearly label your folders for the environment you are targeting; starting folder names with 'aws', 'clowder', or 'cyverse' for example.
If you are thinking of creating an environment specific folder, please consider putting it into its own repository first, using the just mentioned naming convention, to keep this one as clean as possible.

Folder beginning with 'base' are reserved to those images that are not particular to any single environment.

Be sure to read the [organization documentation](https://github.com/AgPipeline/Organization-info) on how to contribute.

## Documenting
Every folder in this repo must have a README.md clearly explaining the interface for derived images, how to create a derived image, and other information on how to use the images created.
Providing a quick start guide with links to more detailed information a good approach for some situations.
The goal is to provide documentation for users of these base images that makes it easy for them to be used.

## Testing
The testing modules and readme may be found in the [testing folder](https://github.com/AgPipeline/base-docker-support/tree/test-development/base-image/test-files).