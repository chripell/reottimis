#!/bin/bash

. /home/chri/python-virtual-environments/rpi/bin/activate

cd /mnt/d/chri/reottimis
exec nice /mnt/d/chri/reottimis/reottimis_daily.py 'yesterday' /mnt/d/chri/reolink.cfg



