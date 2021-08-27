#!/usr/bin/env python3
"""Base entry point for Agriculture Pipeline transformer
"""

import argparse
import json
import logging
import os
from typing import Optional
import yaml

from agpypeline.algorithm import Algorithm
from agpypeline.environment import Environment
from agpypeline.configuration import Configuration


class __internal__:
    """Class for functions intended for internal use only for this file
    """

    def __init__(self):
        """Performs initialization of class instance
        """

    @staticmethod
    def handle_error(code: int, message: str) -> dict:
        """Handles logging and return values when an error occurs. Implies processing
           will stop.
        Arguments:
            code: return code related to the error
            message: the message string of the error
        Return:
            Returns a dict with the code and message
        """
        if code is None:
            logging.warning("An error has occurred without a return code specified, setting default return code")
            code = -1
        if not message:
            logging.warning("An error has occurred without a message, setting default message")
            message = "An error has occurred with error code (%s)" % str(code)

        logging.error(message)
        logging.error("Stopping processing")

        result = {'error': message, 'code': code}

        return result

    @staticmethod
    def load_metadata(metadata_path: str) -> dict:
        """Loads the metadata from the specified path
        Arguments:
            metadata_path: path to the metadata file
        Return:
            Returns a dict containing the loaded metadata. If an error occurs, the dict
            won't contain metadata but will contain an error message under an 'error' key.
        """
        try:
            if os.path.splitext(metadata_path)[1] in ('.yml', '.yaml'):
                load_func = yaml.safe_load
            else:
                load_func = json.load
            with open(metadata_path, 'r', encoding='utf-8') as in_file:
                md_load = load_func(in_file)
                if md_load is not None:
                    md_return = {'metadata': md_load}
                else:
                    msg = 'Invalid JSON/YAML specified in metadata file "%s"' % metadata_path
                    logging.error(msg)
                    md_return = {'error': msg}
        except Exception as ex:
            msg = "Unable to load metadata file '%s'" % metadata_path
            logging.error(msg)
            logging.error('Exception caught: %s', str(ex))
            if logging.getLogger().level == logging.DEBUG:
                logging.exception(msg)
            md_return = {'error': msg}

        return md_return

    @staticmethod
    def check_params_result_error(transformer_params: dict) -> Optional[dict]:
        """Checks the transformer parameter results for an error
        Arguments:
            transformer_params: the dictionary to check for errors
        Return:
            An error dict if errors were found and None if not
        Notes:
            See handle_error() function
        """
        if 'code' in transformer_params:
            if 'error' in transformer_params:
                error = transformer_params['error']
            else:
                error = "Error returned from get_transformer_params with code: %s" % transformer_params['code']
            return __internal__.handle_error(-104, error)

        return None

    @staticmethod
    def check_retrieve_results_error(transformer_retrieve: tuple) -> Optional[dict]:
        """Checks the results of the transformer_class retrieving files
        Arguments:
            transformer_retrieve: the results of the retrieve
        Return:
            An error dict if errors were found and None if not
        Notes:
            See handle_error() function
        """
        if not transformer_retrieve:
            return None

        code = 0
        message = None
        retrieve_len = len(transformer_retrieve)
        if retrieve_len > 0:
            code = transformer_retrieve[0]
        if retrieve_len > 1:
            message = transformer_retrieve[1]
        else:
            message = "Retrieving files returned a code of %s" % str(code)

        # Check for an error code
        if code < 0:
            return __internal__.handle_error(code, message)

        # Log the message if we get one returned to us
        if retrieve_len > 1:
            logging.info(transformer_retrieve[1])

        return None

    @staticmethod
    def check_metadata_needed(configuration_info: Configuration) -> bool:
        """Checks if metadata is required
        Arguments:
            configuration_info: the configuration information of transformer
        Return:
            Returns True if metadata is required (the default is that it's not required), or False if not
        """
        # Disable the following check since it's not a valid test here
        # (metadata_needed is an optional variable)
        # pylint: disable=no-member

        # If we have a variable defined, check the many ways of determining False
        if hasattr(configuration_info, 'metadata_needed'):
            if configuration_info.metadata_needed:
                return True
            if isinstance(configuration_info.metadata_needed, str):
                if configuration_info.metadata_needed.lower().strip() == 'true':
                    return True
        return False

    @staticmethod
    def load_metadata_files(metadata_files: list) -> dict:
        """Loads the specified metadata files
        Arguments:
            metadata_files: list of metadata files to load
        Returns:
            Returns a dict containing the loaded metadata as an array. If an error occurs, the dict
            won't contain metadata but will contain an error message under an 'error' key.
        """
        metadata = []
        result = {'metadata': metadata}
        for metadata_file in metadata_files:
            if hasattr(metadata_file, 'name'):
                if not metadata_file.closed:
                    metadata_file.close()
                metadata_file = metadata_file.name
            if not os.path.exists(str(metadata_file)):
                result = __internal__.handle_error(-2, "Unable to access metadata file '%s'" % metadata_file.name)
                break
            logging.info("Loading metadata from file: '%s'", metadata_file)
            md_loaded = __internal__.load_metadata(metadata_file)
            if 'metadata' in md_loaded:
                metadata.append(md_loaded['metadata'])
            else:
                result = __internal__.handle_error(-3, md_loaded['error'])
                break

        return result

    @staticmethod
    def parse_continue_result(result) -> tuple:
        """Parses the result of calling transformer.check_continue and returns
           the code and/or message
        Arguments:
            result: the result from calling transformer.check_continue
        Return:
            A tuple containing the result code and result message. One or both of these
            values in the tuple may be None
        Notes:
            A string parameter will always return a result code of None and message of None indicating
            the caller needs to decide what to do.
            An integer parameter will cause the result message value of None, the caller needs to decide
            what an appropriate message is.
            A parameter that's iterable with a length > 0 will have the first value as the result code and the
            second value as the result message. No checks are made for type conformity.
            If the parameter is something other than the above, an exception will most likely be thrown.
        """
        result_code = None
        result_message = None

        if isinstance(result, int):
            result_code = result
        elif not isinstance(result, str):
            result_len = len(result)
            if result_len > 0:
                result_code = result[0]
            if result_len > 1:
                result_message = result[1]

        return result_code, result_message

    @staticmethod
    def handle_check_continue(algorithm_instance: Algorithm, environment_instance: Environment, transformer_params: dict) -> dict:
        """Handles calling the transformer.check_continue function
        Arguments:
            algorithm_instance: the working transformer instance
            environment_instance: instance of Environment class
            transformer_params: dictionary of parameters to pass to transform module functions
        Return:
            Returns the result of checking to continue operation
        """
        result = {}

        if hasattr(algorithm_instance, 'check_continue'):
            check_result = algorithm_instance.check_continue(environment=environment_instance, **transformer_params)
            result_code, result_message = __internal__.parse_continue_result(check_result)

            if result_code:
                result['code'] = result_code
            if result_message:
                result['message'] = result_message
        else:
            logging.debug("transformer module doesn't have a function named 'check_continue'")

        return result

    @staticmethod
    def handle_retrieve_files(environment_instance: Environment, args: argparse.Namespace, metadata: list) -> Optional[dict]:
        """Handles calling the transformer class to retrieve files
        Arguments:
            environment_instance: the current Environment
            args: the command line arguments
            metadata: the loaded metadata
        Return:
            A dict containing error information if a problem occurs, or None if no problems are found.
        Note:
            A side effect of this function is a information message logged if the transformer class instance does not
            have a 'retrieve_files' function declared.
        """
        if hasattr(environment_instance, 'retrieve_files'):
            transformer_retrieve = environment_instance.retrieve_files(args, metadata)
            retrieve_results = __internal__.check_retrieve_results_error(transformer_retrieve)
            if retrieve_results:
                return retrieve_results
        else:
            logging.info("Transformer class doesn't have function named 'retrieve_files'")

        return None

    @staticmethod
    def perform_processing(environment_instance: Environment, algorithm_instance: Algorithm, args: argparse.Namespace,
                           metadata: list) -> dict:
        """Makes the calls to perform the processing
        Arguments:
            environment_instance: the current Environment
            algorithm_instance: working Transformer instance
            args: the command line arguments
            metadata: the loaded metadata
        Return:
            Returns a dict containing the result of processing
        """
        result = {}

        # Get the various types of parameters from the transformer instance
        if hasattr(environment_instance, 'get_transformer_params'):
            transformer_params = environment_instance.get_transformer_params(args, metadata)
            if not isinstance(transformer_params, dict):
                return __internal__.handle_error(-101,
                                                 "Invalid return from getting transformer parameters from transformer class instance")

            params_result = __internal__.check_params_result_error(transformer_params)
            if params_result:
                return params_result
        else:
            logging.info("Transformer class instance does not have get_transformer_params method")
            transformer_params = {}

        # First check if the transformer thinks everything is in place
        if hasattr(algorithm_instance, 'check_continue'):
            result = __internal__.handle_check_continue(algorithm_instance, environment_instance, transformer_params)
            if 'code' in result and result['code'] < 0 and 'error' not in result:
                result['error'] = "Unknown error returned from check_continue call"
        else:
            logging.info("Transformer module doesn't have a function named 'check_continue'")

        # Retrieve additional files if indicated by return code from the check
        if 'error' not in result and 'code' in result and result['code'] == 0:
            result = __internal__.handle_retrieve_files(environment_instance, args, metadata)

        # Next make the call to perform the processing
        if 'error' not in result:
            if hasattr(algorithm_instance, 'perform_process'):
                result = algorithm_instance.perform_process(environment=environment_instance, **transformer_params)
            else:
                logging.debug("Transformer module is missing function named 'perform_process'")
                return __internal__.handle_error(-102, "Transformer perform_process interface " +
                                                 "is not available for processing data")

        return result

    @staticmethod
    def handle_result(result: dict, result_types: str = None, result_file_path: str = None) -> dict:
        """Handles the results of processing as dictated by the arguments passed in.
        Arguments:
            result: the dictionary of result information
            result_types: optional, comma separated string containing one or more of: all, file, print
            result_file_path: optional, location to place result file
        Return:
            Returns the result parameter
        Notes:
            If result_types is None then no actions are taken. If 'file' or 'all' is specified
            in result_types and result_file_path is None or empty, writing to a file is skipped
        """
        if result_types is not None:
            type_parts = [one_type.strip() for one_type in result_types.split(',')]
            if 'print' in type_parts or 'all' in type_parts:
                print(json.dumps(result, indent=2))
            if 'file' in type_parts or 'all' in type_parts:
                if result_file_path:
                    try:
                        os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
                    except OSError:
                        msg = 'Error while creating result path "%s"' % str(os.path.dirname(result_file_path))
                        logging.error(msg)
                        if logging.getLogger().level == logging.DEBUG:
                            logging.debug('Error creating folder for result file')
                        logging.warning('Unable to create folders, skipping writing to result file')
                    with open(result_file_path, 'w', encoding='utf-8') as out_file:
                        json.dump(result, out_file, indent=2)
                else:
                    logging.warning("Writing result to a file was requested but a file path wasn't provided.")
                    logging.warning("    Skipping writing to result file.")

        return result


