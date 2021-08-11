import pathlib
import re


class OutDir(type(pathlib.Path())):
    """A folder that knows how to name the files downloaded to it
    
    A regular Path object with extra methods for building full path names for
    apk, obb and split apk files.

    The ugly inheritance and init signature are thanks to this bug, and related
    StackOverflow post:

    https://bugs.python.org/issue24132
    https://stackoverflow.com/questions/29850801/subclass-pathlib-path-fails/29851079#29851079
    """
    filename_pattern = re.compile(r"[^\w\-_.\s]")
    default_fname_template = "{title} by {creator} - {package_name}.apk"

    def __init__(self, *_, tag, meta) -> None:
        if not self.exists or not self.is_dir:
            raise ValueError(f"{self} is not a directory")
        self.meta = meta
        self.tag = tag
        self.apk_path = self.joinpath(self.add_tag(self.build_filename()))
        super().__init__()

    def build_filename(self):
        return self.filename_pattern.sub(
            "_",
            self.default_fname_template.format(
                title=self.meta.docV2.title,
                creator=self.meta.docV2.creator,
                package_name=self.meta.docV2.docid,
            ),
        )

    def add_tag(self, filename):
        return f"{self.tag} {filename}" if self.tag else filename

    def obb_path(self, obb):
        toplevel = 'main' if obb.fileType == 0 else 'patch'
        filename = f"{toplevel}.{obb.versionCode}.{self.meta.details.docid}.obb"
        return self.joinpath(self.add_tag(filename))

    def split_apk_path(self, split_apk):
        version_code = self.meta.details.docV2.details.appDetails.versionCode
        filename = f"{split_apk.name}.{version_code}.{self.package_name}.apk"
        return self.joinpath(self.add_tag(filename))
