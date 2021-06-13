"""Needed for package creation"""

from setuptools import setup

from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="mysqldb_wrapper",
    version="0.10.0",
    description="A small package that wraps MySQLdb for easy usage and encryption",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="mysqldb mysql mysqldb_wrapper encryption hash",
    url="https://github.com/SpartanPlume/MysqldbPythonWrapper",
    author="Spartan Plume",
    author_email="spartan.plume@gmail.com",
    license="MIT",
    packages=["mysqldb_wrapper"],
    install_requires=["mysqlclient", "cryptography"],
    zip_safe=False,
)
