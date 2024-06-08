from colcon_core.verb import VerbExtensionPoint
from colcon_core.command import CommandContext
from colcon_core.package_selection import get_package_descriptors
from colcon_core.package_selection import select_package_decorators
from colcon_core.topological_order import topological_order_packages
from colcon_core.plugin_system import satisfies_version
from colcon_core.package_selection import add_arguments as add_packages_arguments
from colcon_core.package_decorator import PackageDecorator, PackageDescriptor
from pathlib import Path
import subprocess


class DocVerb(VerbExtensionPoint):
    """Generate package documentation with rosdoc2."""

    def __init__(self) -> None:
        super().__init__()
        satisfies_version(VerbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def add_arguments(self, *, parser):
        add_packages_arguments(parser)

    def main(self, *, context: CommandContext):
        """
        Execute the verb extension logic.

        :param context: The context providing the parsed command line arguments
        :returns: The return code
        """
        descriptors = get_package_descriptors(context.args)

        decorators = topological_order_packages(
            descriptors, recursive_categories=("run",)
        )
        select_package_decorators(context.args, decorators)

        if not decorators:
            return "No packages found"
        for decorator in sorted(decorators, key=lambda d: d.descriptor.name):
            decorator: PackageDecorator
            if not decorator.selected:
                continue
            pkg: PackageDescriptor = decorator.descriptor
            assert type(pkg.type) == str
            if not pkg.type.startswith("ros"):
                continue
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
        return 0
