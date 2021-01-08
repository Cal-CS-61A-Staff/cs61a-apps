from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()


setup(
    name="buildtool",
    version="0.1.*",
    author="Rahul Arya",
    author_email="rahularya@berkeley.edu",
    long_description=readme,
    long_description_content_type="text/markdown",
    licence="MIT",
    packages=find_packages(
        include=["buildtool", "buildtool.common", "buildtool.common.rpc"]
    ),
    package_data={"": ["**/*.tex"]},
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "buildtool=buildtool.__main__:cli",
            "bt=buildtool.__main__:cli",
        ]
    },
    python_requires=">=3.8",
    install_requires=["click", "flask", "cachetools", "colorama", "requests", "tqdm"],
)
