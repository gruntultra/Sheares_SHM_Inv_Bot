#! /bin/bash
until python3.6 shmbot.py; do
    echo "'shmbot.py' crashed with exit code $?. Restarting..." >&2
    sleep 1
done
