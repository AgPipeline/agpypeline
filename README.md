# Transformer: agpypeline

This is an installable package derived from [base-image](https://github.com/AgPipeline/base-docker-support/tree/master/base-image) and
[base-transformer-class](https://github.com/AgPipeline/drone-pipeline-environment/tree/master/base-transformer-class)

The purpose of this package is to reduce the cost of deriving a complete transformer and allow for easier integration of additional transformer
code

## Contributing

We welcome the addition of other packages to this repo. Feel free to adjust the given files and add others to meet your needs. 

If you find that the code provided is not meeting your needs, please file a [feature request](https://github.com/AgPipeline/issues-and-projects/issues/new/choose)
so that we can try to meet your needs

Please be sure to clearly label your folders for the environment you are targeting; starting folder names with 'aws', 'clowder', or 'cyverse' for example.
If you are thinking of creating an environment specific folder, please consider putting it into its own repository first, using the just mentioned naming
convention, to keep this one as clean as possible.

Folder beginning with 'base' are reserved to those images that are not particular to any single environment.

Be sure to read the [organization documentation](https://github.com/AgPipeline/Organization-info) on how to contribute

## Documenting

Every folder added to this repo must have a README.md clearly explaining the interface for derived images, how to create a derived image, and
other information on how to use the images created. Providing a quick start guide with links to more detailed information a good approach
for some situations. The goal is to provide documentation for users of these base images that makes it easy for them to be used.

## Testing

Testing modules and README.md files can be found in their respective AgPipeline repositories.