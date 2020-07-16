"""Configuration information for an AgPipeline Transformer
"""


class Configuration:
    """Contains configuration information on Transformers
    """
    # Silence this error until we have public methods
    # pylint: disable=too-few-public-methods
    # The version number of the transformer
    transformer_version = None

    # The transformer description
    transformer_description = None

    # Short name of the transformer
    transformer_name = None

    # The sensor associated with the transformer
    transformer_sensor = None

    # The transformer type (eg: 'rgbmask', 'plotclipper')
    transformer_type = None

    # The name of the author of the extractor
    author_name = None

    # The email of the author of the extractor
    author_email = None

    # Contributors to this transformer
    contributors = []

    # Repository URI of where the source code lives
    repository = None

    # Override flag for disabling the metadata file requirement.
    # Uncomment and set to False to override default behavior
    # metadata_needed = True
