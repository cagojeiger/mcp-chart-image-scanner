"""Extract Docker images from Helm charts.

Core functionality for extracting Docker images from Helm charts.
"""

from __future__ import annotations

import logging
import pathlib
import subprocess
import sys
import tarfile
import tempfile
from typing import Any, List, Set, Optional, Union

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

ImageSet = Set[str]


def extract_chart(chart_archive: pathlib.Path, dest_dir: pathlib.Path) -> pathlib.Path:
    """Extract a chart archive to the specified directory and return the chart root.

    Args:
        chart_archive: The .tgz Helm chart archive to extract
        dest_dir: The destination directory

    Returns:
        The root directory of the extracted chart

    Raises:
        RuntimeError: If the chart structure is unexpected
    """
    logger.info(f"Extracting chart archive: {chart_archive}")
    with tarfile.open(chart_archive, "r:gz") as tar:
        tar.extractall(dest_dir)

    roots = [p for p in dest_dir.iterdir() if p.is_dir()]
    if len(roots) != 1:
        raise RuntimeError(
            f"Unexpected chart archive structure: {len(roots)} top‑level entries found."
        )
    logger.info(f"Chart root directory: {roots[0]}")
    return roots[0]


def prepare_chart(chart_path: pathlib.Path, workdir: pathlib.Path) -> pathlib.Path:
    """Prepare a chart (either an archive or a directory).
    
    Args:
        chart_path: Path to the .tgz archive or chart directory
        workdir: Working directory

    Returns:
        Chart root directory

    Raises:
        FileNotFoundError: If the chart directory does not exist
        ValueError: If the chart format or structure is invalid
    """
    logger.info(f"Preparing chart: {chart_path}")

    if chart_path.is_dir():
        if not chart_path.exists():
            raise FileNotFoundError(f"Chart directory does not exist: {chart_path}")

        if not (chart_path / "Chart.yaml").exists():
            raise ValueError(f"Not a valid Helm chart directory: {chart_path}")

        logger.info(f"Using directory chart: {chart_path}")
        return chart_path

    elif chart_path.is_file() and chart_path.suffix in ['.tgz', '.tar.gz']:
        logger.info(f"Using compressed chart: {chart_path}")
        return extract_chart(chart_path, workdir)

    else:
        raise ValueError(f"Unsupported chart format: {chart_path} (only directory or .tgz file supported)")


