from setuptools import setup

setup(
    name='nwae.utils',
    version='1.8.2',
    packages=[
        'nwae.utils',
        'nwae.utils.audio',
        'nwae.utils.data',
        'nwae.utils.networking',
        'nwae.utils.sec',
    ],
    package_dir={'': 'src'},
    install_requires=[
        # 'numpy',
        # 'pandas',
        # 'requests',
        # 'urllib3',
        # 'pydub'
    ],
    url='',
    license='',
    author='nwae',
    author_email='mapktah@ya.ru',
    description='Basic & Useful Utilities'
)
