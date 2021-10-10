#!/usr/bin/env python3

import sys
import os
from reottimis import read_config
import dateparser
from datetime import datetime, timedelta
from configparser import ConfigParser
import subprocess
import re
from pytz import UTC
from pathlib import Path


class Videoer:

    def __init__(self, frm_: datetime, to_: datetime, cfg: ConfigParser):
        self.cfg = cfg
        self.frm = frm_.replace(tzinfo=UTC)
        self.to = to_.replace(tzinfo=UTC)

    def get_files(self) -> list[str]:
        base = self.cfg["storage"]["dir"]
        cur = self.frm
        all: list[str] = []
        while cur <= self.to:
            y = cur.year
            mo = cur.month
            d = cur.day
            h = cur.hour
            m = cur.minute
            prefix = f"{base}/{y:04d}/{mo:02d}/{d:02d}/{h:02d}/{m:02d}/"
            try:
                all.extend(
                    os.path.join(
                        prefix, i) for i in sorted(os.listdir(prefix)))
            except FileNotFoundError:
                pass
            cur += timedelta(minutes=1)
        return all

    def write_file(self, dest: str) -> bool:
        images = self.get_files()
        if not images:
            print("No images found")
            return False
        with open(dest, "w", encoding='utf-8') as fd:
            for n in images:
                fd.write(f"file '{n}'\n")
        return True

    def generate_video(self):
        y = self.frm.year
        mo = self.frm.month
        d = self.frm.day
        h = self.frm.hour
        m = self.frm.minute
        ey = self.to.year
        emo = self.to.month
        ed = self.to.day
        eh = self.to.hour
        em = self.to.minute
        dest = (
            f"{self.cfg['storage']['video']}/"
            f"{y:04d}{mo:02d}{d:02d}{h:02d}{m:02d}_"
            f"{ey:04d}{emo:02d}{ed:02d}{eh:02d}{em:02d}.mp4"
        )
        if os.path.isfile(dest):
            print(f"File {dest} already exists.", flush=True)
            return
        if not self.write_file("/tmp/listona1"):
            return
        p = subprocess.Popen(
            "ffmpeg -r 30 -f concat -safe 0 -i /tmp/listona1 "
            "-vcodec libx264 -crf 23 -video_size 1280x960 "
            f"{dest}", shell=True)
        # p = subprocess.Popen(
        #     "ffmpeg -r 30 -f concat -safe 0 -i /tmp/listona1 "
        #     "-vcodec libx265 -crf 28 -video_size 1280x960 "
        #     f"{dest}", shell=True)
        p.wait()
        print(f"File {dest} created.", flush=True)
        os.unlink("/tmp/listona1")


def generate_index(cfg: ConfigParser):
    vdir = cfg['storage']['video']
    videos = [v for v in os.listdir(vdir) if v.endswith(".mp4")]
    videos.sort(reverse=True)
    match = re.compile(
        r"(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)_"
        r"(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d).mp4")
    with open(os.path.join(vdir, "manual.html"), "w") as fd:
        fd.write("<html><body>\n")
        for v in videos:
            m = match.match(v)
            if not m:
                print("Invalid filename: ", v, flush=True)
                continue
            fd.write("".join((
                '<p><a href="', v, '">',
                m[1], "-", m[2], "-", m[3], " ", m[4], ":", m[5], "-",
                m[6], "-", m[7], "-", m[8], " ", m[9], ":", m[10], "-",
                "</a></p>\n")))
        fd.write("</body></html>\n")


def main():
    cfg_fname = "/etc/reolink.cfg"
    frm = dateparser.parse(sys.argv[1])
    to = dateparser.parse(sys.argv[2])
    if not frm or not to:
        print("Usage: [date from] [date to] [config file or /etc/reolink.cfg]")
    if len(sys.argv) > 3:
        cfg_fname = sys.argv[3]
    cfg = read_config(cfg_fname)
    videoer = Videoer(frm, to, cfg)
    videoer.generate_video()
    generate_index(cfg)


if __name__ == "__main__":
    main()
