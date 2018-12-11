from __future__ import absolute_import

import argparse
import gzip
import json
import io
import os
from datetime import datetime, timedelta

from six.moves.urllib.request import urlopen

from .vcs import Git

from . import log

here = os.path.dirname(__file__)

wpt_root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))
logger = log.get_logger()


def abs_path(path):
    return os.path.abspath(os.path.expanduser(path))


def should_download(manifest_path, rebuild_time=timedelta(days=5)):
    if not os.path.exists(manifest_path):
        return True
    mtime = datetime.fromtimestamp(os.path.getmtime(manifest_path))
    if mtime < datetime.now() - rebuild_time:
        return True
    logger.info("Skipping manifest download because existing file is recent")
    return False


def merge_pr_tags(repo_root, max_count=50):
    git = Git.get_func(repo_root)
    tags = []
    for line in git("log", "--format=%D", "--max-count=%s" % max_count).split("\n"):
        for ref in line.split(", "):
            if ref.startswith("tag: merge_pr_"):
                tags.append(ref[5:])
    return tags


def github_url(tags):
    for tag in tags:
        url = "https://api.github.com/repos/web-platform-tests/wpt/releases/tags/%s" % tag
        try:
            resp = urlopen(url)
        except Exception:
            logger.warning("Fetching %s failed" % url)
            continue

        if resp.code != 200:
            logger.warning("Fetching %s failed; got HTTP status %d" % (url, resp.code))
            continue

        try:
            release = json.load(resp.fp)
        except ValueError:
            logger.warning("Response was not valid JSON")
            return None

        for item in release["assets"]:
            # Accept both ways of naming the manfest asset, even though
            # there's no longer a reason to include the commit sha.
            if item["name"].startswith("MANIFEST-") and item["name"].endswith(".json.gz"):
                return item["browser_download_url"]
            elif item["name"] == "MANIFEST.json.gz":
                return item["browser_download_url"]

    return None


def download_manifest(manifest_path, tags_func, url_func, force=False):
    if not force and not should_download(manifest_path):
        return False

    tags = tags_func()

    url = url_func(tags)
    if not url:
        logger.warning("No generated manifest found")
        return False

    logger.info("Downloading manifest from %s" % url)
    try:
        resp = urlopen(url)
    except Exception:
        logger.warning("Downloading pregenerated manifest failed")
        return False

    if resp.code != 200:
        logger.warning("Downloading pregenerated manifest failed; got HTTP status %d" %
                       resp.code)
        return False

    gzf = gzip.GzipFile(fileobj=io.BytesIO(resp.read()))

    try:
        decompressed = gzf.read()
    except IOError:
        logger.warning("Failed to decompress downloaded file")
        return False

    try:
        with open(manifest_path, "w") as f:
            f.write(decompressed)
    except Exception:
        logger.warning("Failed to write manifest")
        return False
    logger.info("Manifest downloaded")
    return True


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--path", type=abs_path, help="Path to manifest file.")
    parser.add_argument(
        "--tests-root", type=abs_path, default=wpt_root, help="Path to root of tests.")
    parser.add_argument(
        "--force", action="store_true",
        help="Always download, even if the existing manifest is recent")
    return parser


def download_from_github(path, tests_root, force=False):
    return download_manifest(path, lambda: merge_pr_tags(tests_root), github_url,
                             force=force)


def run(**kwargs):
    if kwargs["path"] is None:
        path = os.path.join(kwargs["tests_root"], "MANIFEST.json")
    else:
        path = kwargs["path"]
    success = download_from_github(path, kwargs["tests_root"], kwargs["force"])
    return 0 if success else 1
