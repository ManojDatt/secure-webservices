import setuptools, os
from setuptools import find_packages, setup
with open("README.md", "r") as fh:
    long_description = fh.read()

project_var_name = "secure-webservices"
here = os.path.dirname(__file__)
packages = find_packages()
setup(
    name="secure-webservices",
    version="1.1.2",
    author="manojdatt1it",
    author_email="manojdatt1it@gmail.com",
    description="A wrapper tool that allow to enable auth service implementation works like SSO, creating your server and clients",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ManojDatt/secure-webservices.git",
    packages=packages,
    include_package_data = True,
    classifiers=[
        "Programming Language :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
