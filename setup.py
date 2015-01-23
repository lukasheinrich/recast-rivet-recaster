from setuptools import setup, find_packages

setup(
  name = '',
  version = '0.0.1',
  description = 'recast-rivet-recaster-demo',
  url = 'http://github.com/lukasheinrich/recast-rivet-recaster-demo',
  author = 'Lukas Heinrich',
  author_email = 'lukas.heinrich@cern.ch',
  packages = find_packages(),
  install_requires = [
    'Flask',
    'celery',
    'recast-api',
    'yoda',
    'socket.io-python-emitter',
    'redis'
  ],
  dependency_links = [
    'https://github.com/ziyasal/socket.io-python-emitter/tarball/master#egg=socket.io-python-emitter-0.1.3',
  ]
)