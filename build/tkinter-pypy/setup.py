#! /usr/bin/env python
from setuptools import setup, Extension

setup(name="tkinter-pypy",
      version="0.1",
      description="Python interface to Tk GUI toolkit (for PyPy)",
      author="Python development team and PyPy development team",
      author_email="pypy-dev@codespeak.net",
      url="http://bitbucket.org/pypy/tkinter/",
      license="Modified CNRI Open Source License",
      ext_modules=[
        Extension("_tkinter",
                  ["src/_tkinter.c", "src/tkappinit.c"],
                  define_macros=[('WITH_APPINIT', None)],
                  library_dirs=["/usr/X11R6/lib"],
                  include_dirs=["/usr/include/tcl", "/usr/include/tk"],
                  libraries=["tk8.4", "tcl8.4", "X11"],
                  )],
      )
