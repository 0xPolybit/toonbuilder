from setuptools import setup

setup(
    name='toonbuilder',
    version='0.1.0',
    description='Convert JSON and XML formatting to TOON, a schema-aware data formatting for LLM prompts.',
    url='https://github.com/0xPolybit/toonbuilder',
    author='Polybit',
    author_email='swastikbiswas962@gmail.com',
    license='MIT-0',
    packages=['toonbuilder'],
    install_requires=[],
    classifiers=[
        'Development Status :: Experimental',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)