"""Allows for the code library to be an installable package and lists the install requirements
"""

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name="agpypeline",
    version="0.0.51",
    author="Jacob van der Leeuw",
    author_email="jvanderleeuw@email.arizona.edu",
    description="Installable package for entrypoint and drone-specific environment code within a transformer",
    long_description="Package containing entrypoint.py from entrypoint code and environment.py "
                     "for drone-specific environment code. This allows for transformers to have"
                     "common entrypoint and environment code in an installable package",
    long_description_content_type="text/markdown",
    url="https://github.com/AgPipeline/agpypeline",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=['setuptools==50.0.1', 'numpy', 'influxdb', 'requests>=2.21.0', 'python-dateutil', 'utm',
                      'matplotlib', 'Pillow', 'scipy', 'piexif', 'cryptography', 'pyyaml', 'pygdal==3.4.1.*',]

)
