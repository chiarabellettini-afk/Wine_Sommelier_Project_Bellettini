"""Persistence of user data (favorites and custom wines) in a JSON file."""

import json
import os

USER_INFO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_info.json"
)
DEFAULT_INFO = {"Custom_wine": [], "Favorites": []}


def save_user_info(user_info):
    """Write the user info dictionary to the JSON file.

    Args:
        user_info (dict): Dictionary with "Custom_wine" and "Favorites" keys.
    """
    with open(USER_INFO_PATH, "w") as f:
        json.dump(user_info, f, indent=4)


def load_user_info():
    """Read the user info file, creating it if it does not exist.

    Returns:
        dict: The user info. If the file is corrupted, the default
        structure is returned (the file itself is not overwritten).
    """
    if not os.path.exists(USER_INFO_PATH):
        save_user_info(dict(DEFAULT_INFO, Custom_wine=[], Favorites=[]))
    try:
        with open(USER_INFO_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {"Custom_wine": [], "Favorites": []}


def toggle_favorite(wine_id):
    """Add the wine to the favorites, or remove it if already there.

    Args:
        wine_id (int): ID of the wine to toggle.
    """
    info = load_user_info()
    favs = info.setdefault("Favorites", [])
    if wine_id in favs:
        favs.remove(wine_id)
    else:
        favs.append(wine_id)
    save_user_info(info)


def custom_wine_names(user_info):
    """Return the names of the custom wines.

    Args:
        user_info (dict): The user info dictionary.

    Returns:
        list[str]: Names of all custom wines (empty if none).
    """
    return [w["WineName"] for w in user_info.get("Custom_wine", []) if "WineName" in w]