from setuptools import setup, find_packages

setup(
  name = 'recast-rivet-recaster-demo',
  version = '0.0.1',
  description = 'recast-rivet-recaster-demo',
  url = 'http://github.com/recast-hep/recast-rivet-recaster-demo',
  author = 'Lukas Heinrich',
  author_email = 'lukas.heinrich@cern.ch',
  packages = find_packages(),
  include_package_data = True,
  install_requires = [
    'Flask',
    'yoda',
  ],
  dependency_links = [
  ]
)