def add_parameters(parser: argparse.ArgumentParser, algorithm_instance: Algorithm, environment_instance: Environment) -> None:
    """Function to prepare and execute work unit
    Arguments:
        parser: an instance of argparse.ArgumentParser
        algorithm_instance: working Transformer instance
        environment_instance: the current Environment
    """
    parser.add_argument('-d', '--debug', action='store_const',
                        default=logging.WARN, const=logging.DEBUG,
                        help='enable debug logging (default=WARN)')

    parser.add_argument('-i', '--info', action='store_const',
                        default=logging.WARN, const=logging.INFO,
                        help='enable info logging (default=WARN)')

    parser.add_argument('--result', nargs='?', default='all',
                        help='Direct the result of a run to one or more of (all is default): "all,file,print"')

    parser.add_argument('-m', '--metadata', type=argparse.FileType('rt'), action='append',
                        help='The path to the source metadata')

    parser.add_argument('-w', '--working_space', type=str, default='output',
                        help='the folder to use use as a workspace and for storing results')

    # Let the transformer class add parameters
    if hasattr(environment_instance, 'add_parameters'):
        environment_instance.add_parameters(parser)

    # Check if the transformer has a function defined to extend command line arguments
    if hasattr(algorithm_instance, 'add_parameters'):
        algorithm_instance.add_parameters(parser)

    # Assume the rest of the arguments are the files
    parser.add_argument('file_list', nargs='*', type=argparse.FileType('r'),
                        help='additional files, folders, and other information'
                             ' for the transformer')


