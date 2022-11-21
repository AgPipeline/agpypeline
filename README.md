[![license](https://img.shields.io/badge/license-BSD%203-green?logo=Open-Source-Initiative)](https://github.com/AgPipeline/agpypeline/blob/add_badges/LICENSE)

[![PyPI - version](https://img.shields.io/pypi/v/agpypeline?label=current&color=green)](https://pypi.org/project/agpypeline/)
[![PyPI - downloads](https://img.shields.io/pypi/dm/agpypeline)](https://pypi.org/project/agpypeline/)

[![Enforcing pylint checks](https://github.com/AgPipeline/agpypeline/actions/workflows/testing_checks.yaml/badge.svg)](https://github.com/AgPipeline/agpypeline/actions/workflows/testing_checks.yaml)

# AgPypeline
Python library of common classes and functions

This is an installable package derived from the [base-image](https://github.com/AgPipeline/base-docker-support/tree/main/base-image) and the
[base-transformer-class](https://github.com/AgPipeline/drone-pipeline-environment/tree/main/base-transformer-class)

It's recommended reading the information on [Transformer architecture](https://agpipeline.github.io/transformers/transformers) first to gain a better understanding how the library is structured.

The last version supporting Ubuntu 20.04 is [0.0.50](https://pypi.org/project/agpypeline/0.0.50/)

## Expected metadata
There are several metadata key/value pairs that a user of entrypoint and environment modules expects to receive.
The metadata keys listed below are all defined in the [BRAPI V1.3](https://brapi.docs.apiary.io/#) standard.

*  studyName - the name of the study the data belongs to
*  season - the season associated with the data
*  observationTimeStamp - a timestamp override in ISO 8610 long format
*  species - the name of the crop being tested in the plot
*  collectingSite - site identification

If the observationTimeStamp metadata key is not specified, the EXIF information in source image files are checked and the earliest found timestamp will be used. 

If the other metadata keys listed above are not specified, default and/or empty values will be used which may introduce errors if not checked for.

Individual users of this library may also have additional metadata needs.

## Metadata provided
The derived transformers using this library as their base, can expect to receive the following defined keys with values in their `check_md` parameter.

* timestamp - the ISO 8610 timestamp relevant to the current dataset
* season - the name of the season
* experiment - the experiment name
* context_md - metadata relevant to the current processing
* working_folder - the workspace for the derived transformer
* list_files - a function that returns a list containing the paths of the available files

## Classes
This library provides classes to enable easier Transformer development.
In this section, an overview of the classes is provided as well as some technical information.

### Algorithm class
The [Algorithm concept](https://agpipeline.github.io/transformers/transformers#algorithm-) provides a standard information for implementing processing algorithms.
The Algorithm class provides a template that can be used for developing Transformers.

There are standardized function definitions that can be used when developing a Transformer.

#### Function add_parameters
The implementation of this function is optional.
Implementing this function allows Transformer developers to specify additional command line parameter requirements, or to alter existing ones.

The signature of this function is as follows:
```python
# import argparse
def add_parameters(self, parser: argparse.ArgumentParser) -> None:
```

#### Function check_continue
This optional function allows a Transformer to perform any checks and preprocessing needed before the `perform_process` function is called.
The return value from the function is evaluated for continuing or not.

The signature of this function is as follows:
```python
# from agpypeline.environment import Environment
def check_continue(self, environment: Environment, check_md: dict, transformer_md: list, full_md: list) -> tuple:
```

A tuple consisting of either an integer value, or an integer value and message string are acceptable return values.

The returned integer values are evaluated as follows:
* 0 (zero) - this value indicates that everything is in place and processing should continue; additional actions may be taken by the Environment such as downloading files, or other work
* \>0 (a value greater than zero) - this indicates that the Environment should not perform additional actions because everything needed by the transformer is available
* \<0 (a value less than zero) - this indicates that an error occurred and that processing should stop

If a message string is returned, and the returned integer value indicates an error, the message is logged as an error.

#### Function perform_process
This is the entry point for processing data.

The signature of this function is as follows:
```python
# from agpypeline.environment import Environment
def perform_process(self, environment: Environment, check_md: dict, transformer_md: dict, full_md: list) -> dict:
```

This function must be defined in the classes derived from this library's `Algorithm` class.

### Configuration class
This class is used to provide information on the Transformers.
The intent behind this class it to make it easier to provide all the relevant information for running the code in different situations.

Transformer developers will need to have a derived instance of this class that fills in the fields.

### Environment class
The [Environmental concept](https://agpipeline.github.io/transformers/transformers#environmental-) is used to provide the run-time support for Transformers.
The Environment class is the Drone Processing Pipeline's implementation of this concept.

Transformer developers will receive an instance of this class at runtime in their implemented Algorithms.
 