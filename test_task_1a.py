import unittest
from pyfakefs.fake_filesystem_unittest import TestCase
from unittest.mock import patch, mock_open

from home_task import task_1a


class TestTask1A(TestCase):
    def test_remove_ignored_objects(self):

        paths = [
            "__init__.py",
            "__pycache__/perfectly_filterable_folder/test.py",
            "f_folder/__pycache__/file.py",
            "test_file_with_weird_name.py",
            "__init__.why/test.py",
        ]

        split = 3
        to_be_ignored = paths[:split]
        to_be_filtered = paths[split:]

        paths_filtered, paths_ignored = task_1a.remove_ignored_objects(paths)
        self.assertListEqual(paths_filtered, to_be_filtered)
        self.assertListEqual(paths_ignored, to_be_ignored)

    def test_get_git_url(self):
        file_data = "clearly not git url pattern"
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            self.assertRaises(Exception, task_1a.get_git_url)

        file_data = """			
			[remote "origin"]
				url = git@git.ccl:mock_group/mock_project.git
				fetch = +refs/heads/*:refs/remotes/origin/*			
		"""
        path = "git@git.ccl:mock_group/mock_project.git"

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            self.assertEqual(task_1a.get_git_url(), path)

    def test_get_git_remote_group_name(self):
        with patch("task_1a.os.environ.get") as mock_os_env_get:
            mock_os_env_get.return_value = "some CI project namespace"
            self.assertEqual(
                task_1a.get_git_remote_group_name(), "some CI project namespace"
            )

        with patch("task_1a.os.environ.get") as mock_os_env_get:
            mock_os_env_get.return_value = None
            with patch("task_1a.get_git_url") as mock_get_git_url:
                mock_get_git_url.return_value = (
                    "git@git.ccl:mock_group/mock_project.git"
                )
                self.assertEqual(task_1a.get_git_remote_group_name(), "mock_group")

    def test_get_git_remote_repo_name(self):
        with patch("task_1a.os.environ.get") as mock_os_env_get:
            mock_os_env_get.return_value = "some CI project name"
            self.assertEqual(task_1a.get_git_remote_repo_name(), "some CI project name")

        with patch("task_1a.os.environ.get") as mock_os_env_get:
            mock_os_env_get.return_value = None
            with patch("task_1a.get_git_url") as mock_get_git_url:
                mock_get_git_url.return_value = (
                    "git@git.ccl:mock_group/mock_project.git"
                )
                self.assertEqual(task_1a.get_git_remote_repo_name(), "mock_project")

    def test_get_git_current_branch_name(self):
        with patch("task_1a.os.environ.get") as mock_os_env_get:
            mock_os_env_get.return_value = "master"
            self.assertEqual(task_1a.get_git_current_branch_name(), "master")

            mock_os_env_get.return_value = "rc"
            self.assertEqual(task_1a.get_git_current_branch_name(), "rc")

            mock_os_env_get.return_value = task_1a.STAGE_BRANCH_NAME
            self.assertEqual(
                task_1a.get_git_current_branch_name(), task_1a.STAGE_BRANCH_NAME
            )

        with patch("task_1a.os.environ.get") as mock_os_env_get:
            mock_os_env_get.return_value = None
            file_data = "ref: refs/heads/master"
            with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
                self.assertEqual(task_1a.get_git_current_branch_name(), "master")

    def test_recursive_traverse(self):
        self.setUpPyfakefs()
        self.fs.create_file("/test/file.txt")
        self.fs.create_file("/test/test2/file.txt")

        expected_result = [
            ["tmp", "test", "test/test2"],
            ["test/file.txt", "test/test2/file.txt"],
        ]
        self.assertListEqual(task_1a.recursive_traverse(""), expected_result)

        expected_result = [["test2"], ["file.txt", "test2/file.txt"]]
        self.assertListEqual(task_1a.recursive_traverse("test"), expected_result)

    def test_is_positive_int(self):
        self.assertEqual(task_1a.is_positive_int("1234"), True)
        self.assertEqual(task_1a.is_positive_int(5313), True)

        self.assertEqual(task_1a.is_positive_int("-16"), False)
        self.assertEqual(task_1a.is_positive_int(-2), False)
        self.assertEqual(task_1a.is_positive_int(None), False)

        # I feel like this should pass as well or the name of the function
        # should be is_positive_num. But it probably depends on the context
        # self.assertEqual(task_1a.is_positive_int(3.14), False)

    def test_string_replacements(self):
        repls = {"env": "dev", "foo": "bar"}

        d = {"path": "/foo/$env/bar", "name": "foo bar", "email": "$foo@bar.cz"}
        expected_res = {
            "path": "/foo/dev/bar",
            "name": "foo bar",
            "email": "bar@bar.cz",
        }
        self.assertDictEqual(task_1a.string_replacements(d, repls), expected_res)

        d = ["/foo/$env/bar", "foo/$bar", "$foo@bar.cz"]
        expected_res = ["/foo/dev/bar", "foo/$bar", "bar@bar.cz"]
        self.assertListEqual(task_1a.string_replacements(d, repls), expected_res)

        d = "/$envA$env/v/bar"
        expected_res = "/$envAdev/v/bar"
        self.assertEqual(task_1a.string_replacements(d, repls), expected_res)

    def test_project_name(self):
        with patch("task_1a.get_git_remote_group_name") as mock_get_git_group:
            with patch("task_1a.get_git_remote_repo_name") as mock_get_git_repo:
                mock_get_git_group.return_value = "pentaho"
                mock_get_git_repo.return_value = "etl"
                self.assertEqual(task_1a.project_name(), "pentaho/etl")
                self.assertEqual(task_1a.project_name(escape=True), "pentaho%2Fetl")

    def test_pares_library(self):
        # zero case
        library = {}
        self.assertRaises(ValueError, task_1a.parse_library, library)

        # 2 case
        library = {"pypi": {"package": "keras"}, "egg": "sklearn"}
        self.assertRaises(AssertionError, task_1a.parse_library, library)

        # happy flow
        library = {"pypi": {"package": "keras"}}
        self.assertTupleEqual(task_1a.parse_library(library), ("pypi", "keras"))


if __name__ == "__main__":
    unittest.main()
