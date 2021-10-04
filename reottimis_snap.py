#!/usr/bin/env python3

import os
import sys
from configparser import ConfigParser
from reolinkapi import Camera
from datetime import datetime
import pathlib
import time
from shutil import move
from PIL import ImageFont, ImageDraw
import urllib3
import requests


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


class Snapper:

    def __init__(self, camera: Camera, cfg: ConfigParser):
        self.camera = camera
        self.cfg = cfg
        self.font = ImageFont.truetype(cfg["draw"]["font"],
                                       cfg["draw"].getint("size"))

    def get_image_path(self, tstamp: float) -> str:
        now = datetime.fromtimestamp(tstamp)
        path = os.path.join(
            self.cfg["storage"]["dir"],
            now.strftime("%Y/%m/%d/%H/%M"))
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        fname = now.strftime("%S") + "_" + str(int(now.timestamp()))
        return os.path.join(path, fname) + ".jpg"

    def save_image(self, tstamp: float) -> str:
        dest_fname = self.get_image_path(tstamp)
        im = self.camera.get_snap()
        if not im:
            print("Failed to get image from reolink camera", flush=True)
            return "FAILED"
        im.save(dest_fname)
        tmp = self.cfg["storage"]["link"] + "_temp.jpg"
        draw = ImageDraw.Draw(im)
        now = datetime.fromtimestamp(tstamp)
        txt = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        origin = (0, 0)
        dims = self.font.getsize(txt)
        draw.rectangle((origin, (dims[0] + 1, dims[1] + 1)),
                       outline='black', fill='black')
        draw.text(origin, txt, (255, 255, 255), font=self.font)
        im.save(tmp)
        move(tmp, self.cfg["storage"]["link"])
        return dest_fname

    def snap(self):
        next_t = int(time.time())
        while True:
            now = time.time()
            if now < next_t:
                time.sleep(0.5)
                continue
            next_t = int(time.time()) + self.cfg["storage"].getint("every")
            dest_fname = self.save_image(now)
            print(f"Saved {dest_fname}", flush=True)


def main():
    cfg_fname = "/etc/reolink.cfg"
    if len(sys.argv) > 1:
        cfg_fname = sys.argv[1]
    cfg = read_config(cfg_fname)
    cam = None
    while not cam:
        try:
            cam = Camera(
                cfg["camera"]["ip"],
                cfg["camera"]["username"],
                cfg["camera"]["password"])
            snapper = Snapper(cam, cfg)
            snapper.snap()
        except (urllib3.exceptions.HTTPError,
                requests.exceptions.ConnectionError) as e:
            print("Error snapping: ", e, flush=True)
            cam = None
            time.sleep(cfg["storage"].getint("every"))


if __name__ == "__main__":
    main()
