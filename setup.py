"""" Packaging and distribution """
from setuptools import setup, find_packages
from get_apply_acv_version import get_git_revision, write_file, delete_file

# write file with version info
write_file()

with open("README.md", "r") as frdm:
    long_description = frdm.read()

setup(
    name="apply_acv",
    version=get_git_revision(),
    author="IGN",
    url="https://github.com/ign-packo/Apply_ACV",
    description="Application courbes acv",
    long_description=long_description,
    py_modules=['apply_acv_version', 'get_apply_acv_version'],
    scripts=['apply_acv.py', 'create_cmd.py', 'test_diff.py'],
    packages=find_packages(),
    install_requires=['scipy'],
    python_requires=">=3.7",
)

# delete file with version info
delete_file()
