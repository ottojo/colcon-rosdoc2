from colcon_core.task import TaskExtensionPoint, TaskContext
from colcon_core.plugin_system import satisfies_version
import subprocess
from pathlib import Path


class Rosdoc2Task(TaskExtensionPoint):

    context: TaskContext

    def __init__(self):
        super().__init__()
        satisfies_version(TaskExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    async def rosdoc2(self, *args, **kwargs):
        pkg = self.context.pkg
        doc_build_dir = Path("build_doc")
        output_dir = Path("install_doc")
        # --install-directory ? --cross-reference-directory ?  ? --doc-build-directory ?
        subprocess.run(
            [
                "rosdoc2",
                "build",
                "--package-path",
                pkg.path,
                "--output-directory",
                output_dir,
                "--doc-build-directory",
                doc_build_dir,
            ]
        )
