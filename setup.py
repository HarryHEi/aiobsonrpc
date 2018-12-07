import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='aiobsonrpc',
    version='0.0.2',
    author='DarHarry',
    author_email='harryx520@qq.com',
    description='A Python library for JSON-RPC 2.0',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/HarryHEi/aiobsonrpc',
    packages=setuptools.find_packages(),
    classifiers=(
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ),
)