"""Configuration information for an AgPipeline Transformer
"""


class Configuration:
    # The version number of the transformer
    TRANSFORMER_VERSION = None

    # The transformer description
    TRANSFORMER_DESCRIPTION = None

    # Short name of the transformer
    TRANSFORMER_NAME = None

    # The sensor associated with the transformer
    TRANSFORMER_SENSOR = None

    # The transformer type (eg: 'rgbmask', 'plotclipper')
    TRANSFORMER_TYPE = None

    # The name of the author of the extractor
    AUTHOR_NAME = None

    # The email of the author of the extractor
    AUTHOR_EMAIL = None

    # Contributors to this transformer
    CONTRUBUTORS = []

    # Repository URI of where the source code lives
    REPOSITORY = None

    # Override flag for disabling the metadata file requirement.
    # Uncomment and set to False to override default behavior
    # METADATA_NEEDED = True
