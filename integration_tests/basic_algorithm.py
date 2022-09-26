#!/usr/bin/env python3
"""
Test algorithm class
"""
from agpypeline.algorithm import Algorithm
from agpypeline import entrypoint

from agpypeline.checkmd import CheckMD
from agpypeline.configuration import Configuration
from agpypeline.environment import Environment


class BasicAlgorithm(Algorithm):
    """Test Algorithm For Integration Tests"""

    def perform_process(self, environment: Environment, check_md: CheckMD, transformer_md: dict,
                        full_md: list) -> dict:
        """Perform the processing of data
        Arguments:
            environment: instance of Environment class
            check_md: metadata for this Transformer execution run
            transformer_md: transformer specific information from previous runs
            full_md: the list of loaded metadata
         """
        return 0


if __name__ == "__main__":
    CONFIGURATION = Configuration()
    entrypoint.entrypoint(CONFIGURATION, BasicAlgorithm())
