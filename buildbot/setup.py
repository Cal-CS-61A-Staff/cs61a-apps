from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()


setup(
    name="hack",
    version="0.0.*",
    author="Rahul Arya",
    author_email="rahularya@berkeley.edu",
    long_description=readme,
    long_description_content_type="text/markdown",
    licence="MIT",
    packages=find_packages(
        include=["buildbot", "buildbot.common", "buildbot.common.rpc"]
    ),
    package_data={"": ["**/*.tex"]},
    include_package_data=True,
    entry_points={"console_scripts": ["buildbot=buildbot.__main__:cli"]},
    python_requires=">=3.8",
    install_requires=[
        "click",
        "flask",
        "cachetools",
        "colorama",
        "requests",
        "asciimatics",
    ],
)