def helm_dependency_update(chart_dir: pathlib.Path) -> None:
    """Run the helm dependency update command on the chart directory.

    Does not raise an error if there are no dependencies.

    Args:
        chart_dir: Helm chart directory
    """
    logger.info(f"Updating chart dependencies: {chart_dir}")
    subprocess.run(
        ["helm", "dependency", "update", str(chart_dir)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    logger.info("Dependency update completed")


def helm_template(chart_dir: pathlib.Path, values_files: List[pathlib.Path]) -> str:
    """Run the helm template command on the chart directory and return the rendered manifests.

    Args:
        chart_dir: Helm chart directory
        values_files: List of additional values files

    Returns:
        Rendered Kubernetes manifests

    Raises:
        FileNotFoundError: If values files do not exist
        subprocess.CalledProcessError: If helm template command fails
    """
    cmd: list[str] = ["helm", "template", "dummy", str(chart_dir)]

    if values_files:
        logger.info(f"Using specified values files: {', '.join(str(v) for v in values_files)}")
        for vf in values_files:
            abs_path = vf if vf.is_absolute() else pathlib.Path.cwd() / vf
            if not abs_path.exists():
                raise FileNotFoundError(f"Values file not found: {vf}")
            cmd.extend(["-f", str(abs_path)])
    else:
        default_values = chart_dir / "values.yaml"
        if default_values.exists():
            logger.info(f"Using default values.yaml file: {default_values}")
            cmd.extend(["-f", str(default_values)])
        else:
            logger.info("No values files available")

    logger.info(f"Rendering chart template: {chart_dir}")
    logger.info(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout


def _add_repo_tag_digest(images: ImageSet, repo: str, tag: Optional[str], digest: Optional[str]) -> None:
    """Add an image with repository and tag or digest to the image set.

    Args:
        images: Image set
        repo: Image repository
        tag: Image tag (optional)
        digest: Image digest (optional)
    """
    if tag:
        images.add(f"{repo}:{tag}")
    elif digest:
        images.add(f"{repo}@{digest}")
    else:
        images.add(repo)


def _traverse(obj: Any, images: ImageSet) -> None:
    """Recursively traverse an object to collect image references.

    Finds the following patterns:
    1. Full image string fields (image: "repo:tag")
    2. Separate field combinations:
       - repository + tag/version/digest
       - repository + image + tag/version

    Args:
        obj: Object to traverse (dictionary or list)
        images: Set to store found images
    """
    if isinstance(obj, dict):
        img_val = obj.get("image")
        if isinstance(img_val, str) and not obj.get("repository"):
            images.add(img_val)

        repo = obj.get("repository")
        img = obj.get("image")
        tag = obj.get("tag") or obj.get("version")
        digest = obj.get("digest")

        if isinstance(repo, str):
            if isinstance(img, str):
                full_repo = f"{repo}/{img}"
            else:
                full_repo = repo

            if isinstance(tag, str) or isinstance(digest, str):
                _add_repo_tag_digest(images, full_repo,
                                     tag if isinstance(tag, str) else None,
                                     digest if isinstance(digest, str) else None)

        for value in obj.values():
            _traverse(value, images)

    elif isinstance(obj, list):
        for item in obj:
            _traverse(item, images)


def normalize_image_name(image: str) -> str:
    """Normalize a Docker image name.

    Standard format: [REGISTRY_HOST[:PORT]/][NAMESPACE/]REPOSITORY[:TAG][@DIGEST]

    Normalization rules:
    1. Missing registry → apply docker.io (Docker Hub)
    2. Missing namespace → apply library (Docker Hub only)
    3. Missing tag → apply latest

    Args:
        image: Original image name

    Returns:
        Normalized image name

    Examples:
        nginx → docker.io/library/nginx:latest
        user/repo → docker.io/user/repo:latest
        nvcr.io/nvidia → nvcr.io/nvidia:latest
        nvcr.io/nvidia/cuda → nvcr.io/nvidia/cuda:latest
    """
    has_digest = '@' in image
    digest_part = ""

    if has_digest:
        base_part, digest_part = image.split('@', 1)
        image = base_part

    has_tag = ':' in image and not (':' in image.split('/', 1)[0] if '/' in image else False)
    tag_part = "latest"  # Default value

    if has_tag:
        image_part, tag_part = image.split(':', 1)
        image = image_part

    has_domain = False
    domain_part = ""
    remaining_part = image

    if '/' in image:
        domain_candidate, remaining = image.split('/', 1)
        if ('.' in domain_candidate) or (domain_candidate == 'localhost') or (':' in domain_candidate):
            has_domain = True
            domain_part = domain_candidate
            remaining_part = remaining

    if has_domain:
        normalized = f"{domain_part}/{remaining_part}"
    else:
        if '/' in remaining_part:
            normalized = f"docker.io/{remaining_part}"
        else:
            normalized = f"docker.io/library/{remaining_part}"

    if has_digest:
        return f"{normalized}@{digest_part}"
    else:
        return f"{normalized}:{tag_part}"


def collect_images(rendered_yaml: str, normalize: bool = True) -> List[str]:
    """Parse image references from rendered YAML documents and return a deduplicated sorted list.

    Args:
        rendered_yaml: Rendered Kubernetes manifests
        normalize: Whether to normalize image names

    Returns:
        Sorted list of images
    """
    logger.info("Collecting images from rendered manifests")
    images: ImageSet = set()
    doc_count = 0

    for doc in yaml.safe_load_all(rendered_yaml):
        if doc is not None:
            doc_count += 1
            _traverse(doc, images)

    logger.info(f"Processed {doc_count} documents, found {len(images)} unique images")

    if normalize:
        normalized_images = {normalize_image_name(img) for img in images}
        logger.info(f"After normalization, {len(normalized_images)} unique images remain")
        return sorted(normalized_images)
    else:
        return sorted(images)


def extract_images_from_chart(
    chart_path: Union[str, pathlib.Path],
    values_files: Optional[List[Union[str, pathlib.Path]]] = None,
    normalize: bool = True,
) -> List[str]:
    """Extract Docker images from a Helm chart.

    This is the main function that combines all the steps to extract images from a chart.

    Args:
        chart_path: Path to the .tgz chart archive or chart directory
        values_files: List of additional values files
        normalize: Whether to normalize image names

    Returns:
        Sorted list of Docker images

    Raises:
        FileNotFoundError: If chart path or values files do not exist
        ValueError: If chart format is invalid
        subprocess.CalledProcessError: If helm commands fail
    """
    chart_path = pathlib.Path(chart_path)
    values_files_paths = []
    if values_files:
        values_files_paths = [pathlib.Path(vf) for vf in values_files]

    with tempfile.TemporaryDirectory() as tmp:
        workdir = pathlib.Path(tmp)
        logger.info(f"Created temporary working directory: {workdir}")

        chart_root = prepare_chart(chart_path, workdir)

        helm_dependency_update(chart_root)

        rendered = helm_template(chart_root, values_files_paths)
        logger.info(f"Template rendering completed: {len(rendered)} bytes")

        images = collect_images(rendered, normalize=normalize)
        logger.info(f"Image extraction completed: found {len(images)} images")

        return images
