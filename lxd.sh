#!/bin/sh
# LXD daemon wrapper 
# regardless --logfile option lxd prints some messages on stderr at start, they
# are printed in log file as well, so just ignore stderr here 

if [ "$1" != "daemon" ]; then
    echo >&2 "This is a wrapper script for lxd, executed by service scripts."
    echo >&2 "Use /usr/sbin/lxd to run lxd manually."
    exit 1
fi

exec 1>>/dev/null
exec 2>&1
exec /usr/sbin/lxd "$@"
