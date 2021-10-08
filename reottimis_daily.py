#!/usr/bin/env python3

import sys
import os
from reottimis import read_config
import dateparser
from datetime import datetime, timedelta
from skyfield import almanac
from skyfield.api import wgs84, load
from configparser import ConfigParser
from pytz import timezone
from tzlocal import get_localzone
import subprocess
import re


class Videoer:

    def __init__(self, when: datetime, cfg: ConfigParser):
        self.cfg = cfg
        # Figure out local midnight.
        zone = get_localzone()
        now = when.astimezone(zone)
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        next_midnight = midnight + timedelta(days=1)
        ts = load.timescale()
        t0 = ts.from_datetime(midnight)
        t1 = ts.from_datetime(next_midnight)
        eph = load('de421.bsp')
        bluffton = wgs84.latlon(
            cfg["geo"].getfloat("lat"),
            cfg["geo"].getfloat("long"))
        f = almanac.dark_twilight_day(eph, bluffton)
        times, events = almanac.find_discrete(t0, t1, f)
        previous_e = f(t0).item()
        for t, e in zip(times, events):
            tstr = str(t.astimezone(timezone("UTC")))[:16]
            if previous_e < e:
                print(tstr, ' ', almanac.TWILIGHTS[e], 'starts')
            else:
                print(tstr, ' ', almanac.TWILIGHTS[previous_e], 'ends')
            previous_e = e
        self.frm = times[0].astimezone(timezone("UTC"))
        self.to = times[-1].astimezone(timezone("UTC"))

    def get_files(self) -> list[str]:
        base = self.cfg["storage"]["dir"]
        y = self.frm.year
        mo = self.frm.month
        d = self.frm.day
        h = self.frm.hour
        m = self.frm.minute
        h_e = self.to.hour
        m_e = self.to.minute
        all: list[str] = []
        while 60 * h + m <= 60 * h_e + m_e:
            prefix = f"{base}/{y:04d}/{mo:02d}/{d:02d}/{h:02d}/{m:02d}/"
            try:
                all.extend(
                    os.path.join(
                        prefix, i) for i in sorted(os.listdir(prefix)))
            except FileNotFoundError:
                pass
            m += 1
            if m >= 60:
                h += 1
                m = 0
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
        h_e = self.to.hour
        m_e = self.to.minute
        dest = (
            f"{self.cfg['storage']['video']}/"
            f"{y:04d}{mo:02d}{d:02d}_"
            f"{h:02d}{m:02d}_{h_e:02d}{m_e:02d}.mp4"
        )
        if os.path.isfile(dest):
            print(f"File {dest} already exists.", flush=True)
            return
        if not self.write_file("/tmp/listona"):
            return
        p = subprocess.Popen(
            "ffmpeg -r 30 -f concat -safe 0 -i /tmp/listona "
            "-vcodec libx264 -crf 23 -video_size 1280x960 "
            f"{dest}", shell=True)
        # p = subprocess.Popen(
        #     "ffmpeg -r 30 -f concat -safe 0 -i /tmp/listona "
        #     "-vcodec libx265 -crf 28 -video_size 1280x960 "
        #     f"{dest}", shell=True)
        p.wait()
        print(f"File {dest} created.", flush=True)
        os.unlink("/tmp/listona")


def generate_index(cfg: ConfigParser):
    vdir = cfg['storage']['video']
    videos = [v for v in os.listdir(vdir) if v.endswith(".mp4")]
    videos.sort(reverse=True)
    match = re.compile(
        r"(\d\d\d\d)(\d\d)(\d\d)_(\d\d)(\d\d)_(\d\d)(\d\d).mp4")
    with open(os.path.join(vdir, "index.html"), "w") as fd:
        fd.write("<html><body>\n")
        for v in videos:
            m = match.match(v)
            if not m:
                print("Invalid filename: ", v, flush=True)
                continue
            fd.write("".join((
                '<p><a href="', v, '">',
                m[1], "-", m[2], "-", m[3], " ",
                m[4], ":", m[5], "-",
                m[6], ":", m[7], "</a></p>\n")))
        fd.write("</body></html>\n")


def main():
    cfg_fname = "/etc/reolink.cfg"
    when = dateparser.parse(sys.argv[1])
    if not when:
        print("Usage: [date] [config file or /etc/reolink.cfg]")
    if len(sys.argv) > 2:
        cfg_fname = sys.argv[2]
    cfg = read_config(cfg_fname)
    videoer = Videoer(when, cfg)
    videoer.generate_video()
    generate_index(cfg)


if __name__ == "__main__":
    main()
