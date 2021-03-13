from setuptools import setup, find_packages

setup(
    name='Prass',
    version='0.1.1',
    py_modules=['prass'],
    packages=find_packages(),
    install_requires=['Click'],
    entry_points='''
        [console_scripts]
        prass=prass:cli
    ''',
)
