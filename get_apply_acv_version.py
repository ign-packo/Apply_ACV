""" Info on version """

import subprocess
import os

VERSION_FILE = 'apply_acv_version.py'


def get_git_revision():
    """ Get git revision """
    rev = 'Unknown'
    try:
        cmd = subprocess.check_output(['git', 'describe', '--dirty'])
        rev = cmd.decode('ascii').strip()
    except subprocess.SubprocessError:
        print('No git revision')
    except FileNotFoundError:
        print('Git not found')
    return rev


def write_file():
    """ Write file containing version information """
    with open(VERSION_FILE, 'w', encoding='utf-8') as fout:
        fout.write(f"APPLYACV_VERSION = '{get_git_revision()}'")


def delete_file():
    """ Delete file"""
    os.remove(VERSION_FILE)


try:
    # pylint: disable=locally-disabled, import-error, unused-import
    from apply_acv_version import APPLYACV_VERSION
# if module not found (i.e. outside whl package)
except ModuleNotFoundError:
    APPLYACV_VERSION = get_git_revision()
