#!/usr/bin/env python3
"""extract_helm_images.py

Extract Docker image references (repository + tag or digest) from a compressed
Helm chart archive (``.tgz``) or unpacked chart directory.

The script adheres to the Google Python Style Guide.

Example::

    python extract_helm_images.py chart-1.2.3.tgz \
        -f prod-values.yaml -f secrets.yaml

Output::

    docker.io/nginx:1.25.4
    ghcr.io/bitnami/redis:7.2.4
"""

from __future__ import annotations

import argparse
import logging
import pathlib
import subprocess
import sys
import tarfile
import tempfile
from typing import Any, List, Set

import yaml

# 로깅 설정 - stderr로 출력하도록 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr  # 로그를 stderr로 출력
)
logger = logging.getLogger(__name__)

ImageSet = Set[str]


# ----------------------------------------------------------------------------
# Helm helpers
# ----------------------------------------------------------------------------

def extract_chart(chart_archive: pathlib.Path, dest_dir: pathlib.Path) -> pathlib.Path:
    """차트 아카이브를 지정된 디렉토리에 추출하고 차트 루트를 반환합니다.

    Args:
        chart_archive: 추출할 .tgz 형식의 Helm 차트 아카이브
        dest_dir: 추출 대상 디렉토리

    Returns:
        추출된 차트의 루트 디렉토리

    Raises:
        RuntimeError: 예상치 못한 차트 구조일 경우
    """
    logger.info(f"차트 아카이브 추출 중: {chart_archive}")
    with tarfile.open(chart_archive, "r:gz") as tar:
        tar.extractall(dest_dir)

    roots = [p for p in dest_dir.iterdir() if p.is_dir()]
    if len(roots) != 1:
        raise RuntimeError(
            f"Unexpected chart archive structure: {len(roots)} top‑level entries found."
        )
    logger.info(f"차트 루트 디렉토리: {roots[0]}")
    return roots[0]


def prepare_chart(chart_path: pathlib.Path, workdir: pathlib.Path) -> pathlib.Path:
    """압축된 차트 또는 디렉토리 형태의 차트를 준비합니다.
    
    Args:
        chart_path: .tgz 아카이브 또는 차트 디렉토리 경로
        workdir: 작업 디렉토리

    Returns:
        차트 루트 디렉토리

    Raises:
        FileNotFoundError: 차트 디렉토리가 존재하지 않을 경우
        ValueError: 유효하지 않은 차트 형식이나 구조일 경우
    """
    logger.info(f"차트 준비 중: {chart_path}")

    # 디렉토리인 경우
    if chart_path.is_dir():
        # 디렉토리가 존재하는지 확인
        if not chart_path.exists():
            raise FileNotFoundError(f"차트 디렉토리가 존재하지 않습니다: {chart_path}")

        # Chart.yaml 파일 존재 확인으로 유효한 차트 디렉토리인지 검증
        if not (chart_path / "Chart.yaml").exists():
            raise ValueError(f"유효한 Helm 차트 디렉토리가 아닙니다: {chart_path}")

        logger.info(f"디렉토리 차트 사용: {chart_path}")
        return chart_path

    # 파일인 경우 (.tgz)
    elif chart_path.is_file() and chart_path.suffix in ['.tgz', '.tar.gz']:
        logger.info(f"압축된 차트 사용: {chart_path}")
        return extract_chart(chart_path, workdir)

    # 지원하지 않는 형식
    else:
        raise ValueError(f"지원하지 않는 차트 형식입니다: {chart_path} (디렉토리 또는 .tgz 파일만 지원)")