def do_work(parser: argparse.ArgumentParser, configuration_info: Configuration,
            algorithm_instance: Algorithm, **kwargs) -> dict:
    """Function to prepare and execute work unit
    Arguments:
        parser: an instance of argparse.ArgumentParser
        configuration_info: instance of Configuration class
        algorithm_instance: instance of Transformer class
        kwargs: keyword args
    """
    result = {}

    # Create an instance of the Transformer class
    transformer_instance = Environment(configuration_info, **kwargs)
    if not transformer_instance:
        result = __internal__.handle_error(-100, "Unable to create transformer class instance for processing")
        return __internal__.handle_result(result, None, None)
    add_parameters(parser, algorithm_instance, transformer_instance)
    args = parser.parse_args()

    # start logging system
    logging.getLogger().setLevel(args.debug if args.debug == logging.DEBUG else args.info)

    if args.working_space and not os.path.isdir(args.working_space):
        try:
            os.makedirs(args.working_space)
        except OSError:
            msg = 'Error while creating working space path "%s"' % str(args.working_space)
            logging.warning(msg)
            if logging.getLogger().level == logging.DEBUG:
                logging.debug('Error creating working space path')
            result = __internal__.handle_error(-10, msg)
            return __internal__.handle_result(result, None, None)

    # Check that we have metadata
    if not args.metadata and __internal__.check_metadata_needed(configuration_info):
        result = __internal__.handle_error(-1, "No metadata paths were specified.")
    elif args.metadata:
        md_results = __internal__.load_metadata_files(args.metadata)
        if 'metadata' not in md_results:
            result = __internal__.handle_error(-3, md_results['error'])
    else:
        md_results = {'metadata': []}

    if not result:
        result = __internal__.perform_processing(transformer_instance, algorithm_instance, args, md_results['metadata'])

    if args.working_space:
        result_path = os.path.join(args.working_space, 'result.json')
    else:
        result_path = None

    __internal__.handle_result(result, args.result, result_path)
    return result


def entrypoint(configuration_info: Configuration, algorithm_instance: Algorithm):
    """Entry point for processing
    Arguments:
        configuration_info: an instance of Configuration class
        algorithm_instance: an instance of class for preparing work
    """
    begin_process(configuration_info, algorithm_instance)


def begin_process(configuration_info: Configuration, algorithm_instance: Algorithm):
    """entrypoint() functionality moved here to allow users to transition over time
    Arguments:
        configuration_info: an instance of the Configuration class
        algorithm_instance: an instance of class for preparing work
    """
    parser = argparse.ArgumentParser(description=configuration_info.transformer_description)
    do_work(parser, configuration_info, algorithm_instance)
