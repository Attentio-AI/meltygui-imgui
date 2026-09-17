# -*- coding: utf-8 -*-
import os
import sys
import sysconfig
from itertools import chain

from setuptools import setup, Extension, find_packages

try:
    from Cython.Build import cythonize
except ImportError:
    # A 'cythonize' stub is needed so that build, develop and install can
    # start before Cython is installed.
    cythonize = lambda extensions, **kwargs: extensions  # noqa
    USE_CYTHON = False
else:
    USE_CYTHON = True


_CYTHONIZE_WITH_COVERAGE = os.environ.get("_CYTHONIZE_WITH_COVERAGE", False)

if _CYTHONIZE_WITH_COVERAGE and not USE_CYTHON:
    raise RuntimeError(
        "Configured to build using Cython "
        "and coverage but Cython not available."
    )


PREBUILT_WHEELS = "Linux x86-64 (glibc 2.28+) and Windows x86-64, CPython 3.11, 3.12 and 3.13"
COMPILING_COMMANDS = {"bdist_wheel", "build_ext", "build", "install", "develop", "editable_wheel"}

# Installers run this file only when no prebuilt wheel matches: say so.
# Release builds set MELTYGUI_IMGUI_RELEASE_BUILD=1 to stay quiet.
if COMPILING_COMMANDS.intersection(sys.argv) and not os.environ.get("MELTYGUI_IMGUI_RELEASE_BUILD"):
    import platform
    print("""{rule}
meltygui-imgui: no prebuilt wheel matches this platform
  this platform:   {system} {machine}, {implementation} {version}
  prebuilt wheels: {prebuilt}
Compiling from source instead (a few minutes). This needs a C++ compiler.
{rule}""".format(rule="*" * 72, system=platform.system(), machine=platform.machine(),
                 implementation=platform.python_implementation(), version=platform.python_version(),
                 prebuilt=PREBUILT_WHEELS), file=sys.stderr, flush=True)


def read(filename):
    with open(filename, 'r') as file_handle:
        return file_handle.read()


def get_version(version_tuple):
    if not isinstance(version_tuple[-1], int):
        return '.'.join(map(str, version_tuple[:-1])) + version_tuple[-1]
    return '.'.join(map(str, version_tuple))


init = os.path.join(os.path.dirname(__file__), 'meltygui_imgui', '__init__.py')
version_line = list(filter(lambda l: l.startswith('VERSION'), open(init)))[0]

VERSION = get_version(eval(version_line.split('=')[-1]))
README = os.path.join(os.path.dirname(__file__), 'README.md')


if sys.platform in ('cygwin', 'win32') and not sysconfig.get_platform().startswith('mingw'):  # Windows if not under MinGW
    # note: `/FI` means forced include in VC++/VC
    # note: may be obsoleted in future if ImGui gets patched
    os_specific_flags = ['/FIpy_imconfig.h']
    os_specific_libraries = []
    # placeholder for future
    os_specific_macros = []
else:  # OS X, Linux and Windows under MinGW (uses gcc)
    # note: `-include` means forced include in GCC/clang
    # note: may be obsoleted in future if ImGui gets patched
    # placeholder for future
    os_specific_flags = ['-includeconfig-cpp/py_imconfig.h']
    if sysconfig.get_platform().startswith('mingw'):
        os_specific_libraries = ["imm32"]
    else:
        os_specific_libraries = []
    os_specific_macros = []


if _CYTHONIZE_WITH_COVERAGE:
    compiler_directives = {
        'linetrace': True,
    }
    cythonize_opts = {
        'gdb_debug': True,
    }
    general_macros = [('CYTHON_TRACE_NOGIL', '1')]
else:
    compiler_directives = {}
    cythonize_opts = {}
    general_macros = []

if USE_CYTHON:
    import Cython
    if int(Cython.__version__.split('.')[0]) >= 3:
        # The bindings predate Cython 3: keep its callbacks' implicit noexcept
        # and the Python 2 style semantics they were written against.
        compiler_directives['legacy_implicit_noexcept'] = True
        compiler_directives['language_level'] = 2


def extension_sources(path):
    sources = ["{0}{1}".format(path, '.pyx' if USE_CYTHON else '.cpp')]
    
    if not USE_CYTHON:
        # note: Cython will pick these files automatically but when building
        #       a plain C++ sdist without Cython we need to explicitly mark
        #       these files for compilation and linking.
        sources += [
            'imgui-cpp/imgui.cpp',
            'imgui-cpp/imgui_draw.cpp',
            'imgui-cpp/imgui_demo.cpp',
            'imgui-cpp/imgui_widgets.cpp',
            'imgui-cpp/imgui_tables.cpp',
            'config-cpp/py_imconfig.cpp'
        ]

    return sources


def backend_extras(*requirements):
    """Construct list of requirements for backend integration.

    All built-in backends depend on PyOpenGL so add it as default requirement.
    """
    return ["PyOpenGL"] + list(requirements)

EXTRAS_REQUIRE = {
    'Cython':  ['Cython>=0.24,<0.30'],
    'cocos2d': backend_extras(
        "cocos2d",
        "pyglet>=1.5.6; sys_platform == 'darwin'",
    ),
    'sdl2': backend_extras('PySDL2'),
    'glfw': backend_extras('glfw'),
    'pygame': backend_extras('pygame'),
    'opengl': backend_extras(),
    'pyglet': backend_extras(
        "pyglet; sys_platform != 'darwin'",
        "pyglet>=1.5.6; sys_platform == 'darwin'",
    )
}

# construct special 'full' extra that adds requirements for all built-in
# backend integrations and additional extra features.
EXTRAS_REQUIRE['full'] = list(set(chain(*EXTRAS_REQUIRE.values())))

EXTENSIONS = [
    Extension(
        "meltygui_imgui.core", extension_sources("meltygui_imgui/core"),
        extra_compile_args=os_specific_flags,
        libraries=os_specific_libraries,
        define_macros=[
            # note: for raising custom exceptions directly in ImGui code
            ('PYIMGUI_CUSTOM_EXCEPTION', None)
        ] + os_specific_macros + general_macros,
        include_dirs=['meltygui_imgui', 'config-cpp', 'imgui-cpp', 'ansifeed-cpp'],
    ),
    Extension(
        "meltygui_imgui.internal", extension_sources("meltygui_imgui/internal"),
        extra_compile_args=os_specific_flags,
        libraries=os_specific_libraries,
        define_macros=[
            # note: for raising custom exceptions directly in ImGui code
            ('PYIMGUI_CUSTOM_EXCEPTION', None)
        ] + os_specific_macros + general_macros,
        include_dirs=['meltygui_imgui', 'config-cpp', 'imgui-cpp', 'ansifeed-cpp'],
    ),
]


setup(
    name="meltygui-imgui",
    version="2.0.0.post3",
    python_requires=">=3.11,<3.14",
    packages=find_packages('.'),

    author=u'Michał Jaworski',
    author_email='swistakm@gmail.com',

    description="Cython-based Python bindings for dear meltygui_imgui",
    long_description=read("MELTYGUI.md"),
    long_description_content_type="text/markdown",

    url="https://github.com/Attentio-AI/meltygui-imgui",

    ext_modules=cythonize(
        EXTENSIONS,
        compiler_directives=compiler_directives, **cythonize_opts
    ),
    extras_require=EXTRAS_REQUIRE,
    include_package_data=True,
        license_files=["LICENSE", "LICENSES/*"],

    license='BSD',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',

        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Cython',

        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',

        'Topic :: Games/Entertainment',
    ],
)
