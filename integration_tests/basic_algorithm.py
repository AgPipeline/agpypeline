#!/usr/bin/env python3
"""
Test algorithm class
"""
from agpypeline.algorithm import Algorithm
from agpypeline import entrypoint

from basic_configuration import BasicConfiguration

class BasicAlgorithm(Algorithm):
    """Test Algorithm For Integration Tests"""

    def calculate(self):
        return 0


if __name__ == "__main__":
    CONFIGURATION = BasicConfiguration()
    entrypoint.entrypoint(CONFIGURATION, BasicAlgorithm())
