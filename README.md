# AgPypeline
Python library of common classes and functions

This is an installable package derived from the [base-image](https://github.com/AgPipeline/base-docker-support/tree/master/base-image) and the
[base-transformer-class](https://github.com/AgPipeline/drone-pipeline-environment/tree/master/base-transformer-class)

## Expected metadata
There are several metadata key/value pairs that a user of entrypoint and transformer_class modules expects to receive.
The metadata keys listed below are all defined in the [BRAPI V1.3](https://brapi.docs.apiary.io/#) standard.

*  studyName - the name of the study the data belongs to
*  season - the season associated with the data
*  observationTimeStamp - a timestamp override in ISO 8610 long format
*  germplasmName - the name of the crop being tested in the plot
*  collectingSite - site identification

If the observationTimeStamp metadata key is not specified, the EXIF information in source image files are checked and the earliest found timestamp will be used. 

If the other metadata keys listed above are not specified, default and/or empty values will be used which may introduce errors if not checked for.

Individual users of this library may also have additional metadata needs.

## Metadata provided
The derived transformers using this library as their base, can expect to receive the following defined keys with values in their `check_md` parameter:

* timestamp - the ISO 8610 timestamp relevant to the current dataset
* season - the name of the season
* experiment - the experiment name
* context_md - metadata relevant to the current processing
* working_folder - the workspace for the derived transformer
* list_files - a function that returns a list containing the paths of the available files
