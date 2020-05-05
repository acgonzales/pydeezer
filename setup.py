import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="py-deezer",
    version="1.1.1",
    author="Aaron Gonzales",
    author_email="aaroncgonzales.dev@gmail.com",
    description="A package to search and download musics on Deezer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Chr1st-oo/pydeezer",
    packages=setuptools.find_packages(),
    install_requires=[
        "requests",
        "cryptography",
        "mutagen",
        "tqdm",
        "click",
        "pyinquirer"
    ],
    license="GNU GPL v3",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    entry_points="""
        [console_scripts]
        pydeezer=pydeezer.cli:cli
    """
)
