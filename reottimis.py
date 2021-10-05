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
        [draw]
        font={ttf file for the font to use}
        size={font size, for example 24}
    """
    config = ConfigParser()
    assert os.path.exists(props_path), f"Path does not exist: {props_path}"
    config.read(props_path)
    return config
