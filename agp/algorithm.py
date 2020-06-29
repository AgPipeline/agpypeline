"""Template class for a Transformer Algorithm
"""
from agp.environment import Environment


class Algorithm:
    """Class for containing a Transformer Algorithm
    """

    def __init__(self):
        """Initializes a class instance
        """

    def perform_process(self, environment: Environment, check_md: dict, transformer_md: dict,
                        full_md: list) -> dict:
        """Perform the processing of data
        Arguments:
            environment: instance of Environment class
            check_md: metadata for this Transformer execution run
            transformer_md: transformer specific information from previous runs
            full_md: the list of loaded metadata
        """
        # pylint: disable=unused-argument,no-self-use
        raise RuntimeError("The Algorithm class method perform_process() must be overridden by a derived class")
