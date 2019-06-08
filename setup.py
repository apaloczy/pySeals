from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='pySeals',
      version='0.1a',
      description='Python module to remove surface gravity wave biases from along-beam velocity data.',
      url='https://github.com/apaloczy/pySeals',
      license='MIT',
      packages=['pySeals', 'examples', 'tests'],
      install_requires=[
          'numpy',
          'matplotlib',
          'scipy',
          'pandas',
          'xarray',
          'cartopy',
      ],
      test_suite = 'nose.collector',
zip_safe=False)
