import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "build_docker_images"
SOURCE_URL = "https://github.com/example/tool-repo"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


def git(cwd, *args):
    subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        env={**os.environ, **GIT_ENV},
    )


def write_definition(
    directory, name="tool", tag="3", extra="", dockerfile="FROM scratch\n"
):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "build.env").write_text(f"IMAGE_NAME={name}\nIMAGE_TAG={tag}\n{extra}")
    (directory / "Dockerfile").write_text(dockerfile)


def make_clone(parent, name, origin_url, definitions):
    """A real clone of a bare origin, with origin's URL rewritten to origin_url."""
    bare = parent / f"{name}-bare.git"
    clone = parent / name
    parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "--bare", "-b", "main", str(bare)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "clone", str(bare), str(clone)], check=True, capture_output=True
    )
    for rel, kwargs in definitions.items():
        write_definition(clone / rel, **kwargs)
    git(clone, "add", "-A")
    git(clone, "commit", "-m", "init")
    git(clone, "push", "origin", "HEAD:main")
    git(clone, "remote", "set-url", "origin", origin_url)
    return clone


@pytest.fixture
def script(tmp_path):
    """A copy of the script in a git repo named bioinformatics-scripts.

    The directory beside it is tmp_path/beside, which tests control.
    """
    repo = tmp_path / "beside" / "bioinformatics-scripts"
    (repo / "scripts").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    copy = repo / "scripts" / "build_docker_images"
    shutil.copy(SCRIPT, copy)
    return copy


@pytest.fixture
def beside(tmp_path):
    return tmp_path / "beside"


@pytest.fixture
def pointer(tmp_path):
    directory = tmp_path / "pointers" / "tool"
    write_definition(directory, extra=f"BUILT_IN={SOURCE_URL}\n")
    (directory / "Dockerfile").unlink()
    return directory


@pytest.fixture
def source_clone(tmp_path):
    return make_clone(
        tmp_path / "repos",
        "tool-repo",
        "git@github.com:example/tool-repo.git",
        {"docker/tool": {}},
    )


@pytest.fixture
def docker_log(tmp_path):
    """Put a fake docker first on PATH; returns the file recording its calls."""
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    log = tmp_path / "docker.log"
    fake = bin_dir / "docker"
    fake.write_text(f'#!/bin/bash\nprintf \'%s\\n\' "$*" >> "{log}"\n')
    fake.chmod(0o755)
    log.touch()
    return log


def run(script, *args, env=None, cwd=None, docker_log=None):
    full_env = {k: v for k, v in os.environ.items() if k != "GIT_REPO_ROOT"}
    full_env["TERM"] = "xterm"
    if docker_log is not None:
        full_env["PATH"] = f"{docker_log.parent / 'fakebin'}:{full_env['PATH']}"
    full_env.update(env or {})
    return subprocess.run(
        [str(script), *args],
        capture_output=True,
        text=True,
        env=full_env,
        cwd=cwd,
    )


def resolved(source_dir):
    return f"BUILT_IN_SOURCE\t{source_dir.resolve()}\n"


def test_resolve_prints_a_plain_definition_itself(script, tmp_path):
    plain = tmp_path / "plain"
    write_definition(plain)
    result = run(script, "-r", str(plain))
    assert result.returncode == 0
    assert result.stdout == resolved(plain)


