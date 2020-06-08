"""My nifty transformer
"""

import argparse
import transformer_class


# pylint: disable=unused-argument
def add_parameters(parser: argparse.ArgumentParser) -> None:
    """Adds parameters
    Arguments:
        parser: instance of argparse
    """


def check_continue(transformer: transformer_class.Transformer, **kwargs) -> tuple:
    """Checks if conditions are right for continuing processing
    Arguments:
        transformer: instance of transformer class
    Return:
        Returns a tuple containing the return code for continuing or not, and
        an error message if there's an error
    """
    print("check_continue(): received arguments: %s" % str(kwargs))
    return (0, "We are good here")


def perform_process(transformer: transformer_class.Transformer, **kwargs) -> dict:
    """Performs the processing of the data
    Arguments:
        transformer: instance of transformer class
    Return:
        Returns a dictionary with the results of processing
    """
    print("perform_process(): received arguments: %s" % str(kwargs))
    return {'code': 0, 'message': "Everything is going swimmingly"}
