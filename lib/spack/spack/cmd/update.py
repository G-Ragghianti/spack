# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from __future__ import print_function

import textwrap
from six.moves import zip_longest

import llnl.util.tty.color as color
from llnl.util.tty.colify import colify

import spack.cmd.common.arguments as arguments
import spack.repo
import spack.spec
import spack.fetch_strategy as fs
from spack.version import Version, VersionList
from spack.stage import Stage
import hashlib
import tempfile
import shutil
import os
import re


description = 'update a package'
section = 'packaging'
level = 'short'


def setup_parser(subparser):
    arguments.add_common_arguments(subparser, ['package'])


def validate_version(package, version):
    print("Validating version", version, "of", package.name)


def add_version(package, version, checksum):
    print("Adding version", version, "to", package.name)
    pkg_filename = spack.repo.path.filename_for_package_name(package.name)
    with tempfile.NamedTemporaryFile() as tmp, open(pkg_filename, 'r') as f:
        tmp_fh = open(tmp.name, 'w')
        done = False
        for line in f.readlines():
            if re.search("^\s+version\(", line) and not done:
                tmp_fh.write("    version('"+version.string+"', sha256='"+checksum+"')\n")
                done = True
            tmp_fh.write(line)
        tmp_fh.close()
        f.close()
        shutil.copy(tmp.name, pkg_filename)

def update(parser, args):
    pkg = spack.repo.get(args.package)
    urls = []
    if pkg.versions and pkg.has_code:
        max_version = VersionList(pkg.versions).highest()
        for v in pkg.versions:
            fs_url = fs.for_package_version(pkg, v)
            if re.search("^http", fs_url.url):
                urls.append(fs_url.url)
        url_dict = spack.util.web.find_versions_of_archive(urls, list_url=pkg.list_url)
        newer_version = None
        for v in url_dict:
            if re.search("(rc\d+)|(alpha)|(beta)", v.string): continue
            if v > max_version and v > newer_version:
                newer_version = v                
        if newer_version:
            print("Found new version of", pkg.name, ":", newer_version)
            validate_version(pkg, newer_version)
            checksum = None
            with Stage(url_dict[newer_version]) as stage:
                stage.fetch()
                checksum = spack.util.crypto.checksum(hashlib.sha256, stage.archive_file)
            add_version(pkg, newer_version, checksum)

