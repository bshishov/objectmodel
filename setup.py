from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

pkg_vars = {}

with open("src/objectmodel/_version.py") as fp:
    exec(fp.read(), pkg_vars)

setup(
    name='objectmodel',
    version=pkg_vars['__version__'],
    description='Python typed object schema validation',
    url='https://github.com/bshishov/objectmodel',
    author='Boris Shishov',
    author_email='borisshishov@gmail.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages('src', exclude=('test*', 'examples')),
    package_dir={'': 'src'},
    license="MIT",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries'
    ],
    python_requires='>=3.5'
)
