#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Registers the recommender-domain server secret with KeyManager:
#   username: rebert.server0
#   domain:   recs.rebert.net
#
# Usage (from repo root):
#   PYTHONPATH=/path/to/HCDE563 python3 rebert/tools/register_rec_server_key.py
# Or pass the secret on the command line:
#   PYTHONPATH=... python3 rebert/tools/register_rec_server_key.py 'your-long-random-secret'
#
# Or set environment variable REBERT_RECS_SECRET (used if no argv secret).
#
import os
import sys

# Repo root must be on PYTHONPATH so `rebert` imports resolve.
from rebert.classes.data.KeyManager import KeyManager

USERNAME = "rebert.server0"
DOMAIN = "recs.rebert.net"


def main():
    secret = (
        (sys.argv[1] if len(sys.argv) > 1 else "").strip()
        or os.environ.get("REBERT_RECS_SECRET", "").strip()
    )
    if not secret:
        sys.stderr.write(
            "Missing secret. Provide it as argv[1] or set REBERT_RECS_SECRET.\n"
            "Example: PYTHONPATH=<repo-root> python3 rebert/tools/register_rec_server_key.py '...'\n"
        )
        sys.exit(1)

    km = KeyManager()
    km.createRecord(
        username=USERNAME,
        domain=DOMAIN,
        key=secret,
        description="Server secret for Rebert recommendations domain (e.g. Flask session signing)",
    )
    print(f"KeyManager: saved record for username={USERNAME!r} domain={DOMAIN!r}")


if __name__ == "__main__":
    main()
