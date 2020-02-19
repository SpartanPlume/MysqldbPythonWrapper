"""Needed for package creation"""

from setuptools import setup

setup(
    name="mysqldb_wrapper",
    version="0.1",
    description="A small package that wraps MySQLdb for easy usage and encryption",
    keywords="mysqldb mysql mysqldb_wrapper encryption hash",
    url="https://github.com/SpartanPlume/MysqldbPythonWrapper",
    author="Spartan Plume",
    author_email="spartan.plume@gmail.com",
    license="MIT",
    packages=["mysqldb_wrapper"],
    install_requires=["mysqlclient", "cryptography"],
    zip_safe=False,
)
