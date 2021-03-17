from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()


setup(
    name="examtool",
    version="2.2.*",
    author="Rahul Arya",
    author_email="rahularya@berkeley.edu",
    long_description=readme,
    long_description_content_type="text/markdown",
    licence="MIT",
    packages=find_packages(
        include=["examtool.api", "examtool.cli", "examtool.gui_files"]
    ),
    package_data={"": ["**/*.tex"]},
    include_package_data=True,
    entry_points={"console_scripts": ["examtool=examtool.cli.__main__:cli"]},
    python_requires=">=3.6",
    install_requires=["cryptography"],
    extras_require={
        "admin": [
            "pytz",
            "requests",
            "pypandoc",
            "google-cloud-firestore",
            "google-auth",
            "sendgrid",
        ],
        "cli": [
            "click",
            "pikepdf",
            "pytz",
            "requests",
            "fpdf",
            "pypandoc",
            "sendgrid",
            "func-timeout",
            "fullGSapi>=1.3.7",
            "tqdm",
            "numpy",
            "opencv-python",
            "pdfkit",
        ],
    },
)
