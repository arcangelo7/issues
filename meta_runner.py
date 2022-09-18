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


from sys import platform
from typing import List
import csv
import io
import json
import os
import subprocess


def dump_csv(data_to_store:List[dict], output_path:str):
    keys = data_to_store[0].keys()
    with open(output_path, "w", newline="") as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data_to_store)

def store_meta_input(issues:List[dict]) -> None:
    data_to_store = list()
    counter = 0
    for issue in issues:
        issue_body = issue["body"]
        split_data = issue_body.split("===###===@@@===")
        metadata = list(csv.DictReader(io.StringIO(split_data[0].strip())))
        if len(data_to_store) < 1000:
            data_to_store.extend(metadata)
        else:
            dump_csv(data_to_store, f"meta_input/{str(counter)}.csv")
            data_to_store = list()
    dump_csv(data_to_store, f"meta_input/{str(counter)}.csv")

def update_labels(meta_output:subprocess.CompletedProcess, issues:List[dict]) -> None:
    if meta_output.returncode == 0:
        for issue in issues:
            issue_number = str(issue['number'])
            subprocess.run(["gh", "issue", "edit", issue_number, "--remove-label", "to be processed", "--add-label", "done", "--repo", "https://github.com/arcangelo7/issues"])
    else:
        for issue in issues:
            issue_number = str(issue['number'])
            subprocess.run(["gh", "issue", "edit", issue_number, "--add-label", "oc meta error", "--repo", "https://github.com/arcangelo7/issues"])                    


if __name__ == "__main__":
    output = subprocess.run(
        ["gh", "issue", "list", "--state", "closed", "--label", "to be processed", "--json", "body,number", "--repo", "https://github.com/arcangelo7/issues"], 
        capture_output=True, text=True)
    issues = json.loads(output.stdout)
    is_unix = platform in {"linux", "linux2", "darwin"}
    call_python = "python3" if is_unix else "python"
    store_meta_input(issues)
    os.chdir("oc_meta/")
    subprocess.run(["poetry", "shell"])
    meta_output = subprocess.run([call_python, "-m", "oc_meta.run.meta_process", "-c", "../meta_config.yaml"], capture_output=True, text=True)
    update_labels(meta_output, issues)
    for f in os.listdir("../meta_input"):
        os.remove(os.path.join("..", "meta_input", f))