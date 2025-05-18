#!/usr/bin/env bash
# Overwrites local sqlite database with production one.


set -o errexit
set -o nounset
set -o pipefail

scp root@schoolmemories.01z.io:/var/www/schoolmemories/db.sqlite3 .
