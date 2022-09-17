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
            "related_identifiers": [{"isDerivedFrom": "https://github.com/opencitations/crowdsourcing"}],
            "version": "1.0.0"
        }},
        headers={"Content-Type": "application/json"})
    print(r.json())
    return r.json()["links"]["bucket"]

def __upload_data(today:str, bucket:str) -> None:
    with open("data_to_store.json", "rb") as fp:
        r = requests.put(
            "%s/%s" % (bucket, f"{today}_weekly_deposit"),
            data=fp,
            params={"access_token": os.environ["ZENODO"]}
        )
    r.json()

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
    print(os.environ)
    for issue in issues:
        issue_title = issue["title"]
        issue_body = issue["body"]
        issue_number = str(issue["number"])
        created_at = issue["createdAt"]
        username = issue["author"]
        is_valid, message = validate(issue_title, issue_body)
        answer(is_valid, message, issue_number)
        data_to_store.append(get_data_to_store(issue_title, issue_body, created_at, username))
    deposit_on_zenodo(data_to_store)

environ({'SELENIUM_JAR_PATH': '/usr/share/java/selenium-server.jar', 'GOROOT_1_17_X64': '/opt/hostedtoolcache/go/1.17.13/x64', 'CONDA': '/usr/share/miniconda', 'GITHUB_WORKSPACE': '/home/runner/work/issues/issues', 'JAVA_HOME_11_X64': '/usr/lib/jvm/temurin-11-jdk-amd64', 'PKG_CONFIG_PATH': '/opt/hostedtoolcache/Python/3.10.7/x64/lib/pkgconfig', 'GITHUB_PATH': '/home/runner/work/_temp/_runner_file_commands/add_path_d1696ddc-bb31-4274-ba90-64c2315ec05f', 'GITHUB_ACTION': '__run_2', 'JAVA_HOME': '/usr/lib/jvm/temurin-11-jdk-amd64', 'GITHUB_RUN_NUMBER': '9327', 'RUNNER_NAME': 'Hosted Agent', 'GRADLE_HOME': '/usr/share/gradle-7.5.1', 'XDG_CONFIG_HOME': '/home/runner/.config', 'Python_ROOT_DIR': '/opt/hostedtoolcache/Python/3.10.7/x64', 'DOTNET_SKIP_FIRST_TIME_EXPERIENCE': '1', 'ANT_HOME': '/usr/share/ant', 'JAVA_HOME_8_X64': '/usr/lib/jvm/temurin-8-jdk-amd64', 'GITHUB_TRIGGERING_ACTOR': 'arcangelo7', 'HOMEBREW_PREFIX': '/home/linuxbrew/.linuxbrew', 'pythonLocation': '/opt/hostedtoolcache/Python/3.10.7/x64', 'GITHUB_REF_TYPE': 'branch', 'HOMEBREW_CLEANUP_PERIODIC_FULL_DAYS': '3650', 'ANDROID_NDK': '/usr/local/lib/android/sdk/ndk/25.1.8937393', 'BOOTSTRAP_HASKELL_NONINTERACTIVE': '1', 'PWD': '/home/runner/work/issues/issues', 'PIPX_BIN_DIR': '/opt/pipx_bin', 'DEPLOYMENT_BASEPATH': '/opt/runner', 'GITHUB_ACTIONS': 'true', 'ANDROID_NDK_LATEST_HOME': '/usr/local/lib/android/sdk/ndk/25.1.8937393', 'GITHUB_SHA': '310da6f89c5e7b116a875281d634f1ff7e6d4e04', 'POWERSHELL_DISTRIBUTION_CHANNEL': 'GitHub-Actions-ubuntu20', 'DOTNET_MULTILEVEL_LOOKUP': '0', 'GITHUB_REF': 'refs/heads/main', 'RUNNER_OS': 'Linux', 'GITHUB_REF_PROTECTED': 'false', 'HOME': '/home/runner', 'GITHUB_API_URL': 'https://api.github.com', 'LANG': 'C.UTF-8', 'GITHUB_TOKEN': '***', 'RUNNER_TRACKING_ID': 'github_8547c8bf-f03e-4715-a2df-518d1f8d65a1', 'RUNNER_ARCH': 'X64', 'ISSUE_CONTEXT': 'null', 'RUNNER_TEMP': '/home/runner/work/_temp', 'EDGEWEBDRIVER': '/usr/local/share/edge_driver', 'GITHUB_ENV': '/home/runner/work/_temp/_runner_file_commands/set_env_d1696ddc-bb31-4274-ba90-64c2315ec05f', 'GITHUB_EVENT_PATH': '/home/runner/work/_temp/_github_workflow/event.json', 'INVOCATION_ID': '7fcd5f2bc7884b78983ff0206cd78c8f', 'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_RUN_ID': '3072979822', 'JAVA_HOME_17_X64': '/usr/lib/jvm/temurin-17-jdk-amd64', 'ANDROID_NDK_HOME': '/usr/local/lib/android/sdk/ndk/25.1.8937393', 'GITHUB_STEP_SUMMARY': '/home/runner/work/_temp/_runner_file_commands/step_summary_d1696ddc-bb31-4274-ba90-64c2315ec05f', 'HOMEBREW_NO_AUTO_UPDATE': '1', 'GITHUB_ACTOR': 'arcangelo7', 'NVM_DIR': '/home/runner/.nvm', 'SGX_AESM_ADDR': '1', 'GITHUB_RUN_ATTEMPT': '1', 'ANDROID_HOME': '/usr/local/lib/android/sdk', 'GITHUB_GRAPHQL_URL': 'https://api.github.com/graphql', 'ACCEPT_EULA': 'Y', 'RUNNER_USER': 'runner', 'USER': 'runner', 'GITHUB_SERVER_URL': 'https://github.com', 'HOMEBREW_CELLAR': '/home/linuxbrew/.linuxbrew/Cellar', 'PIPX_HOME': '/opt/pipx', 'GECKOWEBDRIVER': '/usr/local/share/gecko_driver', 'CHROMEWEBDRIVER': '/usr/local/share/chrome_driver', 'SHLVL': '1', 'ANDROID_SDK_ROOT': '/usr/local/lib/android/sdk', 'VCPKG_INSTALLATION_ROOT': '/usr/local/share/vcpkg', 'HOMEBREW_REPOSITORY': '/home/linuxbrew/.linuxbrew/Homebrew', 'RUNNER_TOOL_CACHE': '/opt/hostedtoolcache', 'ImageVersion': '20220905.1', 'Python3_ROOT_DIR': '/opt/hostedtoolcache/Python/3.10.7/x64', 'DOTNET_NOLOGO': '1', 'GITHUB_REF_NAME': 'main', 'GRAALVM_11_ROOT': '/usr/local/graalvm/graalvm-ce-java11-22.2.0', 'GITHUB_JOB': 'Validate', 'LD_LIBRARY_PATH': '/opt/hostedtoolcache/Python/3.10.7/x64/lib', 'XDG_RUNTIME_DIR': '/run/user/1001', 'AZURE_EXTENSION_DIR': '/opt/az/azcliextensions', 'PERFLOG_LOCATION_SETTING': 'RUNNER_PERFLOG', 'GITHUB_REPOSITORY': 'arcangelo7/issues', 'Python2_ROOT_DIR': '/opt/hostedtoolcache/Python/3.10.7/x64', 'CHROME_BIN': '/usr/bin/google-chrome', 'ANDROID_NDK_ROOT': '/usr/local/lib/android/sdk/ndk/25.1.8937393', 'GOROOT_1_18_X64': '/opt/hostedtoolcache/go/1.18.5/x64', 'GITHUB_RETENTION_DAYS': '90', 'JOURNAL_STREAM': '8:21937', 'RUNNER_WORKSPACE': '/home/runner/work/issues', 'LEIN_HOME': '/usr/local/lib/lein', 'LEIN_JAR': '/usr/local/lib/lein/self-installs/leiningen-2.9.10-standalone.jar', 'GITHUB_ACTION_REPOSITORY': '', 'PATH': '/opt/hostedtoolcache/Python/3.10.7/x64/bin:/opt/hostedtoolcache/Python/3.10.7/x64:/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:/home/runner/.local/bin:/opt/pipx_bin:/home/runner/.cargo/bin:/home/runner/.config/composer/vendor/bin:/usr/local/.ghcup/bin:/home/runner/.dotnet/tools:/snap/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin', 'RUNNER_PERFLOG': '/home/runner/perflog', 'GITHUB_BASE_REF': '', 'CI': 'true', 'SWIFT_PATH': '/usr/share/swift/usr/bin', 'ImageOS': 'ubuntu20', 'GITHUB_REPOSITORY_OWNER': 'arcangelo7', 'GITHUB_HEAD_REF': '', 'GITHUB_ACTION_REF': '', 'GOROOT_1_19_X64': '/opt/hostedtoolcache/go/1.19.0/x64', 'GITHUB_WORKFLOW': 'Issues manager', 'DEBIAN_FRONTEND': 'noninteractive', 'AGENT_TOOLSDIRECTORY': '/opt/hostedtoolcache', '_': '/opt/hostedtoolcache/Python/3.10.7/x64/bin/python3'})