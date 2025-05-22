# SPDX-License-Identifier: MIT

import os
import os.path

import nox


nox.options.default_venv_backend = 'uv|virtualenv'
nox.options.sessions = ['mypy', 'test']
nox.options.reuse_existing_virtualenvs = True


@nox.session(python='3.8')
def mypy(session):
    session.install('.', 'mypy')

    session.run('mypy', '-p', 'hid_parser')


@nox.session(python=['3.9', '3.10', '3.11', '3.12', '3.13'])
def test(session):
    htmlcov_output = os.path.join(session.virtualenv.location, 'htmlcov')
    xmlcov_output = os.path.join(session.virtualenv.location, f'coverage-{session.python}.xml')

    session.install('.', '--group', 'test')

    session.run(
        'pytest',
        '--cov',
        f'--cov-report=html:{htmlcov_output}',
        f'--cov-report=xml:{xmlcov_output}',
        'tests/',
        *session.posargs,
    )
