#!/usr/bin/env bash

export PYTHONPATH=`pwd`

while true; do

    echo -ne "\033c"
    py.test --color yes -x -v
    #python test.py
    #python get_definitions.py
    echo "exit code: $?"

    inotifywait -rq -e close_write,moved_to,create *.py tests zigpy_cc

done