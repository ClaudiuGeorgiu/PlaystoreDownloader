#!/usr/bin/env python3

import pathlib
import re


class OutDir(type(pathlib.Path())):
    """
    A folder that knows how to name the files downloaded into it.

    A regular Path object with extra methods for building full path names for
    .apk, .obb and split apk files.

    The ugly inheritance and init signature are thanks to this bug, and related
    StackOverflow post:
    https://bugs.python.org/issue24132
    https://stackoverflow.com/questions/29850801/subclass-pathlib-path-fails/29851079#29851079
    """

    filename_pattern = re.compile(r"[^\w\-_.\s]")
    default_fname_template = "{package_name} - {title} by {creator}.apk"

    def __init__(self, *_, tag=None, meta) -> None:
        super().__init__()
        self.mkdir(parents=True, exist_ok=True)
        self.meta = meta
        self.tag = tag
        self.apk_path = self.joinpath(self.add_tag(self.build_filename()))

    def build_filename(self):
        # TODO: include title and author in the final package name?
        # return self.filename_pattern.sub(
        #     "_",
        #     self.default_fname_template.format(
        #         title=self.meta.docV2.title,
        #         creator=self.meta.docV2.creator,
        #         package_name=self.meta.docV2.docid,
        #     ),
        # )
        return f"{self.meta.package_name}.apk"

    def add_tag(self, filename):
        stripped_tag = self.tag.strip(" '\"") if self.tag else None
        return f"[{stripped_tag}] {filename}" if stripped_tag else filename

    def obb_path(self, obb):
        toplevel = "main" if obb.fileType == 0 else "patch"
        filename = f"{toplevel}.{obb.versionCode}.{self.meta.package_name}.obb"
        return self.joinpath(self.add_tag(filename))

    def split_apk_path(self, split_apk):
        version_code = self.meta.details.docV2.details.appDetails.versionCode
        filename = f"{split_apk.name}.{version_code}.{self.meta.package_name}.apk"
        return self.joinpath(self.add_tag(filename))
