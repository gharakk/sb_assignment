import logging
import os
import re
from string import Template
from typing import List, Union
from urllib.parse import quote_plus
from glom import glom
from typing import Tuple
import json


# Constants
STAGE_BRANCH_NAME = 'dev'
MAP_BRANCH_ENV = {
    STAGE_BRANCH_NAME: 'stage',
    'rc': 'rc',
    'master': 'prod'
}

PATTERN_GIT_URL = re.compile(r'.*(git@git\.ccl:.+\/.+\.git.*)')
PATTERN_GIT_REPO_NAME = re.compile(r'.*git@git\.ccl:(.+)\/(.+)\.git.*')
SBDB_IGNORE_LOCAL = [
    '__init__.py',
    '__pycache__'
]

def is_ignored_path(path: str) -> bool:
    """
    Returns True, if specified path shouldn't be uploaded to Databricks
    """
    for ignored in SBDB_IGNORE_LOCAL:
        if ignored in os.path.normpath(path).split(os.path.sep):
            return True
    return False


def remove_ignored_objects(paths: List[str]) -> (List[str], List[str]):
    """
    Splits the input list into a list of filtered paths & a list of ignored paths
    """
    paths_ignored = []
    paths_filtered = []

    for path in paths:
        if is_ignored_path(path):
            paths_ignored.append(path)
        else:
            paths_filtered.append(path)

    return (paths_filtered, paths_ignored)


def get_git_url() -> str:
    """
    Returns remote git repository name
    """
    with open(os.path.join('.git', 'config'), 'r') as f:
        for line in f:
            extract = PATTERN_GIT_URL.search(line)
            if (extract):
                return extract.group(1)

    logging.error(
        'Remote git repository name must be in ./.git/config & defined using a git@git.ccl:GROUP/PROJECTNAME.git format'
    )
    raise Exception('Can\'t find repository name')


def get_git_remote_group_name() -> str:
    CI_PROJECT_NAMESPACE = os.environ.get('CI_PROJECT_NAMESPACE')
    if (CI_PROJECT_NAMESPACE is not None):
        logging.info('Found CI_PROJECT_NAMESPACE=%s', CI_PROJECT_NAMESPACE)
        return CI_PROJECT_NAMESPACE

    return PATTERN_GIT_REPO_NAME.search(get_git_url()).group(1)


def get_git_remote_repo_name() -> str:
    CI_PROJECT_NAME = os.environ.get('CI_PROJECT_NAME')
    if (CI_PROJECT_NAME is not None):
        logging.info('Found CI_PROJECT_NAME=%s', CI_PROJECT_NAME)
        return CI_PROJECT_NAME

    return PATTERN_GIT_REPO_NAME.search(get_git_url()).group(2)


def get_git_current_branch_name() -> str:
    """
    Returns currently checked out GIT branch
    """
    CI_COMMIT_REF_NAME = os.environ.get('CI_COMMIT_REF_NAME')
    if (CI_COMMIT_REF_NAME in MAP_BRANCH_ENV.keys()):
        logging.info('Found CI_COMMIT_REF_NAME=%s', CI_COMMIT_REF_NAME)
        return CI_COMMIT_REF_NAME

    with open(os.path.join('.git', 'HEAD'), 'r') as f:
        f_content = f.readlines()[0]
        branch_name = f_content[f_content.index('/heads/') + 7:].strip(' \n\t')
    return branch_name


def recursive_traverse(target_dir: str) -> List[List[str]]:
    """
    Recursively traverse through the filesystem target_dir
    and returns a list of directories & files (paths relative to target_dir)

    response[0] -> list of directories
    response[1] -> list of files
    """
    accum_dirs, accum_files = [], []
    for root, dirs, files in os.walk(target_dir):
        for name in dirs:
            accum_dirs.append(os.path.relpath(os.path.join(root, name), target_dir))
        for name in files:
            accum_files.append(os.path.relpath(os.path.join(root, name), target_dir))

    return [accum_dirs, accum_files]


def is_positive_int(val: Union[str, int, None]) -> bool:
    """Returns true, if input value represents a positive integer"""
    if val is None:
        return False

    try:
        return int(val) > 0
    except ValueError:
        return False


def string_replacements(d: Union[dict, list, str], repls: dict) -> Union[dict, list, str]:
    """
    Replaces variables in all string values in a dictionary
    E.g. d = {'path': '/foo/$env/bar'}; repls = {'env': 'dev'}
    would result in {'path': '/foo/dev/bar'}
    """
    if isinstance(d, str):
        return Template(d).safe_substitute(repls)
    elif isinstance(d, list):
        return [string_replacements(j, repls) for j in d]
    elif isinstance(d, dict):
        return {k: string_replacements(v, repls) for k, v in d.items()}

    return d


def project_name(escape: bool = False) -> str:
    """
    Given a git group 'pentaho' and repo 'etl', return 'pentaho/etl'
    """
    project = '{}/{}'.format(get_git_remote_group_name(), get_git_remote_repo_name())
    if escape:
        return quote_plus(project)
    return project


def parse_library(library: dict) -> Tuple[str, str]:
    """
    When listing data from the Databricks API, libraries are exported
    in a weird format:

    ```
        "library": {
            "pypi": {
                "package": "keras"
            }
        },
    ```

    We need to export the type (pypi, maven, jar, ...) and the package name.
    """
    mp = [('pypi', 'pypi.package'), ('jar', 'jar'), ('maven', 'maven.coordinates'),
          ('egg', 'egg'), ('whl', 'whl')]
    libs = [(src, glom(library, pkg)) for src, pkg in mp if glom(library, pkg, default=None)]
    if len(libs) == 0:
        raise ValueError('Unknown library definition: {}'.format(json.dumps(library)))
    assert len(libs) == 1, 'Expected one library for each entry, got: {}'.format(json.dumps(library))

    return libs[0]
