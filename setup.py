from distutils.core import setup

setup(
    name='django-mongom2m',
    version='0.1.0',
    author=u'Kenneth Falck',
    author_email='kennu@iki.fi',
    packages=['mongom2m', 'mongom2m_testapp'],
    url='https://github.com/kennu/django-mongom2m',
    license='BSD licence, see LICENCE.txt',
    description='A ManyToManyField for django-mongodb-engine',
    long_description='A ManyToManyField for django-mongodb-engine',
    zip_safe=False,
)

