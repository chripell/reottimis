import os
from configparser import ConfigParser


def read_config(props_path: str) -> ConfigParser:
    """Reads in a properties file into variables.

    # /etc/reolink.cfg
        [camera]
        ip={ip_address}
        username={username}
        password={password}
        [storage]
        dir={where to save the images}
        link={link to the latest image}
        every={seconds between pictures}
        video={where to put videos}
        [draw]
        font={ttf file for the font to use}
        size={font size, for example 24}
        [geo]
        lat=
        long=
        alt=
        [keep]
        days=
    """
    config = ConfigParser()
    assert os.path.exists(props_path), f"Path does not exist: {props_path}"
    config.read(props_path)
    return config


def is_space_available(directory_path, min_gb=1):
    """
    Checks if there is at least min_gb of disk space available
    on the filesystem containing the given directory.

    :param directory_path: Path to a directory on the target filesystem.
    :param min_gb: The threshold in Gigabytes.
    :return: True if space is sufficient, False otherwise.
    """
    try:
        # Get filesystem statistics
        st = os.statvfs(directory_path)

        # f_frsize: Fundamental file system block size
        # f_bavail: Free blocks available to non-superusers
        free_bytes = st.f_bavail * st.f_frsize

        # Calculate threshold: 1 GB = 1024^3 bytes
        threshold_bytes = min_gb * (1024 ** 3)

        return free_bytes >= threshold_bytes

    except FileNotFoundError:
        print(f"Error: The directory '{directory_path}' does not exist.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
