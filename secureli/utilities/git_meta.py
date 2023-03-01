import subprocess
import configparser


def git_user_email() -> str:
    """Leverage the command prompt to derive the user's email address"""
    args = ["git", "config", "user.email"]
    completed_process = subprocess.run(args, stdout=subprocess.PIPE)
    output = completed_process.stdout.decode("utf8").strip()
    return output


def origin_url() -> str:
    """Leverage the git config file to determine the remote origin URL"""
    git_config_parser = configparser.ConfigParser()
    git_config_parser.read(".git/config")
    return (
        git_config_parser['remote "origin"'].get("url", "UNKNOWN")
        if git_config_parser.has_section('remote "origin"')
        else "UNKNOWN"
    )


def current_branch_name() -> str:
    """Leverage the git HEAD file to determine the current branch name"""
    try:
        with open(".git/HEAD", "r") as f:
            content = f.readlines()
            for line in content:
                if line[0:4] == "ref:":
                    return line.partition("refs/heads/")[2].strip()
    except IOError:
        return "UNKNOWN"
