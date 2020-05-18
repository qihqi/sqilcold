from distutils.core import setup
setup(
  name = 'sqilcold',
  packages = ['sqilcold'],
  version = '0.1',
  license='bsd-3-clause',
  description = 'A small wrapper on SqlAlchemy to make dataclasses of DB records',
  author = 'Han Qi',
  author_email = 'qihan.dev@gmail.com',
  url = 'https://github.com/qihqi/sqilcold',
  download_url = 'https://github.com/qihqi/sqilcold/archive/v_01.tar.gz',
  keywords = ['Sqlalchemy', 'dataclass'],
  install_requires=[
          'sqlalchemy',
  ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
  ],
)
