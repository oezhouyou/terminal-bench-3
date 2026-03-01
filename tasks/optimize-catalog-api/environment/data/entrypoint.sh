#!/bin/bash
service postgresql start
sleep 2
exec "$@"
