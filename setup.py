"""
Setup script for the OPS API package.
"""

from setuptools import setup, find_packages

setup(
    name="ops_api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=1.18.0",
        "requests>=2.22.0",
        "pytz>=2019.3",
        "uscis-opts>=0.1.4",
        "python-dotenv>=0.19.0",
        "boto3>=1.18.0",
        "aws-lambda-powertools>=1.25.0",
    ],
    entry_points={
        "console_scripts": [
            "ops-api=ops_api.main:main",
        ],
    },
    author="CVP",
    author_email="info@cvpcorp.com",
    description="OPS API for syncing SIR data from Archer to DHS OPS Portal",
    keywords="ops, api, archer, dhs",
    python_requires=">=3.6",
)
