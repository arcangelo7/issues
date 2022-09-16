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
import os
import re
import subprocess


if isinstance(os.environ.get("ISSUE_CONTEXT"), dict):
    ISSUE_CONTEXT = json.loads(os.environ.get("ISSUE_CONTEXT"))
    BODY:str = ISSUE_CONTEXT["body"]
    TITLE = ISSUE_CONTEXT["title"]
    ISSUE_NUMBER = ISSUE_CONTEXT["number"]
    CREATED_AT = ISSUE_CONTEXT["created_at"]
    USER_ID = ISSUE_CONTEXT["user"]["id"]
    TOKEN = os.environ.get("GITHUB_TOKEN")
else:
    ISSUE_CONTEXT = dict()
    BODY = str()
    TITLE = str()
    ISSUE_NUMBER = str()
    CREATED_AT = str()
    USER_ID = int()
    TOKEN = str()

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

def validate(issue_title:str=TITLE, issue_body:str=BODY) -> Tuple[bool, str]:
    is_valid_title, title_message = __validate_title(issue_title)
    if not is_valid_title:
        return False, title_message
    if "===###===@@@===" not in issue_body:
        return False, 'Please use the separator "===###===@@@===" to divide metadata from citations, as shown in the following guide: https://github.com/arcangelo7/issues/blob/main/README.md'
    try:
        split_data = issue_body.split("===###===@@@===")
        read_csv(io.StringIO(split_data[0].strip()))
        read_csv(io.StringIO(split_data[1].strip()))
        return True, "Thank you for your contribution! OpenCitations will process the data you provided within a week. Afterwards, citations will be available through the [CROCI](https://opencitations.net/index/croci) index and metadata through OpenCitations Meta"
    except Exception as e:
        return False, "The data you provided could not be processed as a CSV. Please, check that the metadata CSV and the citation CSV are valid CSVs"

def answer(is_valid:bool, message:str) -> None:
    if is_valid:
        label = "Done"
    else:
        label = "Rejected"
    subprocess.run(["gh", "auth", "login", "--with-token", TOKEN])
    subprocess.run(["gh", "issue", "edit", ISSUE_NUMBER, "--add-label", label])
    subprocess.run(["gh", "issue", "close", ISSUE_NUMBER, "--comment", message])

def store():
    split_data = BODY.split("===###===@@@===")
    metadata = list(csv.DictReader(io.StringIO(split_data[0].strip())))
    citations = list(csv.DictReader(io.StringIO(split_data[1].strip())))
    new_object = {
        'data': {
            'title': TITLE,
            'metadata': metadata,
            'citations': citations
        },
        'provenance': {
            'generatedAtTime': CREATED_AT,
            'wasAttributedTo': USER_ID
        }
    }

if __name__ == '__main':
    is_valid, message = validate()
    answer(is_valid, message)
    store()