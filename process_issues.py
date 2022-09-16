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


from pandas import read_csv
from typing import Tuple
import csv
import io
import json
import oc_idmanager
import re
import subprocess


def __validate_title(title:str) -> Tuple[bool, str]:
    match = re.search(r"deposit\s+(.+?)(?:(doi|issn|isbn|pmid|pmcid|url|wikidata|wikipedia):(.+))", title)
    if not match:
        return False, 'The title of the issue was not structured correctly. Please, follow this format: deposit {domain name of journal} {doi or other supported identifier}. For example "deposit localhost:330 doi:10.1007/978-3-030-00668-6_8". The following identifiers are currently supported: doi, issn, isbn, pmid, pmcid, url, wikidata, and wikipedia'
    identifier_schema = match.group(2)
    identifier = match.group(3)
    if identifier_schema.lower() in {"doi", "orcid"}:
        id_manager = getattr(oc_idmanager, f"{identifier_schema.upper()}Manager")(use_api_service=True)
    else:
        id_manager = getattr(oc_idmanager, f"{identifier_schema.upper()}Manager")()
    is_valid = id_manager.is_valid(identifier)
    if not is_valid:
        return False, f"The identifier with literal value {identifier} specified in the issue title is not a valid {identifier_schema.upper()}"
    return True, ""

def validate(issue_title:str, issue_body:str) -> Tuple[bool, str]:
    is_valid_title, title_message = __validate_title(issue_title)
    if not is_valid_title:
        return False, title_message
    if "===###===@@@===" not in issue_body:
        return False, 'Please use the separator "===###===@@@===" to divide metadata from citations, as shown in the following guide: https://github.com/arcangelo7/issues/blob/main/README.md'
    try:
        split_data = issue_body.split("===###===@@@===")
        read_csv(io.StringIO(split_data[0].strip()))
        read_csv(io.StringIO(split_data[1].strip()))
        return True, "Thank you for your contribution! OpenCitations will process the data you provided within a week. Afterwards, citations will be available on the [CROCI](https://opencitations.net/index/croci) index and metadata on OpenCitations Meta"
    except Exception:
        return False, "The data you provided could not be processed as a CSV. Please, check that the metadata CSV and the citation CSV are valid CSVs"

def answer(is_valid:bool, message:str, issue_number:str) -> None:
    if is_valid:
        label = "done"
    else:
        label = "rejected"
    subprocess.run(["gh", "issue", "edit", issue_number, "--add-label", label])
    subprocess.run(["gh", "issue", "close", issue_number, "--comment", message])

def store(issue_title:str, issue_body:str, created_at:str, user_id:int):
    split_data = issue_body.split("===###===@@@===")
    metadata = list(csv.DictReader(io.StringIO(split_data[0].strip())))
    citations = list(csv.DictReader(io.StringIO(split_data[1].strip())))
    new_object = {
        'data': {
            'title': issue_title,
            'metadata': metadata,
            'citations': citations
        },
        'provenance': {
            'generatedAtTime': created_at,
            'wasAttributedTo': user_id
        }
    }    


if __name__ == "__main__":
    output = subprocess.run(
        ["gh", "issue", "list", "--state", "open", "--label", "deposit", 
        "--json", "title,body,number,author,createdAt"], 
        capture_output=True, text=True)
    issues = json.loads(output.stdout)
    # for issue in issues:
    #     is_valid, message = validate(issue["title"], issue["body"])
    #     answer(is_valid, message, issue["number"])