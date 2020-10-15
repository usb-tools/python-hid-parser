# SPDX-License-Identifier: MIT

import os
import os.path

import nox


nox.options.sessions = ['mypy', 'test']
nox.options.reuse_existing_virtualenvs = True


@nox.session(python='3.8')
def mypy(session):
    session.install('.', 'mypy')

    session.run('mypy', '-p', 'hid_parser')


@nox.session(python=['3.7', '3.8', '3.9'])
def test(session):
    htmlcov_output = os.path.join(session.virtualenv.location, 'htmlcov')
    xmlcov_output = os.path.join(session.virtualenv.location, f'coverage-{session.python}.xml')

    session.install('.[test]')

    session.run(
        'pytest', '--cov', '--cov-config', 'setup.cfg',
        f'--cov-report=html:{htmlcov_output}',
        f'--cov-report=xml:{xmlcov_output}',
        'tests/', *session.posargs
    )
