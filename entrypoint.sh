#!/bin/bash

LINKS_PATH=/opt/reddit-depression/stats
cd $LINKS_PATH

case "$1" in
    stats)
        LINK=stats.py
        ;;

    *)
        echo "Usage: [stats] [ARGS]"
        exit 1
esac

shift
python $LINK "$@"
