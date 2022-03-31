import inspect
import sqlite3
import os


def get_function_name(): return inspect.stack()[1][3]


def get_root_path():
    document_path = os.path.expanduser('~/Documents')
    root_path = f"{document_path}/youtube-scripts"
    os.makedirs(root_path, exist_ok=True)
    return root_path


def get_downloader_path():
    print(f"[{get_function_name()}]")
    root_path = get_root_path()
    project_path = f"{root_path}/downloader"
    os.makedirs(project_path, exist_ok=True)
    return project_path


def get_watchlist_path():
    print(f"[{get_function_name()}]")
    root_path = get_root_path()
    project_path = f"{root_path}/watchlist"
    os.makedirs(project_path, exist_ok=True)

    database_path = f"{project_path}/watchlist.db"
    client_secret_path = f"{project_path}/client_secret.json"
    client_token_path = f"{project_path}/client_token.pickle"

    if not os.path.exists(client_secret_path):
        exit(f"!!! client secret file is needed {client_secret_path}")

    return {
        "database": database_path,
        "client_secret": client_secret_path,
        "client_token": client_token_path,
    }
