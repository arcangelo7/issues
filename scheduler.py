#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2022 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.

from cryptography.fernet import Fernet
from getpass import getpass
import os
import sched
import subprocess
import time


def trigger_issues_manager_workflow(sc:sched.scheduler): 
    subprocess.run(["gh", "workflow", "run", "issues_manager.yaml"])
    sc.enter(5, 1, trigger_issues_manager_workflow, (sc,))


if __name__ == "__main__":
    key = getpass("Insert decryption key: ")
    ecrypted_token = "gAAAAABjJMhSFw3I89ti0N1B8nI_-ULl8fROzbRtxWJsjRRta3WzDa8UNC1Z682hL2mjUgZpP43pt-NBzmzcMwJVITBdQEtAgyE7Q_mIoxGDpnJgl1JmfnNCNTt5CyWKF5ygzyzGoRog"
    token = Fernet(key).decrypt(ecrypted_token).decode()
    os.environ["GH_TOKEN"] = token
    s = sched.scheduler(time.time, time.sleep)
    s.enter(5, 1, trigger_issues_manager_workflow, (s,))
    s.run()



    