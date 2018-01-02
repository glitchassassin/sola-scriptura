from setuptools import setup

def readme():
    with open("README.rst", "r") as f:
        return f.read()

setup(  name="SolaScriptura",
        version="0.1",
        description="A cross-platform interactive Bible reader for the terminal",
        long_description=readme(),
        classifiers=[
            "Development Status :: 4 - Beta",
            "Environment :: Console",
            "Intended Audience :: End Users/Desktop",
            "License :: OSI Approved :: MIT License",
            "Topic :: Religion"
        ],
        keywords="bible reader interactive terminal",
        url="https://github.com/glitchassassin/sola-scriptura",
        author="Jon Winsley",
        author_email="jon.winsley@gmail.com",
        license="MIT",
        packages=["solascriptura"],
        install_requires=["urwid", "pysword"],
        entry_points={"console_scripts": ["solascriptura = solascriptura.main"]},
        zip_safe=False
)