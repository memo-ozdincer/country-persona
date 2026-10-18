"""Back up a bounded checkpoint in the existing private GitHub repository.

Never overwrites/deletes an asset. Credentials come from Git's credential helper
and are used only in HTTPS headers, never printed or placed in arguments.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com/repos/memo-ozdincer/country-persona"
SCRATCH = Path("/mfs1/u/memo/country-persona-research")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--assets", type=Path, required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--commit", required=True)
    p.add_argument("--body-file", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or not a.tag.startswith("scenario-role-checkpoint-"):
        raise ValueError("Fresh receipt and a scoped checkpoint tag required")
    if len(a.commit) != 40 or any(c not in "0123456789abcdef" for c in a.commit):
        raise ValueError("Exact committed source revision required")
    spec = json.loads(a.assets.read_text())
    for asset in spec["assets"]:
        path = Path(asset["path"]).resolve()
        if not path.is_relative_to(SCRATCH) or path.stat().st_size > 512 * 1024**2:
            raise ValueError("Asset outside scratch or beyond bounded checkpoint size")
        if path.stat().st_size != asset["bytes"] or hashlib.sha256(path.read_bytes()).hexdigest() != asset["sha256"]:
            raise ValueError("Asset bytes changed")
    credential = subprocess.run(["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n", text=True, capture_output=True, check=True)
    values = dict(line.split("=", 1) for line in credential.stdout.splitlines() if "=" in line)
    encoded = base64.b64encode((values["username"] + ":" + values["password"]).encode()).decode()
    headers = {"Authorization": "Basic " + encoded, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    def request(method, url, data=None, content_type="application/json"):
        extra = {**headers, "Content-Type": content_type}
        raw = json.dumps(data).encode() if isinstance(data, dict) else data
        with urllib.request.urlopen(urllib.request.Request(url, data=raw, headers=extra, method=method), timeout=120) as response:
            return json.load(response)
    repo = request("GET", API)
    if not repo["private"]:
        raise ValueError("Destination must remain private")
    commit = request("GET", API + "/commits/" + a.commit)
    if commit["sha"] != a.commit:
        raise ValueError("Push source commit before publishing its checkpoint")
    try:
        release = request("GET", API + "/releases/tags/" + urllib.parse.quote(a.tag, safe=""))
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        release = request("POST", API + "/releases", dict(tag_name=a.tag, target_commitish=a.commit,
            name="Scenario/delegation checkpoint — 18 October 2026", body=a.body_file.read_text(), draft=False, prerelease=False))
    tag = request("GET", API + "/git/ref/tags/" + urllib.parse.quote(a.tag, safe=""))
    if tag["object"]["type"] != "commit" or tag["object"]["sha"] != a.commit:
        raise ValueError("Existing tag points elsewhere; preserve it")
    url = release["upload_url"].split("{")[0]
    if not url.startswith("https://uploads.github.com/repos/memo-ozdincer/country-persona/releases/"):
        raise ValueError("Unexpected upload destination")
    existing = {x["name"]: x for x in release["assets"]}
    verified = []
    for asset in spec["assets"]:
        path = Path(asset["path"])
        result = existing.get(path.name)
        if result is None:
            result = request("POST", url + "?name=" + urllib.parse.quote(path.name), path.read_bytes(), "application/octet-stream")
        if result["size"] != asset["bytes"] or result.get("digest") != "sha256:" + asset["sha256"]:
            raise ValueError("Remote asset differs or digest is unavailable; do not overwrite")
        verified.append(dict(name=path.name, bytes=result["size"], sha256=asset["sha256"], asset_id=result["id"]))
    receipt = dict(status="private_checkpoint_assets_verified", repository_private=True,
        source_commit=a.commit, release=release["html_url"], assets=verified,
        limitation="Local bytes hashed; live GitHub sizes and SHA256 digests match. No redundant full snapshot or repeated remote download.")
    a.output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "release": receipt["release"], "assets": len(verified)}))


if __name__ == "__main__":
    main()
