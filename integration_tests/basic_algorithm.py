#!/usr/bin/env python3
"""
Test algorithm class
"""
from agpypeline.algorithm import Algorithm
from agpypeline import entrypoint

from agpypeline.configuration import Configuration


class BasicAlgorithm(Algorithm):
    """Test Algorithm For Integration Tests"""

    def calculate(self):
        return 0


if __name__ == "__main__":
    CONFIGURATION = Configuration()
    entrypoint.entrypoint(CONFIGURATION, BasicAlgorithm())
