import importlib
import sys
from argparse import ArgumentParser
from pathlib import Path
import inspect

from RelativeAddonsSystem import AddonMeta

parser = ArgumentParser(
    usage="""
Addon creation tool

Parameters:
    --name={name}, -n {name} - Required. Specify addons name
    --description={description}, --desc={description}, -d {description} - Required. Specify addons description
    --version={version}, -v {version} - Required. Specify addons version
    --author={author}, -a {author} - Required. Specify addons author
    --status={status}, -s {status} - Optional. Specify addons status
    --path={path}, -p {path} - Optional. Specify addons path
    --prompt - Optional. Prompt all values"""
)

parser.add_argument(
    "--description", "-d", "--desc"
)
parser.add_argument(
    "--version", "-v"
)

parser.add_argument(
    "--author", "-a"
)

parser.add_argument(
    "--name", "-n"
)

parser.add_argument(
    "--status", "-s"
)

parser.add_argument(
    "--path", "-p"
)

parser.add_argument(
    "--prompt", const=True, nargs="?"
)

if len(sys.argv) < 2:
    parser.print_usage()
    exit()

namespace = parser.parse_args(sys.argv[1:])

name = namespace.name
author = namespace.author
description = namespace.description
version = namespace.version


def required_input(prompt: str = ""):
    while len(value := input(prompt)) == 0:
        pass

    return value


if namespace.prompt:
    name = required_input("(REQUIRED) Type the name of the addon > ")
    author = required_input("(REQUIRED) Type the author of the addon > ")
    description = input("(OPTIONAL) Type the description of the addon > ")
    version = input("(OPTIONAL) Type the version of the addon > ")
    path = input("(OPTIONAL) Type the path to the addon >")

    if len(path) == 0:
        path = None

    if len(version) == 0:
        version = "1.0.0"

if (
    not name or not author or not description or not version
):
    parser.print_usage()
    exit()

status = namespace.status
if not status:
    status = "disabled"

path = namespace.path
if not path:
    path = Path("./addons/{addon_name}".format(addon_name=name))
else:
    path = Path(path)

if path.exists():
    print("This path already exist")
    exit()

path.mkdir()

with open(path / "addon.json", "w", encoding="utf8") as f:
    f.write("{}")

meta = AddonMeta(path / "addon.json")

meta.set("name", name)
meta.set("version", version)
meta.set("description", description)
meta.set("author", author)
meta.set("status", status)

meta.save()

template_module = importlib.import_module("addon template")

source = inspect.getsource(template_module)

doc = inspect.getdoc(template_module)

source = source.replace(doc, f"Addon: {name}(v{version}), Copyright holder: {author}\n{description}", 1)

with open(path / "__init__.py", "w", encoding="utf8") as module:
    module.write(source)