def test_resolve_follows_a_pointer_to_the_matching_definition(
    script, source_clone, pointer
):
    result = run(
        script,
        "-r",
        str(pointer),
        env={"GIT_REPO_ROOT": str(source_clone.parent)},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == resolved(source_clone / "docker" / "tool")


def test_resolve_finds_the_clone_beside_bioinformatics_scripts_without_git_repo_root(
    script, beside, pointer
):
    clone = make_clone(
        beside,
        "tool-repo",
        SOURCE_URL + ".git",
        {"docker/tool": {}},
    )
    result = run(script, "-r", str(pointer))
    assert result.returncode == 0, result.stderr
    assert result.stdout == resolved(clone / "docker" / "tool")


def test_resolve_through_a_path_symlink_uses_the_scripts_own_clone(
    script, beside, pointer, tmp_path
):
    clone = make_clone(beside, "tool-repo", SOURCE_URL, {"docker/tool": {}})
    link_dir = tmp_path / "elsewhere"
    link_dir.mkdir()
    link = link_dir / "build_docker_images"
    link.symlink_to(os.path.relpath(script, link_dir))
    result = run(link, "-r", str(pointer), cwd=link_dir)
    assert result.returncode == 0, result.stderr
    assert result.stdout == resolved(clone / "docker" / "tool")


def test_resolve_falls_back_beside_the_script_when_git_repo_root_lacks_the_clone(
    script, beside, pointer, tmp_path
):
    clone = make_clone(beside, "tool-repo", SOURCE_URL, {"docker/tool": {}})
    empty = tmp_path / "empty"
    empty.mkdir()
    result = run(script, "-r", str(pointer), env={"GIT_REPO_ROOT": str(empty)})
    assert result.returncode == 0, result.stderr
    assert result.stdout == resolved(clone / "docker" / "tool")


def test_resolve_skips_a_same_named_clone_of_another_repository(
    script, beside, pointer, tmp_path
):
    make_clone(
        tmp_path / "repos",
        "tool-repo",
        "https://github.com/other/tool-repo.git",
        {"docker/tool": {}},
    )
    real = make_clone(beside, "tool-repo", SOURCE_URL, {"docker/tool": {}})
    result = run(
        script,
        "-r",
        str(pointer),
        env={"GIT_REPO_ROOT": str(tmp_path / "repos")},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == resolved(real / "docker" / "tool")


@pytest.mark.parametrize(
    "origin",
    [
        "git@github.com:example/tool-repo.git",
        "https://github.com/example/tool-repo",
        "ssh://git@github.com/Example/Tool-Repo.git",
        "https://github.com/EXAMPLE/TOOL-REPO.git/",
    ],
)
def test_resolve_matches_ssh_and_https_forms_and_case(
    script, pointer, tmp_path, origin
):
    pointer_env = pointer / "build.env"
    pointer_env.write_text(
        "IMAGE_NAME=tool\nIMAGE_TAG=3\nBUILT_IN=https://github.com/Example/Tool-Repo\n"
    )
    clone = make_clone(tmp_path / "repos", "tool-repo", origin, {"docker/tool": {}})
    result = run(script, "-r", str(pointer), env={"GIT_REPO_ROOT": str(clone.parent)})
    assert result.returncode == 0, result.stderr
    assert result.stdout == resolved(clone / "docker" / "tool")


@pytest.mark.parametrize("suffix", ["", "/"])
def test_resolve_accepts_a_relative_git_repo_root_with_trailing_slash(
    script, source_clone, pointer, tmp_path, suffix
):
    result = run(
        script,
        "-r",
        str(pointer),
        env={"GIT_REPO_ROOT": "repos" + suffix},
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == resolved(source_clone / "docker" / "tool")


def test_resolve_refuses_naming_every_directory_searched_and_the_clone_command(
    script, beside, pointer, tmp_path
):
    make_clone(
        tmp_path / "repos",
        "tool-repo",
        "https://github.com/other/tool-repo.git",
        {"docker/tool": {}},
    )
    result = run(
        script,
        "-r",
        str(pointer),
        env={"GIT_REPO_ROOT": str(tmp_path / "repos")},
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert f"tool:3 is built in {SOURCE_URL}" in result.stderr
    assert str(tmp_path / "repos") in result.stderr
    assert "origin https://github.com/other/tool-repo.git" in result.stderr
    assert str(beside) in result.stderr
    assert "missing" in result.stderr
    assert f'git clone {SOURCE_URL} "{tmp_path / "repos"}/tool-repo"' in result.stderr
    assert "GIT_REPO_ROOT" in result.stderr


def test_resolve_refuses_when_the_clone_lacks_the_tag_listing_what_it_has(
    script, pointer, tmp_path
):
    clone = make_clone(
        tmp_path / "repos",
        "tool-repo",
        SOURCE_URL,
        {"docker/tool": {"tag": "2"}},
    )
    result = run(script, "-r", str(pointer), env={"GIT_REPO_ROOT": str(clone.parent)})
    assert result.returncode == 1
    assert result.stdout == ""
    assert "the pointer wants tool:3, the clone defines tool:2" in result.stderr


def test_resolve_refuses_one_tag_defined_twice_differently(script, pointer, tmp_path):
    clone = make_clone(
        tmp_path / "repos",
        "tool-repo",
        SOURCE_URL,
        {
            "docker/tool": {},
            "docker/copy": {"dockerfile": "FROM scratch\nRUN true\n"},
        },
    )
    result = run(script, "-r", str(pointer), env={"GIT_REPO_ROOT": str(clone.parent)})
    assert result.returncode == 1
    assert result.stdout == ""
    assert "tool:3" in result.stderr
    assert "more than once" in result.stderr


def test_resolve_accepts_one_tag_defined_twice_identically(script, pointer, tmp_path):
    clone = make_clone(
        tmp_path / "repos",
        "tool-repo",
        SOURCE_URL,
        {"docker/tool": {}, "docker/copy": {}},
    )
    result = run(script, "-r", str(pointer), env={"GIT_REPO_ROOT": str(clone.parent)})
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("BUILT_IN_SOURCE\t")


def test_resolve_ignores_pointers_and_git_metadata_inside_the_clone(
    script, pointer, tmp_path
):
    clone = make_clone(
        tmp_path / "repos",
        "tool-repo",
        SOURCE_URL,
        {
            "docker/tool": {},
            "docker/pointer": {"extra": f"BUILT_IN={SOURCE_URL}\n"},
        },
    )
    write_definition(clone / ".git" / "stray", dockerfile="FROM scratch\nRUN false\n")
    result = run(script, "-r", str(pointer), env={"GIT_REPO_ROOT": str(clone.parent)})
    assert result.returncode == 0, result.stderr
    assert result.stdout == resolved(clone / "docker" / "tool")


def test_build_follows_a_pointer_and_builds_the_source_once(
    script, source_clone, pointer, tmp_path, docker_log
):
    second = tmp_path / "pointers" / "tool-again"
    write_definition(second, extra=f"BUILT_IN={SOURCE_URL}\n")
    (second / "Dockerfile").unlink()
    result = run(
        script,
        "-d",
        str(tmp_path / "pointers"),
        env={"GIT_REPO_ROOT": str(source_clone.parent)},
        docker_log=docker_log,
    )
    assert result.returncode == 0, result.stderr
    calls = docker_log.read_text().splitlines()
    assert len(calls) == 1
    source = (source_clone / "docker" / "tool").resolve()
    assert f"-f {source}/Dockerfile {source}" in calls[0]
    assert "-t tool:3" in calls[0]


def test_build_without_built_in_is_unchanged(script, tmp_path, docker_log):
    plain = tmp_path / "plain"
    write_definition(plain)
    result = run(script, "-d", str(plain), docker_log=docker_log)
    assert result.returncode == 0, result.stderr
    calls = docker_log.read_text().splitlines()
    assert len(calls) == 1
    assert f"-f {plain}/Dockerfile {plain}" in calls[0]


def test_nobuild_still_skips(script, tmp_path, docker_log):
    plain = tmp_path / "plain"
    write_definition(plain, extra="NOBUILD=true\n")
    result = run(script, "-d", str(plain), docker_log=docker_log)
    assert result.returncode == 0, result.stderr
    assert docker_log.read_text() == ""


def test_resolve_finds_a_lower_case_clone_directory_for_a_mixed_case_url(
    script, tmp_path
):
    pointer = tmp_path / "pointers" / "foo"
    write_definition(
        pointer,
        name="foo",
        extra="BUILT_IN=https://github.com/DNAstack/Foo\n",
    )
    (pointer / "Dockerfile").unlink()
    clone = make_clone(
        tmp_path / "repos",
        "foo",
        "git@github.com:dnastack/foo.git",
        {"docker/foo": {"name": "foo"}},
    )
    result = run(script, "-r", str(pointer), env={"GIT_REPO_ROOT": str(clone.parent)})
    assert result.returncode == 0, result.stderr
    assert result.stdout == resolved(clone / "docker" / "foo")


def test_resolve_accepts_exactly_the_directory_as_its_only_argument(script, tmp_path):
    plain = tmp_path / "plain"
    write_definition(plain)
    result = run(script, "-r", str(plain))
    assert result.returncode == 0, result.stderr
    assert result.stdout == resolved(plain)


def test_refusal_is_plain_text_when_stderr_is_not_a_terminal(script, pointer):
    env = {k: v for k, v in os.environ.items() if k not in ("TERM", "GIT_REPO_ROOT")}
    result = subprocess.run(
        [str(script), "-r", str(pointer)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "is built in" in result.stderr
    assert "\x1b" not in result.stderr
    assert "No value for $TERM" not in result.stderr
