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
            all.extend(
                os.path.join(prefix, i) for i in sorted(os.listdir(prefix)))
            m += 1
            if m >= 60:
                h += 1
                m = 0
        return all

    def write_file(self, dest: str):
        with open(dest, "w", encoding='utf-8') as fd:
            for n in self.get_files():
                fd.write(f"file '{n}'\n")

```
ffmpeg -r 30 -f concat -safe 0 -i /tmp/listona -vcodec libx265 -crf 28 -video_size 1280x960 test.mp4
```


def main():
    cfg_fname = "/etc/reolink.cfg"
    when = dateparser.parse(sys.argv[1])
    if not when:
        print("Usage: [date] [config file or /etc/reolink.cfg]")
    if len(sys.argv) > 2:
        cfg_fname = sys.argv[2]
    cfg = read_config(cfg_fname)
    videoer = Videoer(when, cfg)
    videoer.write_file("/tmp/listona")


if __name__ == "__main__":
    main()
