import pwd
import pam
from typing import Optional


def verify_system_user(username: str, password: str) -> bool:
    try:
        pwd.getpwnam(username)
    except KeyError:
        return False

    try:
        pam.authenticate(username, password)
        return True
    except Exception:
        return False


def get_user_info(username: str) -> Optional[dict]:
    try:
        user_entry = pwd.getpwnam(username)
        return {
            "username": username,
            "uid": user_entry.pw_uid,
            "gid": user_entry.pw_gid,
            "home": user_entry.pw_dir,
            "shell": user_entry.pw_shell,
        }
    except KeyError:
        return None


def list_system_users() -> list[str]:
    users = []
    for entry in pwd.getpwall():
        if entry.pw_shell and "/nologin" not in entry.pw_shell:
            users.append(entry.pw_name)
    return sorted(users)
