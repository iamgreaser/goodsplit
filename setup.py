import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="goodsplit-iamgreaser",
    version="0.0.0",
    author="GreaseMonkey",
    author_email="thematrixeatsyou@gmail.com",
    description="An autosplitter-first split timer for speedrunning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/iamgreaser/goodsplit",
    packages=setuptools.find_packages(),
    install_requires=[
        "sqlalchemy",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Zlib License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
