from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')


def get_version(root_path):
    with open(root_path / 'src' / 'pyopenapi3' / '__init__.py') as f:
        for line in f:
            if line.startswith('__version__ ='):
                return line.split('=')[1].strip().strip('"\'')


version = get_version(here)

setup(
    name='pyopenapi3',
    version=version,
    license="MIT",
    description='Generate OpenAPI3 from Python objects',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Algebra8/pyopenapi3',
    author='Milad M. Nasr',
    author_email='milad.m.nasr@gmail.com',
    package_dir={'': 'src'},
    packages=find_packages(where='src', exclude=['tests', 'examples']),
    python_requires='>=3.8',
    install_requires=[
        'pydantic', 'email_validator>=1.1.2', 'PyYAML==5.4.1'
    ],
    extras_require={
        'test': ['pytest==6.2.2', 'mypy==0.812'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    project_urls={
        'Source': 'https://github.com/Algebra8/pyopenapi3',
    },
)
