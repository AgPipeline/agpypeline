
# agpypeline
This repo is used as an installable package for the entrypoint and environment transformers. It is a template to which other files can be added

We are providing these to promote the development of code/container templates to reduce the cost of adding functionality to the processing pipeline.

It is expected that all derived docker images will have their own repositories instead of residing here.
See [Contributing](#contributing) below for more information on how to name your derived repos.

## Contributing <a name="contributing" />
Please be sure to clearly label your folders for the environment you are targeting; starting folder names with 'aws', 'clowder', or 'cyverse' for example.
If you are thinking of creating an environment specific folder, please consider putting it into its own repository first, using the just mentioned naming convention, to keep this one as clean as possible.

Be sure to read the [organization documentation](https://github.com/AgPipeline/Organization-info) on how to contribute.

## Documenting
After you have added your files, remember that every folder in this repo must have a README.md clearly explaining 
the interface for derived images, how to create a derived image, and other information on how to use the images created.
Providing a quick start guide with links to more detailed information a good approach for some situations.
The goal is to provide documentation for users that makes it easy for them to be used.

## Testing
This package may be found in the [following repo](https://github.com/AgPipeline/agpypeline).