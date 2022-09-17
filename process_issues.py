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


from datetime import datetime
from pandas import read_csv
from typing import List, Tuple
import csv
import io
import json
import oc_idmanager
import os
import re
import requests
import subprocess
import time


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
        return True, "Thank you for your contribution! OpenCitations just processed the data you provided. The citations will soon be available on the [CROCI](https://opencitations.net/index/croci) index and metadata on OpenCitations Meta"
    except Exception:
        return False, "The data you provided could not be processed as a CSV. Please, check that the metadata CSV and the citation CSV are valid CSVs"

def answer(is_valid:bool, message:str, issue_number:str) -> None:
    if is_valid:
        label = "done"
    else:
        label = "rejected"
    subprocess.run(["gh", "issue", "edit", issue_number, "--add-label", label])
    subprocess.run(["gh", "issue", "close", issue_number, "--comment", message])

def __get_user_id(username:str) -> str:
    tentative = 3
    while tentative:
        tentative -= 1
        try:
            r = requests.get(f"https://api.github.com/users/{username}", headers={"Accept":"application/vnd.github+json"}, timeout=30)
            if r.status_code == 200:
                r.encoding = "utf-8"
                json_res = json.loads(r.text)
                return json_res.get("id")
        except requests.ReadTimeout:
            # Do nothing, just try again
            pass
        except requests.ConnectionError:
            # Sleep 5 seconds, then try again
            time.sleep(5)

def get_data_to_store(issue_title:str, issue_body:str, created_at:str, username:str) -> dict:
    split_data = issue_body.split("===###===@@@===")
    metadata = list(csv.DictReader(io.StringIO(split_data[0].strip())))
    citations = list(csv.DictReader(io.StringIO(split_data[1].strip())))
    user_id = __get_user_id(username)        
    return {
        "data": {
            "title": issue_title,
            "metadata": metadata,
            "citations": citations
        },
        "provenance": {
            "generatedAtTime": created_at,
            "wasAttributedTo": user_id
        }
    }

def __create_deposition_resource(today:str) -> str:
    r = requests.post("https://zenodo.org/api/deposit/depositions",
        params={"access_token": os.environ["ZENODO"]},
        json={"metadata": {
            "upload_type": "dataset",
            "publication_date": today,
            "title": f"OpenCitations crowdsourcing: deposits of the week before {today}",
            "creators": [{"name": "Massari, Arcangelo", "affiliation": "Research Centre for Open Scholarly Metadata, Department of Classical Philology and Italian Studies, University of Bologna, Bologna, Italy", "orcid": "0000-0002-8420-0696"}],
            "description": f"OpenCitations collects citation data and related metadata from the community through issues on the GitHub repository https://github.com/opencitations/crowdsourcing. In order to preserve long-term provenance information, such data is uploaded to Zenodo every week. This upload contains the data of deposit issues published in the week before {today}.",
            "access_right": "open",
            "license": "CC0-1.0",
            "prereserve_doi": True,
            "keywords": ["OpenCitations", "crowdsourcing", "provenance", "GitHub issues"],
            "related_identifiers": [{"identifier": "https://github.com/opencitations/crowdsourcing", "relation": "isDerivedFrom", "resource_type": "dataset"}],
            "version": "1.0.0"
        }},
        headers={"Content-Type": "application/json"})
    return r.json()["links"]["bucket"]

def __upload_data(today:str, bucket:str) -> None:
    with open("data_to_store.json", "rb") as fp:
        r = requests.put(
            "%s/%s" % (bucket, f"{today}_weekly_deposit.json"),
            data=fp,
            params={"access_token": os.environ["ZENODO"]}
        )
    print(r.json())

def deposit_on_zenodo(data_to_store:List[dict]) -> None:
    with open('data_to_store.json', 'w') as outfile:
        json.dump(data_to_store, outfile)
    today = datetime.now().strftime("%Y-%m-%d")
    bucket = __create_deposition_resource(today)
    __upload_data(today, bucket)
    # r = requests.post('https://zenodo.org/api/deposit/depositions/%s/actions/publish' % deposition_id,
    #                     params={'access_token': ACCESS_TOKEN} )
    # print(r.json())


if __name__ == "__main__":
    output = subprocess.run(
        ["gh", "issue", "list", "--state", "open", "--label", "deposit", 
        "--json", "title,body,number,author,createdAt"], 
        capture_output=True, text=True)
    issues = json.loads(output.stdout)
    data_to_store = list()
    for issue in issues:
        issue_title = issue["title"]
        issue_body = issue["body"]
        issue_number = str(issue["number"])
        created_at = issue["createdAt"]
        username = issue["author"]
        is_valid, message = validate(issue_title, issue_body)
        answer(is_valid, message, issue_number)
        data_to_store.append(get_data_to_store(issue_title, issue_body, created_at, username))
    if data_to_store:
        deposit_on_zenodo(data_to_store)