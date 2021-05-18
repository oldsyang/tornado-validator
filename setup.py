from setuptools import setup

import tornado_validator

setup(
    name="tornado_validator",
    keywords="validator",
    author="oldsyang",
    author_email="yq@oldsyang.com",
    url="https://github.com/oldsyang/tornado-validator.git",
    description="tornado validator with decorators.",
    version=tornado_validator.VERSION,
    packages=[
        "tornado_validator",
    ],
    license="MIT",
    install_requires=[
        "tornado>=5.0.2"
    ],
)
