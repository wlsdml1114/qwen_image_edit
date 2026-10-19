#!/usr/bin/env python3
"""
Qwen Image Edit RunPod API 테스트 스크립트
handler 입력 스펙에 맞춰 /runsync 호출 후 결과를 검증합니다.
"""

import os
import sys
import json
import base64
import argparse
from pathlib import Path
import uuid

# 프로젝트 루트의 test.env 로드 (선택)
def _load_test_env():
    env_path = Path(__file__).resolve().parent.parent / "test.env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if v.startswith('"') and v.endswith('"'):
                        v = v[1:-1]
                    os.environ.setdefault(k, v)


_load_test_env()

try:
    import requests
except ImportError:
    print("requests 필요: pip install requests")
    sys.exit(1)

def _get_s3_config():
    """
    test.env 또는 환경변수에서 RunPod Network Volume S3 설정 읽기.
    test.env 키(현재 리포): url, region, access_key_id, bucket_name, secret_access_key
    """
    endpoint_url = os.getenv("url") or os.getenv("S3_ENDPOINT_URL")
    region = os.getenv("region") or os.getenv("S3_REGION")
    access_key_id = os.getenv("access_key_id") or os.getenv("S3_ACCESS_KEY_ID")
    secret_access_key = os.getenv("secret_access_key") or os.getenv("S3_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("bucket_name") or os.getenv("S3_BUCKET_NAME")

    if not (endpoint_url and region and access_key_id and secret_access_key and bucket_name):
        return None

    return {
        "endpoint_url": endpoint_url.strip(),
        "region": region.strip(),
        "access_key_id": access_key_id.strip(),
        "secret_access_key": secret_access_key.strip(),
        "bucket_name": bucket_name.strip(),
    }

def _encode_file_to_base64(file_path: str) -> str:
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {file_path}")
    return base64.b64encode(p.read_bytes()).decode("utf-8")

def _upload_to_runpod_s3(local_path: str, s3_key: str) -> str:
    """
    RunPod Network Volume S3로 업로드 후, 워커에서 접근 가능한 경로(/runpod-volume/...) 반환.
    로컬에 boto3 필요.
    """
    s3_cfg = _get_s3_config()
    if not s3_cfg:
        raise RuntimeError("S3 설정이 없습니다. test.env에 url/region/access_key_id/bucket_name/secret_access_key를 채우세요.")

    try:
        import boto3
        from botocore.client import Config
    except ImportError as e:
        raise RuntimeError("S3 업로드에는 boto3 필요: pip install boto3") from e

    client = boto3.client(
        "s3",
        endpoint_url=s3_cfg["endpoint_url"],
        aws_access_key_id=s3_cfg["access_key_id"],
        aws_secret_access_key=s3_cfg["secret_access_key"],
        region_name=s3_cfg["region"],
        config=Config(signature_version="s3v4"),
    )

    local_path_p = Path(local_path)
    if not local_path_p.exists():
        raise FileNotFoundError(f"업로드할 파일이 존재하지 않습니다: {local_path}")

    client.upload_file(str(local_path_p), s3_cfg["bucket_name"], s3_key)
    return f"/runpod-volume/{s3_key}"

def get_config():
    """test.env 또는 환경변수에서 API 설정 읽기."""
    api_key = os.getenv("runpod_API_KEY") or os.getenv("RUNPOD_API_KEY")
    endpoint_id = os.getenv("qwen_image_edit") or os.getenv("RUNPOD_ENDPOINT_ID") or os.getenv("QWEN_IMAGE_EDIT_ENDPOINT_ID")
    if not api_key or not endpoint_id:
        print("필요한 환경변수: runpod_API_KEY (또는 RUNPOD_API_KEY), qwen_image_edit (또는 RUNPOD_ENDPOINT_ID)")
        print("프로젝트 루트의 test.env에 넣어두거나 export 하세요.")
        return None, None
    return api_key.strip(), endpoint_id.strip()


def run_sync(api_key: str, endpoint_id: str, input_payload: dict, timeout: int = 300):
    """RunPod /runsync 호출. timeout(초)로 클라이언트 대기 시간과 서버 결과 유지 시간(wait) 설정."""
    # wait: 결과 유지 시간(ms). 최대 300000(5분). runsync는 이 시간 내에 완료되면 결과 반환.
    wait_ms = min(300000, max(60000, timeout * 1000))
    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync?wait={wait_ms}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {"input": input_payload}
    r = requests.post(url, json=body, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()


def main():
    parser = argparse.ArgumentParser(description="Qwen Image Edit API 테스트")
    parser.add_argument("--json", "-j", help="입력 JSON 파일 경로 (input 객체만 있는 파일 또는 전체 { \"input\": {...} })")
    parser.add_argument("--image-url", help="테스트용 이미지 URL (단일 이미지)")
    _examples_dir = Path(__file__).resolve().parent / "examples"
    _default_input = _examples_dir / "input" / "test_input.png"
    _default_out_dir = _examples_dir / "output"
    parser.add_argument("--image-file", default=str(_default_input), help="테스트용 로컬 이미지 파일 경로 (기본: qwen_edit/examples/input/test_input.png)")
    parser.add_argument("--mode", choices=["url", "base64", "s3"], default="url", help="입력 방식: url | base64 | s3")
    parser.add_argument("--all", action="store_true", help="로컬 test_input.png로 base64 + s3 두 가지를 순차 테스트")
    parser.add_argument("--prompt", default="add watercolor style, soft pastel tones", help="편집 프롬프트")
    parser.add_argument("--seed", type=int, default=12345, help="시드")
    parser.add_argument("--width", type=int, default=768, help="너비")
    parser.add_argument("--height", type=int, default=1024, help="높이")
    parser.add_argument("--timeout", type=int, default=300, help="대기 초 (기본 300)")
    parser.add_argument("--out", "-o", help="응답 이미지 저장 경로 (미지정 시 examples/output/out_test.png 등)")
    args = parser.parse_args()
    # 기본 출력 경로: examples/output/
    if args.out is None:
        args.out = str(_default_out_dir / "out_test.png")

    api_key, endpoint_id = get_config()
    if not api_key or not endpoint_id:
        sys.exit(1)

    def _build_common():
        return {
            "prompt": args.prompt,
            "seed": args.seed,
            "width": args.width,
            "height": args.height,
        }

    def _call_once(input_payload: dict, out_path: str | None):
        # base64 payload가 매우 커질 수 있으므로 출력 시 축약
        printable = dict(input_payload)
        for k in ["image_base64", "image_base64_2", "image_base64_3"]:
            if k in printable and isinstance(printable[k], str):
                printable[k] = f"<base64:{len(printable[k])} chars>"
        print("Input:", json.dumps(printable, indent=2, ensure_ascii=False))
        print("\nRunPod runsync 호출 중...")

        try:
            result = run_sync(api_key, endpoint_id, input_payload, timeout=args.timeout)
        except requests.exceptions.RequestException as e:
            print("요청 실패:", e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    print("응답 본문:", e.response.text[:800])
                except Exception:
                    pass
            return False

        status = result.get("status")
        output = result.get("output")

        print("\nStatus:", status)
        if output:
            if isinstance(output, dict) and "error" in output:
                print("Error:", output["error"])
                return False
            if isinstance(output, dict) and "image" in output:
                img_b64 = output["image"]
                print("image 필드 있음, 길이:", len(img_b64) if isinstance(img_b64, str) else "N/A")
                if out_path and img_b64:
                    raw = base64.b64decode(img_b64)
                    out_p = Path(out_path)
                    out_p.parent.mkdir(parents=True, exist_ok=True)
                    out_p.write_bytes(raw)
                    print("저장됨:", out_path)
                return True
            print("Output (일부):", json.dumps(output, indent=2, ensure_ascii=False)[:1200])
        else:
            print("전체 응답:", json.dumps(result, indent=2, ensure_ascii=False)[:1800])

        if status == "IN_QUEUE" or status == "IN_PROGRESS":
            print("\n(참고) 작업이 아직 완료되지 않았습니다. 워커 콜드 스타트일 수 있으니 잠시 후 다시 시도하거나, /run + /status 비동기 방식을 사용하세요.")
            return False
        if status != "COMPLETED":
            return False
        print("\n테스트 통과: 결과물이 정상 반환되었습니다.")
        return True

    if args.json:
        with open(args.json, encoding="utf-8") as f:
            data = json.load(f)
        input_payload = data.get("input", data)
        ok = _call_once(input_payload, args.out)
        sys.exit(0 if ok else 1)

    if args.all:
        # 1) base64
        print("=== 테스트 1/2: base64 입력 ===")
        img_b64 = _encode_file_to_base64(args.image_file)
        payload_b64 = _build_common()
        payload_b64["image_base64"] = img_b64
        out1 = args.out
        ok1 = _call_once(payload_b64, out1)

        # 2) s3 업로드 + image_path
        print("\n=== 테스트 2/2: S3 업로드 + image_path 입력 ===")
        ext = Path(args.image_file).suffix or ".png"
        s3_key = f"qwen_edit_tests/{uuid.uuid4().hex}{ext}"
        try:
            remote_path = _upload_to_runpod_s3(args.image_file, s3_key)
            payload_s3 = _build_common()
            payload_s3["image_path"] = remote_path
            out2 = None
            if args.out:
                p = Path(args.out)
                out2 = str(p.with_name(p.stem + "_s3" + p.suffix))
            ok2 = _call_once(payload_s3, out2)
        except Exception as e:
            print("S3 테스트 준비 실패:", e)
            ok2 = False

        sys.exit(0 if (ok1 and ok2) else 1)

    # 단일 모드
    mode = args.mode
    if mode == "url":
        image_url = args.image_url or os.getenv("TEST_IMAGE_URL")
        if not image_url:
            print("--image-url 또는 TEST_IMAGE_URL 필요 (또는 --json/--all 사용)")
            sys.exit(1)
        input_payload = _build_common()
        input_payload["image_url"] = image_url
        ok = _call_once(input_payload, args.out)
        sys.exit(0 if ok else 1)

    if mode == "base64":
        img_b64 = _encode_file_to_base64(args.image_file)
        input_payload = _build_common()
        input_payload["image_base64"] = img_b64
        ok = _call_once(input_payload, args.out)
        sys.exit(0 if ok else 1)

    if mode == "s3":
        ext = Path(args.image_file).suffix or ".png"
        s3_key = f"qwen_edit_tests/{uuid.uuid4().hex}{ext}"
        remote_path = _upload_to_runpod_s3(args.image_file, s3_key)
        input_payload = _build_common()
        input_payload["image_path"] = remote_path
        ok = _call_once(input_payload, args.out)
        sys.exit(0 if ok else 1)

    print("지원하지 않는 mode:", mode)
    sys.exit(1)


if __name__ == "__main__":
    main()
