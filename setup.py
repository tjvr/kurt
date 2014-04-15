import glob
import re
from setuptools import setup


version = re.search("__version__ = '([^']+)'",
                    open('kurt/__init__.py').read()).group(1)


setup(name = 'kurt',
      version = version,
      author = 'Tim Radvan',
      author_email = 'blob8108@gmail.com',
      url = 'https://github.com/blob8108/kurt',
      description = "Library for reading/writing MIT's Scratch file format.",
      install_requires = ['construct == 2.0.6', 'pillow >= 2.0'],
      keywords = ['scratch'],
      license = 'LGPL',
      packages = ['kurt', 'kurt.scratch14', 'kurt.scratch20'],
      scripts = glob.glob('util/*'),
      test_suite='tests',
      classifiers = [
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Education",
        "Environment :: Console",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Education",
      ],
      long_description = open("README.md").read(),
)
