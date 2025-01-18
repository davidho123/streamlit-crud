from setuptools import setup, find_packages


with open( "README-zh.md", encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = '0.1'
DESCRIPTION = 'Automatically generate UI components based on the data model, and implement CRUD functionalities.'
LONG_DESCRIPTION = 'Dynamically generate form UI components based on the database model class, and implement functions for creating, deleting, updating, and querying.'

setup(
    name="streamlit_crud",
    version=VERSION,
    author="davidho",
    author_email="",
    url="https://github.com/davidho123/streamlit-crud",
    license="MIT",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=[],
    keywords=['crud', 'streamlit','model','function','python'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
    ]
)