def helm_dependency_update(chart_dir: pathlib.Path) -> None:
    """차트 디렉토리에 대해 helm dependency update 명령을 실행합니다.

    의존성이 없는 경우에도 오류를 발생시키지 않습니다.

    Args:
        chart_dir: Helm 차트 디렉토리
    """
    logger.info(f"차트 의존성 업데이트: {chart_dir}")
    subprocess.run(
        ["helm", "dependency", "update", str(chart_dir)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    logger.info("의존성 업데이트 완료")


def helm_template(chart_dir: pathlib.Path, values_files: List[pathlib.Path]) -> str:
    """차트 디렉토리에 대해 helm template 명령을 실행하고 렌더링된 매니페스트를 반환합니다.

    Args:
        chart_dir: Helm 차트 디렉토리
        values_files: 추가 values 파일 목록

    Returns:
        렌더링된 Kubernetes 매니페스트

    Raises:
        FileNotFoundError: values 파일이 존재하지 않을 경우
        subprocess.CalledProcessError: helm template 명령 실행 실패 시
    """
    cmd: list[str] = ["helm", "template", "dummy", str(chart_dir)]

    # 값 파일이 지정되었으면 해당 파일들을 사용
    if values_files:
        logger.info(f"지정된 values 파일 사용: {', '.join(str(v) for v in values_files)}")
        for vf in values_files:
            # 상대 경로를 절대 경로로 변환
            abs_path = vf if vf.is_absolute() else pathlib.Path.cwd() / vf
            if not abs_path.exists():
                raise FileNotFoundError(f"Values 파일을 찾을 수 없습니다: {vf}")
            cmd.extend(["-f", str(abs_path)])
    else:
        # 기본 values.yaml 파일이 차트 디렉토리에 있다면 사용
        default_values = chart_dir / "values.yaml"
        if default_values.exists():
            logger.info(f"기본 values.yaml 파일 사용: {default_values}")
            cmd.extend(["-f", str(default_values)])
        else:
            logger.info("사용 가능한 values 파일 없음")

    logger.info(f"차트 템플릿 렌더링 중: {chart_dir}")
    logger.info(f"실행 명령어: {' '.join(cmd)}")

    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout


# ----------------------------------------------------------------------------
# YAML traversal
# ----------------------------------------------------------------------------

def _add_repo_tag_digest(images: ImageSet, repo: str, tag: str | None, digest: str | None) -> None:
    """저장소와 태그 또는 다이제스트를 결합하여 이미지 세트에 추가합니다.

    Args:
        images: 이미지 세트
        repo: 이미지 저장소
        tag: 이미지 태그 (선택적)
        digest: 이미지 다이제스트 (선택적)
    """
    if tag:
        images.add(f"{repo}:{tag}")
    elif digest:
        images.add(f"{repo}@{digest}")
    else:
        images.add(repo)


def _traverse(obj: Any, images: ImageSet) -> None:
    """객체를 재귀적으로 순회하여 이미지 참조를 수집합니다.

    다음 패턴들을 찾습니다:
    1. 완전한 이미지 문자열 필드 (image: "repo:tag")
    2. 분리된 필드 조합:
       - repository + tag/version/digest
       - repository + image + tag/version

    Args:
        obj: 순회할 객체 (딕셔너리 또는 리스트)
        images: 발견된 이미지를 저장할 세트
    """
    if isinstance(obj, dict):
        # Case 1: full image string.
        img_val = obj.get("image")
        if isinstance(img_val, str) and not obj.get("repository"):
            images.add(img_val)

        # Case 2: separate fields combinations
        repo = obj.get("repository")
        img = obj.get("image")
        tag = obj.get("tag") or obj.get("version")
        digest = obj.get("digest")

        if isinstance(repo, str):
            # repository가 있고 image도 있으면 결합
            if isinstance(img, str):
                full_repo = f"{repo}/{img}"
            else:
                full_repo = repo

            # tag/version 또는 digest 추가
            if isinstance(tag, str) or isinstance(digest, str):
                _add_repo_tag_digest(images, full_repo,
                                     tag if isinstance(tag, str) else None,
                                     digest if isinstance(digest, str) else None)

        # Recurse.
        for value in obj.values():
            _traverse(value, images)

    elif isinstance(obj, list):
        for item in obj:
            _traverse(item, images)


def normalize_image_name(image: str) -> str:
    """Docker 이미지 이름을 표준화합니다.

    표준 형식: [REGISTRY_HOST[:PORT]/][NAMESPACE/]REPOSITORY[:TAG][@DIGEST]

    표준화 규칙:
    1. 레지스트리 생략 → docker.io 적용 (Docker Hub)
    2. 네임스페이스 생략 → library 적용 (Docker Hub 전용)
    3. 태그 생략 → latest 적용

    Args:
        image: 원본 이미지 이름

    Returns:
        표준화된 이미지 이름

    예시:
        nginx → docker.io/library/nginx:latest
        user/repo → docker.io/user/repo:latest
        nvcr.io/nvidia → nvcr.io/nvidia:latest
        nvcr.io/nvidia/cuda → nvcr.io/nvidia/cuda:latest
    """
    # 다이제스트가 있는지 확인
    has_digest = '@' in image
    digest_part = ""

    # 다이제스트 분리
    if has_digest:
        base_part, digest_part = image.split('@', 1)
        image = base_part

    # 태그 분리
    has_tag = ':' in image and not (':' in image.split('/', 1)[0] if '/' in image else False)
    tag_part = "latest"  # 기본값

    if has_tag:
        image_part, tag_part = image.split(':', 1)
        image = image_part

    # 도메인(레지스트리) 확인
    has_domain = False
    domain_part = ""
    remaining_part = image

    if '/' in image:
        domain_candidate, remaining = image.split('/', 1)
        # 도메인은 '.'을 포함하거나 localhost이거나 포트를 가짐
        if ('.' in domain_candidate) or (domain_candidate == 'localhost') or (':' in domain_candidate):
            has_domain = True
            domain_part = domain_candidate
            remaining_part = remaining

    # 최종 이미지 이름 구성
    if has_domain:
        # 커스텀 레지스트리인 경우
        normalized = f"{domain_part}/{remaining_part}"
    else:
        # Docker Hub인 경우
        if '/' in remaining_part:
            # 사용자/리포지토리 형식
            normalized = f"docker.io/{remaining_part}"
        else:
            # 단일 이름 형식
            normalized = f"docker.io/library/{remaining_part}"

    # 태그와 다이제스트 추가
    if has_digest:
        return f"{normalized}@{digest_part}"
    else:
        return f"{normalized}:{tag_part}"


def collect_images(rendered_yaml: str) -> List[str]:
    """렌더링된 YAML 문서에서 이미지 참조를 파싱하고 중복 제거된 정렬 목록을 반환합니다.

    Args:
        rendered_yaml: 렌더링된 Kubernetes 매니페스트

    Returns:
        정렬된 이미지 목록
    """
    logger.info("렌더링된 매니페스트에서 이미지 수집 중")
    images: ImageSet = set()
    doc_count = 0

    for doc in yaml.safe_load_all(rendered_yaml):
        if doc is not None:
            doc_count += 1
            _traverse(doc, images)

    logger.info(f"총 {doc_count}개 문서 처리, {len(images)}개 고유 이미지 발견")

    # 이미지 이름 표준화 및 중복 제거
    normalized_images = {normalize_image_name(img) for img in images}
    logger.info(f"표준화 후 {len(normalized_images)}개 고유 이미지 남음")

    return sorted(normalized_images)


# ----------------------------------------------------------------------------
# CLI interface
# ----------------------------------------------------------------------------

def _parse_cli() -> argparse.Namespace:  # » chart: Path, values: List[Path]
    """명령줄 인수를 파싱합니다.

    Returns:
        파싱된 명령줄 인수
    """
    parser = argparse.ArgumentParser(
        description="Extract Docker images used by a Helm chart archive or directory.",
    )
    parser.add_argument(
        "chart",
        type=pathlib.Path,
        help="Path to the .tgz Helm chart archive or unpacked chart directory",
    )
    parser.add_argument(
        "-f",
        "--values",
        type=pathlib.Path,
        action="append",
        default=[],
        help="Additional values.yaml file(s)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress log messages (stderr)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON array"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output raw image names without normalization"
    )
    return parser.parse_args()


def main() -> None:
    """스크립트의 메인 실행 함수입니다."""
    args = _parse_cli()

    # 로그 레벨 설정 (quiet 옵션)
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)

    logger.info(f"스크립트 시작: 차트={args.chart}, values 파일={args.values or '없음'}")

    # Work inside a throw‑away directory so that temp files are scrubbed.
    with tempfile.TemporaryDirectory() as tmp:
        workdir = pathlib.Path(tmp)
        logger.info(f"임시 작업 디렉토리 생성: {workdir}")

        try:
            # .tgz 아카이브 또는 디렉토리 처리
            chart_root = prepare_chart(args.chart, workdir)

            helm_dependency_update(chart_root)
            rendered = helm_template(chart_root, args.values)
            logger.info(f"매니페스트 렌더링 완료: {len(rendered)} 바이트")

            images = collect_images(rendered)

            # 결과 출력 (stdout으로)
            if images:
                logger.info(f"이미지 추출 완료: {len(images)}개 발견")
                if args.json:
                    # JSON 형식으로 출력
                    import json
                    print(json.dumps(images))
                else:
                    # 일반 텍스트 형식으로 출력
                    print("\n".join(images))
            else:
                logger.error("이미지 필드를 찾을 수 없음")
                sys.exit(1)
        except Exception as e:
            logger.error(f"오류 발생: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()