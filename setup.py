#from setuptools import setup, find_packages
from setuptools import setup, find_namespace_packages

setup(
    name = "ucode_upgrade",
    version = "0.1.0",
    description = "ucode_upgrade",
    long_description = "",

    packages = find_namespace_packages(include=["ucode", "ucode.*"]),
    package_data = {"ucode": ["*"],
                    "ucode.config": ["*"],
                    "ucode.config.locale": ["*"],
                    "ucode.config.locale.en_US": ["*"],
                    "ucode.config.locale.zh_CN": ["*"],
                    "ucode.config.locale.en_US.LC_MESSAGES": ["*"],
                    "ucode.config.locale.zh_CN.LC_MESSAGES": ["*"],
                    },
    include_package_data = True,
    platforms = "any",
    install_requires = []
)
