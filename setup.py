import setuptools

try:
    with open('README.md', 'rt', encoding='UTF8') as fh:
        long_description = fh.read()
except IOError as e:
    long_description = ""

setuptools.setup(
    name="dc_api",
    version="0.7.0",
    author="Eunchul, Song",
    author_email="eunchulsong9@gmail.com",
    description="Deadly dimple unofficial dcinside api",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/song9446/dcinside-python3-api",
    #packages=setuptools.find_packages(),
    py_modules=['dc_api'],
    install_requires=[
        'lxml',
        'aiohttp',
        'tenacity',
    ],
    entry_points     = """
           [console_scripts]
           dc_api = dc_api:dc_api
       """,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
