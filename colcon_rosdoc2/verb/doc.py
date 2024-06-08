from collections import OrderedDict
import typing
from colcon_core.verb import VerbExtensionPoint
from colcon_core.command import CommandContext
from colcon_core.package_selection import get_package_descriptors
from colcon_core.package_selection import select_package_decorators
from colcon_core.topological_order import topological_order_packages
from colcon_core.plugin_system import satisfies_version
from colcon_core.package_selection import add_arguments as add_packages_arguments
from colcon_core.package_decorator import PackageDecorator, PackageDescriptor
from colcon_core.executor import execute_jobs
from pathlib import Path
import subprocess
from colcon_core.verb import logger
from colcon_core.task import get_task_extension, TaskContext
import os
from colcon_core.executor import Job
from colcon_core.executor import add_executor_arguments
from colcon_core.event_handler import add_event_handler_arguments


class DocVerb(VerbExtensionPoint):
    """Generate package documentation with rosdoc2."""

    def __init__(self) -> None:
        super().__init__()
        satisfies_version(VerbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def add_arguments(self, *, parser):
        add_packages_arguments(parser)
        add_executor_arguments(parser)
        add_event_handler_arguments(parser)

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
        jobs: OrderedDict = OrderedDict()
        install_base = os.path.abspath(os.path.join(os.getcwd(), "install"))
        for decorator in sorted(decorators, key=lambda d: d.descriptor.name):
            decorator: PackageDecorator
            if not decorator.selected:
                continue
            pkg: PackageDescriptor = decorator.descriptor
            assert type(pkg.type) == str
            if not pkg.type.startswith("ros"):
                continue

            extension = get_task_extension("colcon_rosdoc2.task.rosdoc2", pkg.type)
            if not extension:
                logger.warning(
                    f"No task extension to document a '{pkg.type}' package with rosdoc2"
                )
                continue

            recursive_dependencies = OrderedDict()
            for dep_name in decorator.recursive_dependencies:
                dep_path = os.path.join(install_base, dep_name)
                recursive_dependencies[dep_name] = dep_path

            task_context = TaskContext(
                pkg=pkg, args=None, dependencies=recursive_dependencies
            )

            job = Job(
                identifier=pkg.name,
                dependencies=set(recursive_dependencies.keys()),
                task=extension,
                task_context=task_context,
            )

            jobs[pkg.name] = job

        execute_jobs(context, jobs)
        return 0
