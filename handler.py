import runpod
from runpod.serverless.utils import rp_upload
import os
import websocket
import base64
import json
import uuid
import logging
import urllib.request
import urllib.parse
import binascii # Base64 에러 처리를 위해 import
import subprocess
import time
import io
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_DEFAULT_NEGATIVE_PROMPT = (
    "extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, "
    "deformed hands, malformed face, asymmetrical eyes, duplicate people, "
    "unwanted text, watermark, logo, blurry details"
)


def enhance_prompt(user_prompt: str) -> str:
    """Optional LLM enhancement; preserve user intent and safely fall back."""
    prompt = str(user_prompt or "").strip()
    if not prompt:
        raise ValueError("prompt is required")
    if not os.getenv("OPENAI_API_KEY"):
        return prompt
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                     "Content-Type": "application/json"},
            json={
                "model": os.getenv("PROMPT_ENHANCER_MODEL", "gpt-4o-mini"),
                "temperature": 0.2,
                "max_tokens": 450,
                "messages": [
                    {"role": "system", "content": (
                        "Improve this image-edit instruction with clear composition, lighting, "
                        "materials, and natural anatomy. Preserve the user's intent, identity, "
                        "counts, requested changes, and any quoted wording exactly. Do not add "
                        "new subjects, text, logos, or claims. Never promise perfect results. "
                        "Return only the improved instruction."
                    )},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=(5, 20),
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        return content[:12000] or prompt
    except Exception as exc:
        logger.warning("Optional prompt enhancement failed; using original prompt (%s)", type(exc).__name__)
        return prompt


def _font_for_overlay(name: str, size: int):
    candidates = {
        "sans": ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        "sans-bold": ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                      "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
        "serif": ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",),
        "mono": ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",),
    }.get(name, ())
    for path in candidates:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def apply_text_overlay(image_bytes: bytes, config: dict) -> bytes:
    """Render caller-supplied copy after generation; never asks the image model to spell it."""
    if not isinstance(config, dict):
        raise ValueError("text_overlay must be an object")
    text = config.get("text")
    if not isinstance(text, str) or not text.strip() or len(text) > 240:
        raise ValueError("text_overlay.text must contain 1-240 characters")
    position = str(config.get("position", "bottom")).lower()
    if position not in {"bottom", "center"}:
        raise ValueError("text_overlay.position must be 'bottom' or 'center'")
    color = str(config.get("color", "#FFFFFF"))
    if len(color) != 7 or color[0] != "#":
        raise ValueError("text_overlay.color must be a hex color such as #FFFFFF")
    try:
        rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    except ValueError as exc:
        raise ValueError("text_overlay.color must be a hex color such as #FFFFFF") from exc

    with Image.open(io.BytesIO(image_bytes)) as source:
        image = source.convert("RGBA")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    max_width = int(width * 0.88)
    size = max(12, min(int(config.get("font_size", max(18, height // 18))), height // 5))
    font = _font_for_overlay(str(config.get("font", "sans-bold")), size)
    # Wrap by measured pixels and shrink until all lines fit the safe area.
    lines = []
    for paragraph in text.splitlines() or [text]:
        current = ""
        for word in paragraph.split():
            # Split unusually long unbroken tokens so a URL-like word cannot
            # escape the image bounds.
            pieces = [word]
            while draw.textbbox((0, 0), pieces[-1], font=font)[2] > max_width and len(pieces[-1]) > 1:
                token = pieces.pop()
                midpoint = max(1, len(token) // 2)
                pieces.extend((token[:midpoint], token[midpoint:]))
            for piece in pieces:
                candidate = f"{current} {piece}".strip()
                if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
                    lines.append(current)
                    current = piece
                else:
                    current = candidate
        if current:
            lines.append(current)
    while size > 12:
        line_heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
        if max(line_heights, default=0) * len(lines) + 12 * (len(lines) - 1) <= height * 0.35:
            break
        size -= 2
        font = _font_for_overlay(str(config.get("font", "sans-bold")), size)
    gap = max(4, size // 4)
    heights = [max(1, draw.textbbox((0, 0), line, font=font)[3]) for line in lines]
    block_h = sum(heights) + gap * max(0, len(lines) - 1)
    if block_h > height * 0.7:
        raise ValueError("text_overlay is too long to fit legibly on this image")
    y = (height - block_h) // 2 if position == "center" else height - block_h - max(24, height // 24)
    pad_y = max(8, height // 80)
    draw.rounded_rectangle((width * .05, y - pad_y, width * .95, y + block_h + pad_y),
                           radius=max(6, size // 3), fill=(0, 0, 0, 150))
    for line, line_h in zip(lines, heights):
        x = (width - draw.textbbox((0, 0), line, font=font)[2]) // 2
        draw.text((x, y), line, font=font, fill=(*rgb, 255),
                  stroke_width=max(1, size // 32), stroke_fill=(0, 0, 0, 220))
        y += line_h + gap
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def verify_and_normalize_image(image_bytes: bytes) -> bytes:
    """Verify uploaded image and normalize it to a clean JPEG."""
    if not image_bytes:
        raise ValueError("Reference image is empty.")

    with Image.open(io.BytesIO(image_bytes)) as check:
        check.verify()

    with Image.open(io.BytesIO(image_bytes)) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")

        if image.width < 64 or image.height < 64:
            raise ValueError("Reference image must be at least 64x64 pixels.")

        if image.width * image.height > 40_000_000:
            raise ValueError("Reference image exceeds the 40-megapixel limit.")

        output = io.BytesIO()
        image.save(output, format="JPEG", quality=95, optimize=True)
        return output.getvalue()


def upload_image_to_comfy(image_bytes: bytes, task_id: str) -> str:
    """Upload a verified image to ComfyUI's managed input folder."""
    jpeg_bytes = verify_and_normalize_image(image_bytes)

    url = f"http://{server_address}:8188/upload/image"
    filename = f"qwen_reference_{task_id}.jpg"

    response = requests.post(
        url,
        files={"image": (filename, jpeg_bytes, "image/jpeg")},
        data={"type": "input", "overwrite": "true"},
        timeout=60,
    )
    response.raise_for_status()

    result = response.json()
    uploaded_name = result.get("name")

    if not uploaded_name or result.get("type") != "input":
        raise RuntimeError(f"ComfyUI returned an invalid image-upload response: {result}")

    return uploaded_name
# CUDA 검사 및 설정
def check_cuda_availability():
    """CUDA 사용 가능 여부를 확인하고 환경 변수를 설정합니다."""
    try:
        import torch
        if torch.cuda.is_available():
            logger.info("✅ CUDA is available and working")
            os.environ['CUDA_VISIBLE_DEVICES'] = '0'
            return True
        else:
            logger.error("❌ CUDA is not available")
            raise RuntimeError("CUDA is required but not available")
    except Exception as e:
        logger.error(f"❌ CUDA check failed: {e}")
        raise RuntimeError(f"CUDA initialization failed: {e}")

# CUDA 검사 실행
try:
    cuda_available = check_cuda_availability()
    if not cuda_available:
        raise RuntimeError("CUDA is not available")
except Exception as e:
    logger.error(f"Fatal error: {e}")
    logger.error("Exiting due to CUDA requirements not met")
    exit(1)



server_address = os.getenv('SERVER_ADDRESS', '127.0.0.1')
client_id = str(uuid.uuid4())
_HANDLER_JOB_COUNT = 0
def save_data_if_base64(data_input, temp_dir, output_filename):
    """
    입력 데이터가 Base64 문자열인지 확인하고, 맞다면 파일로 저장 후 경로를 반환합니다.
    만약 일반 경로 문자열이라면 그대로 반환합니다.
    """
    # 입력값이 문자열이 아니면 그대로 반환
    if not isinstance(data_input, str):
        return data_input

    try:
        # Base64 문자열은 디코딩을 시도하면 성공합니다.
        decoded_data = base64.b64decode(data_input)
        
        # 디렉토리가 존재하지 않으면 생성
        os.makedirs(temp_dir, exist_ok=True)
        
        # 디코딩에 성공하면, 임시 파일로 저장합니다.
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        with open(file_path, 'wb') as f: # 바이너리 쓰기 모드('wb')로 저장
            f.write(decoded_data)
        
        # 저장된 파일의 경로를 반환합니다.
        print(f"✅ Base64 입력을 '{file_path}' 파일로 저장했습니다.")
        return file_path

    except (binascii.Error, ValueError):
        # 디코딩에 실패하면, 일반 경로로 간주하고 원래 값을 그대로 반환합니다.
        print(f"➡️ '{data_input}'은(는) 파일 경로로 처리합니다.")
        return data_input
    
def queue_prompt(prompt):
    url = f"http://{server_address}:8188/prompt"
    logger.info(f"Queueing prompt to: {url}")
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    url = f"http://{server_address}:8188/view"
    logger.info(f"Getting image from: {url}")
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{url}?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    url = f"http://{server_address}:8188/history/{prompt_id}"
    logger.info(f"Getting history from: {url}")
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        if 'images' in node_output:
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                # bytes 객체를 base64로 인코딩하여 JSON 직렬화 가능하게 변환
                if isinstance(image_data, bytes):
                    import base64
                    image_data = base64.b64encode(image_data).decode('utf-8')
                images_output.append(image_data)
        output_images[node_id] = images_output

    return output_images

def load_workflow(workflow_path):
    with open(workflow_path, 'r') as file:
        return json.load(file)

# 새 워크플로우 파일명: 이미지 개수별
_WORKFLOW_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflow")
_WORKFLOW_FILES = {
    1: "qwen_image_edit_1_1image.json",
    2: "qwen_image_edit_1_2image.json",
    3: "qwen_image_edit_1_3image.json",
}

# 워크플로우별 노드 ID (이미지 개수에 따라 사용)
# 1-image: LoadImage=78, KSampler(seed)=3, prompt=111
# 2-image: 위 + LoadImage2=117
# 3-image: 위 + LoadImage3=119
_NODE_IMAGE_1 = "78"
_NODE_IMAGE_2 = "117"
_NODE_IMAGE_3 = "119"
_NODE_SEED = "3"
_NODE_PROMPT = "111"
_NODE_NEGATIVE_PROMPT = "110"
_NODE_WIDTH = "128"   # 현재 워크플로우에는 없음(선택 적용)
_NODE_HEIGHT = "129"  # 현재 워크플로우에는 없음(선택 적용)

# ------------------------------
# 입력 처리 유틸 (path/url/base64)
# ------------------------------
def process_input(input_data, temp_dir, output_filename, input_type):
    """입력 데이터를 처리하여 파일 경로를 반환하는 함수
    - input_type: "path" | "url" | "base64"
    """
    if input_type == "path":
        logger.info(f"📁 경로 입력 처리: {input_data}")
        return input_data
    elif input_type == "url":
        logger.info(f"🌐 URL 입력 처리: {input_data}")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        return download_file_from_url(input_data, file_path)
    elif input_type == "base64":
        logger.info("🔢 Base64 입력 처리")
        return save_base64_to_file(input_data, temp_dir, output_filename)
    else:
        raise Exception(f"지원하지 않는 입력 타입: {input_type}")

def download_file_from_url(url, output_path):
    """URL에서 파일을 다운로드하는 함수"""
    try:
        result = subprocess.run([
            'wget', '-O', output_path, '--no-verbose', url
        ], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ URL에서 파일을 성공적으로 다운로드했습니다: {url} -> {output_path}")
            return output_path
        else:
            logger.error(f"❌ wget 다운로드 실패: {result.stderr}")
            raise Exception(f"URL 다운로드 실패: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("❌ 다운로드 시간 초과")
        raise Exception("다운로드 시간 초과")
    except Exception as e:
        logger.error(f"❌ 다운로드 중 오류 발생: {e}")
        raise Exception(f"다운로드 중 오류 발생: {e}")

def save_base64_to_file(base64_data, temp_dir, output_filename):
    """Base64 데이터를 파일로 저장하는 함수"""
    try:
        decoded_data = base64.b64decode(base64_data)
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        with open(file_path, 'wb') as f:
            f.write(decoded_data)
        logger.info(f"✅ Base64 입력을 '{file_path}' 파일로 저장했습니다.")
        return file_path
    except (binascii.Error, ValueError) as e:
        logger.error(f"❌ Base64 디코딩 실패: {e}")
        raise Exception(f"Base64 디코딩 실패: {e}")

def handler(job):
    global _HANDLER_JOB_COUNT
    _HANDLER_JOB_COUNT += 1
    job_number = _HANDLER_JOB_COUNT
    request_started = time.monotonic()
    job_input = job.get("input", {})

    # Do not log base64 image payloads or potentially private image URLs/paths.
    logger.info("Received job input fields: %s", sorted(job_input.keys()))
    task_id = f"task_{uuid.uuid4()}"

    # ------------------------------
    # 이미지 입력 수집 (1개 / 2개 / 3개)
    # 지원 키: image_path | image_url | image_base64
    #         image_path_2 | image_url_2 | image_base64_2
    #         image_path_3 | image_url_3 | image_base64_3
    # ------------------------------
    image_paths = []

    for i, suffix in enumerate([ "", "_2", "_3" ], start=1):
        path_key = f"image_path{suffix}"
        url_key = f"image_url{suffix}"
        b64_key = f"image_base64{suffix}"
        fname = f"input_image_{i}.jpg"
        if path_key in job_input:
            image_paths.append(process_input(job_input[path_key], task_id, fname, "path"))
        elif url_key in job_input:
            image_paths.append(process_input(job_input[url_key], task_id, fname, "url"))
        elif b64_key in job_input:
            image_paths.append(process_input(job_input[b64_key], task_id, fname, "base64"))
        else:
            break

    num_images = len(image_paths)
    logger.info("QWEN_TIMING phase=input_preparation seconds=%.3f images=%d worker_job=%d",
                time.monotonic() - request_started, num_images, job_number)
    if num_images == 0:
        return {"error": "최소 1개의 이미지 입력이 필요합니다. (image_path / image_url / image_base64 중 하나)"}

    if num_images not in _WORKFLOW_FILES:
        return {"error": f"지원하는 이미지 개수는 1, 2, 3개입니다. 입력된 이미지: {num_images}개"}

    workflow_filename = _WORKFLOW_FILES[num_images]
    workflow_path = os.path.join(_WORKFLOW_BASE, workflow_filename)
    if not os.path.exists(workflow_path):
        return {"error": f"워크플로우 파일을 찾을 수 없습니다: {workflow_path}"}

    prompt = load_workflow(workflow_path)

    # Upload every reference through ComfyUI's managed input endpoint.
    # The absolute /task_... paths returned by process_input are not valid
    # LoadImage values; LoadImage expects the uploaded input filename.
    uploaded_image_names = []
    for image_index, image_path in enumerate(image_paths, start=1):
        try:
            with open(image_path, "rb") as image_file:
                image_bytes = image_file.read()
        except OSError as exc:
            raise RuntimeError(
                f"Could not read reference image {image_index} for ComfyUI upload."
            ) from exc

        uploaded_image_names.append(
            upload_image_to_comfy(image_bytes, f"{task_id}_{image_index}")
        )

    prompt[_NODE_IMAGE_1]["inputs"]["image"] = uploaded_image_names[0]
    if num_images >= 2:
        prompt[_NODE_IMAGE_2]["inputs"]["image"] = uploaded_image_names[1]
    if num_images >= 3:
        prompt[_NODE_IMAGE_3]["inputs"]["image"] = uploaded_image_names[2]

    user_prompt = job_input.get("prompt", "")
    prompt[_NODE_PROMPT]["inputs"]["prompt"] = enhance_prompt(user_prompt)
    # This ComfyUI graph has a real negative conditioning node (110), unlike
    # workflows that merely append negatives to the positive prompt.
    negative_prompt = str(job_input.get("negative_prompt") or _DEFAULT_NEGATIVE_PROMPT)
    if _NODE_NEGATIVE_PROMPT in prompt:
        prompt[_NODE_NEGATIVE_PROMPT]["inputs"]["prompt"] = negative_prompt[:3000]
    if _NODE_SEED in prompt and "seed" in job_input:
        prompt[_NODE_SEED]["inputs"]["seed"] = job_input["seed"]
    if _NODE_WIDTH in prompt and "width" in job_input:
        prompt[_NODE_WIDTH]["inputs"]["value"] = job_input["width"]
    if _NODE_HEIGHT in prompt and "height" in job_input:
        prompt[_NODE_HEIGHT]["inputs"]["value"] = job_input["height"]

    ws_url = f"ws://{server_address}:8188/ws?clientId={client_id}"
    logger.info(f"Connecting to WebSocket: {ws_url}")
    
    # 먼저 HTTP 연결이 가능한지 확인
    http_url = f"http://{server_address}:8188/"
    logger.info(f"Checking HTTP connection to: {http_url}")
    
    # HTTP 연결 확인 (최대 1분)
    max_http_attempts = 180
    for http_attempt in range(max_http_attempts):
        try:
            import urllib.request
            response = urllib.request.urlopen(http_url, timeout=5)
            logger.info(f"HTTP 연결 성공 (시도 {http_attempt+1})")
            break
        except Exception as e:
            logger.warning(f"HTTP 연결 실패 (시도 {http_attempt+1}/{max_http_attempts}): {e}")
            if http_attempt == max_http_attempts - 1:
                raise Exception("ComfyUI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
            time.sleep(1)
    
    ws = websocket.WebSocket()
    # 웹소켓 연결 시도 (최대 3분)
    max_attempts = int(180/5)  # 3분 (1초에 한 번씩 시도)
    for attempt in range(max_attempts):
        try:
            ws.connect(ws_url)
            logger.info(f"웹소켓 연결 성공 (시도 {attempt+1})")
            break
        except Exception as e:
            logger.warning(f"웹소켓 연결 실패 (시도 {attempt+1}/{max_attempts}): {e}")
            if attempt == max_attempts - 1:
                raise Exception("웹소켓 연결 시간 초과 (3분)")
            time.sleep(5)
    inference_started = time.monotonic()
    images = get_images(ws, prompt)
    logger.info("QWEN_TIMING phase=comfy_inference_and_possible_model_load seconds=%.3f worker_job=%d",
                time.monotonic() - inference_started, job_number)
    ws.close()

    # 이미지가 없는 경우 처리
    if not images:
        return {"error": "이미지를 생성할 수 없습니다."}
    
    # 첫 번째 이미지 반환
    for node_id in images:
        if images[node_id]:
            output_bytes = base64.b64decode(images[node_id][0], validate=True)
            overlay = job_input.get("text_overlay")
            if overlay:
                output_bytes = apply_text_overlay(output_bytes, overlay)
            logger.info("QWEN_TIMING phase=job_total seconds=%.3f worker_job=%d",
                        time.monotonic() - request_started, job_number)
            return {"image": base64.b64encode(output_bytes).decode("ascii")}
    
    return {"error": "이미지를 찾을 수 없습니다."}

runpod.serverless.start({"handler": handler})
