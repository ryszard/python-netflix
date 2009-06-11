from setuptools import setup, find_packages
import sys

dependencies = ['oauth']

if sys.version < 2.6:
    dependencies.append('simplejson')

setup(
    name = "netflix",
    version = "0.2.2",
    description="A very simple Python client for the Netflix API",
    author="Ryszard Szopa",
    author_email="ryszard.szopa@gmail.com",
    url="http://github.com/ryszard/python-netflix/",
    packages = find_packages(),
    keywords='internet netflix api',
    zip_safe=True,
    long_description = """\
Extremely simple client for the API of Netflix.""",
    install_requires = dependencies,
    license = 'MIT',
    package_data = {
        '': ['*.txt', '*.rst', '*.markdown'],},
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Internet",
      ],


)
