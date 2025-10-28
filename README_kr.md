# Qwen Image Edit for RunPod Serverless
[English README](README.md)

이 프로젝트는 RunPod Serverless 환경에서 ComfyUI 기반의 이미지 편집 워크플로우(Qwen Image Edit)를 쉽게 배포하고 사용할 수 있도록 설계된 템플릿입니다.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/qwen_image_edit)](https://console.runpod.io/hub/wlsdml1114/qwen_image_edit)

이 템플릿은 프롬프트 기반의 이미지 편집을 수행하며, 1장 또는 2장의 입력 이미지를 지원하고 경로/URL/Base64 방식의 입력을 받을 수 있습니다.

## 🎨 Engui Studio 통합

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

이 Qwen Image Edit 템플릿은 포괄적인 AI 모델 관리 플랫폼인 **Engui Studio**를 위해 주로 설계되었습니다. API를 통해 사용할 수 있지만, Engui Studio는 향상된 기능과 더 넓은 모델 지원을 제공합니다.

**Engui Studio의 장점:**
- **확장된 모델 지원**: API를 통해 사용 가능한 것보다 더 다양한 AI 모델에 접근
- **향상된 사용자 인터페이스**: 직관적인 워크플로우 관리 및 모델 선택
- **고급 기능**: AI 모델 배포를 위한 추가 도구 및 기능
- **원활한 통합**: Engui Studio 생태계에 최적화

> **참고**: 이 템플릿은 API 호출로도 완벽하게 작동하지만, Engui Studio 사용자는 향후 출시 예정인 추가 모델과 기능에 접근할 수 있습니다.

## ✨ 주요 기능

*   **프롬프트 기반 이미지 편집**: 텍스트 프롬프트로 편집을 유도합니다.
*   **단일/이중 이미지 입력**: 입력 이미지 수에 따라 워크플로우가 자동 선택됩니다.
*   **유연한 입력 방식**: 경로, URL, Base64 문자열 입력을 지원합니다.
*   **사용자 정의 가능한 매개변수**: 시드, 너비, 높이, 프롬프트를 제어합니다.
*   **ComfyUI 통합**: 유연한 워크플로우 관리를 위해 ComfyUI 위에 구축되었습니다.

## 🚀 RunPod Serverless 템플릿

이 템플릿은 Qwen Image Edit를 RunPod Serverless Worker로 실행하는 데 필요한 모든 구성 요소를 포함합니다.

*   **Dockerfile**: 모델 실행에 필요한 환경을 구성하고 모든 의존성을 설치합니다.
*   **handler.py**: RunPod Serverless용 요청을 처리하는 핸들러 함수를 구현합니다.
*   **entrypoint.sh**: Worker가 시작될 때 초기화 작업을 수행합니다.
*   **qwen_image_edit_1.json / qwen_image_edit_2.json**: 단일/이중 이미지 편집용 ComfyUI 워크플로우입니다.

### 입력

`input` 객체는 다음 필드를 포함해야 합니다. 이미지 입력은 **URL, 파일 경로 또는 Base64 인코딩된 문자열**을 지원합니다.

| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | **예** | `N/A` | 편집을 유도하는 텍스트 프롬프트입니다. |
| `image_path` 또는 `image_url` 또는 `image_base64` | `string` | **예** | `N/A` | 첫 번째 이미지 입력 (경로/URL/Base64). |
| `image_path_2` 또는 `image_url_2` 또는 `image_base64_2` | `string` | 아니오 | `N/A` | 선택적 두 번째 이미지 입력 (경로/URL/Base64). 제공 시 이중 이미지 워크플로우 사용. |
| `seed` | `integer` | **예** | `N/A` | 동일 결과 재현을 위한 랜덤 시드. |
| `width` | `integer` | **예** | `N/A` | 출력 이미지의 너비(픽셀). |
| `height` | `integer` | **예** | `N/A` | 출력 이미지의 높이(픽셀). |

참고:
- 현재 핸들러는 guidance 매개변수를 사용하지 않습니다.
- `*_2` 필드 중 하나라도 제공되면 자동으로 이중 이미지 워크플로우가 선택됩니다.

**요청 예시 (단일 이미지, URL):**

```json
{
  "input": {
    "prompt": "수채화 느낌, 파스텔 톤",
    "image_url": "https://path/to/your/reference.jpg",
    "seed": 12345,
    "width": 768,
    "height": 1024
  }
}
```

**요청 예시 (이중 이미지, 경로 + URL):**

```json
{
  "input": {
    "prompt": "A와 B를 자연스럽게 블렌딩, 시네마틱 조명",
    "image_path": "/network_volume/img_a.jpg",
    "image_url_2": "https://path/to/img_b.jpg",
    "seed": 7777,
    "width": 1024,
    "height": 1024
  }
}
```

**요청 예시 (단일 이미지, Base64):**

```json
{
  "input": {
    "prompt": "빈티지 감성, 그레인, 웜 톤",
    "image_base64": "<BASE64_STRING>",
    "seed": 42,
    "width": 512,
    "height": 512
  }
}
```

### 출력

#### 성공

작업이 성공하면 생성된 이미지가 Base64로 인코딩된 JSON 객체를 반환합니다.

| 매개변수 | 타입 | 설명 |
| --- | --- | --- |
| `image` | `string` | Base64로 인코딩된 이미지 파일 데이터입니다. |

**성공 응답 예시:**

```json
{
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

#### 오류

작업이 실패하면 오류 메시지를 포함한 JSON 객체를 반환합니다.

| 매개변수 | 타입 | 설명 |
| --- | --- | --- |
| `error` | `string` | 발생한 오류에 대한 설명입니다. |

**오류 응답 예시:**

```json
{
  "error": "이미지를 찾을 수 없습니다."
}
```

## 🛠️ 사용법 및 API 참조

1.  이 저장소를 기반으로 RunPod에서 Serverless Endpoint를 생성합니다.
2.  빌드가 완료되고 엔드포인트가 활성화되면 위 API 스펙에 따라 HTTP POST 요청을 통해 작업을 제출합니다.

### 📁 네트워크 볼륨 사용

Base64로 인코딩된 파일을 직접 전송하는 대신 RunPod의 Network Volumes를 사용하여 대용량 파일을 처리할 수 있습니다. 이는 특히 대용량 이미지 파일을 다룰 때 유용합니다.

1.  **네트워크 볼륨 생성 및 연결**: RunPod 대시보드에서 Network Volume(예: S3 기반 볼륨)을 생성하고 Serverless Endpoint 설정에 연결합니다.
2.  **파일 업로드**: 사용하려는 이미지 파일을 생성된 Network Volume에 업로드합니다.
3.  **경로 지정**: API 요청 시 Network Volume 내의 파일 경로를 `image_path` 또는 `image_path_2`에 지정합니다. 예: 볼륨이 `/my_volume`에 마운트되고 `reference.jpg`를 사용하는 경우 경로는 `"/my_volume/reference.jpg"`입니다.

## 🔧 워크플로우 구성

이 템플릿은 다음 워크플로우 구성을 포함합니다:

*   **qwen_image_edit_1.json**: 단일 이미지 편집 워크플로우
*   **qwen_image_edit_2.json**: 이중 이미지 편집 워크플로우

워크플로우는 ComfyUI를 기반으로 하며 프롬프트 기반 이미지 편집 및 출력 처리를 위한 필요한 노드를 포함합니다.

## 🙏 원본 프로젝트

이 프로젝트는 다음 저장소를 기반으로 합니다. 모델과 핵심 로직에 대한 모든 권리는 원본 작성자에게 있습니다.

*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **Qwen (project group):** [https://github.com/QwenLM/Qwen-Image](https://github.com/QwenLM/Qwen-Image)

## 📄 라이선스

이 템플릿은 원본 프로젝트의 라이선스를 준수합니다.
