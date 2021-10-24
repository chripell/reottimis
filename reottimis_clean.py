#!/usr/bin/env python3
"""Keep just one image per hours after some days."""

# pylint: disable=C0103
# pylint: disable=R0903
# pylint: disable=R1702
# pylint: disable=R0912

import sys
from datetime import datetime, timedelta
import os
import re
from reottimis import read_config


def main():
    """Keep just one picture per hour."""
    dry_run = True
    cfg_fname = "/etc/reolink.cfg"
    if len(sys.argv) > 1:
        cfg_fname = sys.argv[1]
    if len(sys.argv) > 2:
        dry_run = False
    cfg = read_config(cfg_fname)
    now = datetime.now()
    frm = now - timedelta(days=cfg["keep"].getint("days"))
    base = cfg["storage"]["dir"]
    mtch = re.compile(os.path.join(base, r"(\d\d\d\d)/(\d\d)/(\d\d)/(\d\d)$"))
    for root, _, _ in os.walk(base):
        m = mtch.match(root)
        # Match if we are at hour level.
        if m:
            at = datetime(year=int(m[1]), month=int(m[2]), day=int(m[3]))
            # Old enough to be deleted, keep just one per hour.
            if at < frm:
                snaps = []
                for nroot, _, files in os.walk(root):
                    snaps.extend(os.path.join(nroot, f) for f in files)
                snaps.sort()
                if len(snaps) > 0:
                    for s in snaps[1:]:
                        if dry_run:
                            print("unlink", s)
                        else:
                            os.unlink(s)
    # Delete empty directories.
    for root, _, _ in os.walk(base, topdown=False):
        if dry_run:
            print("rmdir", root)
        else:
            try:
                os.rmdir(root)
            except OSError:
                pass


if __name__ == "__main__":
    main()
