import setuptools

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name="example_pkg_username",
    version="0.0.1",
    author="Example Author",
    author_email="author@example.com",
    description="Base_Docker_Support package",
    long_description="longde_scription",
    long_description_content_type="text/markdown",
    url="https://github.com/AgPipeline/base-docker-support/tree/master",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
