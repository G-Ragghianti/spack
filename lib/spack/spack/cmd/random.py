# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import sys
import textwrap
from itertools import zip_longest
import random as rand

import llnl.util.tty as tty
import llnl.util.tty.color as color
from llnl.util.tty.colify import colify

import spack.builder
import spack.deptypes as dt
import spack.fetch_strategy as fs
import spack.install_test
import spack.repo
import spack.spec
import spack.variant
from spack.cmd.common import arguments
from spack.package_base import preferred_version

description = "General a randomized spec for a given package"
section = "basic"
level = "short"


def setup_parser(subparser):
    arguments.add_common_arguments(subparser, ["package"])


def set_variant(variant):
    values = variant.values
    if not isinstance(variant.values, (tuple, list, spack.variant.DisjointSetsOfValues)):
        values = [variant.values]
    value = rand.choice( list(values) )
    if value is None:
        return f"{variant.name}=None"
    elif isinstance(value, bool):
        value = '+' if value else '~'
        return f"{value}{variant.name}"
    else:
        value = str(value)
        return f"{variant.name}={value}"


def is_valid_spec(spec):
    try:
        spack.cmd.parse_specs(spec, concretize=True)
    except:
        return False
    return True


def create_spec(name, recurse):
    spec = spack.spec.Spec(name)
    pkg_cls = spack.repo.PATH.get_pkg_class(spec.fullname)
    pkg = pkg_cls(spec)

    rspec = [pkg.name]
    vname = rand.choice(pkg.variant_names())
    aa,variant = pkg.variant_definitions(vname).pop()
    rspec.append( set_variant(variant) )
    cspec = spack.cmd.parse_specs(" ".join(rspec), concretize=True)
    #print(cspec[0].format("{name}{@version}{%compiler.name}{@compiler.version} {variants}"))
    print(cspec[0].long_spec)
 
    if recurse:
        for depname, extra in pkg.dependencies_by_name().items():
            if depname in spack.repo.PATH.provider_index.providers.keys():
                depname = rand.choice( spack.repo.PATH.providers_for(depname) )
            dep = create_spec(depname, False)
            rspec.append( f"^{dep}" )

    rspec.append("\n")
    return " ".join(rspec)


def random(parser, args):
    print(create_spec(args.package, False))

