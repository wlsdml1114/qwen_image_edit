# Flux Kontext for RunPod Serverless
[English README](README.md)

이 프로젝트는 [Flux Kontext](https://github.com/Comfy-Org/Flux_Kontext)를 RunPod Serverless 환경에서 쉽게 배포하고 사용할 수 있도록 설계된 템플릿입니다.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/Flux-tontext_Runpod_hub)](https://console.runpod.io/hub/wlsdml1114/Flux-tontext_Runpod_hub)

Flux Kontext는 Flux 아키텍처를 사용하여 맥락적 이해와 창의적인 텍스트-투-이미지 기능을 가진 고품질 이미지를 생성하는 고급 AI 모델입니다.

## 🎨 Engui Studio 통합

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

이 InfiniteTalk 템플릿은 포괄적인 AI 모델 관리 플랫폼인 **Engui Studio**를 위해 주로 설계되었습니다. API를 통해 사용할 수 있지만, Engui Studio는 향상된 기능과 더 넓은 모델 지원을 제공합니다.

**Engui Studio의 장점:**
- **확장된 모델 지원**: API를 통해 사용 가능한 것보다 더 다양한 AI 모델에 접근
- **향상된 사용자 인터페이스**: 직관적인 워크플로우 관리 및 모델 선택
- **고급 기능**: AI 모델 배포를 위한 추가 도구 및 기능
- **원활한 통합**: Engui Studio 생태계에 최적화

> **참고**: 이 템플릿은 API 호출로도 완벽하게 작동하지만, Engui Studio 사용자는 향후 출시 예정인 추가 모델과 기능에 접근할 수 있습니다.

## ✨ 주요 기능

*   **텍스트-투-이미지 생성**: 맥락적 이해를 통해 텍스트 설명으로부터 고품질 이미지를 생성합니다.
*   **고급 Flux 아키텍처**: 우수한 이미지 생성 품질을 위해 최신 Flux 모델을 활용합니다.
*   **사용자 정의 가능한 매개변수**: 시드, 가이던스, 너비, 높이, 프롬프트 등 다양한 매개변수로 이미지 생성을 제어할 수 있습니다.
*   **ComfyUI 통합**: 유연한 워크플로우 관리를 위해 ComfyUI 위에 구축되었습니다.
*   **이중 CLIP 지원**: 이중 CLIP 모델 통합으로 향상된 텍스트 이해 기능을 제공합니다.

## 🚀 RunPod Serverless 템플릿

이 템플릿은 Flux Kontext를 RunPod Serverless Worker로 실행하는 데 필요한 모든 구성 요소를 포함합니다.

*   **Dockerfile**: 모델 실행에 필요한 환경을 구성하고 모든 의존성을 설치합니다.
*   **handler.py**: RunPod Serverless용 요청을 처리하는 핸들러 함수를 구현합니다.
*   **entrypoint.sh**: Worker가 시작될 때 초기화 작업을 수행합니다.
*   **flux_kontext_example.json**: 텍스트-투-이미지 생성을 위한 워크플로우 구성입니다.

### 입력

`input` 객체는 다음 필드를 포함해야 합니다. `image_path`는 **URL, 파일 경로 또는 Base64 인코딩된 문자열**을 지원합니다.

| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | **예** | `N/A` | 생성할 이미지에 대한 설명 텍스트입니다. |
| `image_path` | `string` | **예** | `N/A` | 참조 이미지의 경로, URL 또는 Base64 문자열입니다 (선택사항, 예시 이미지 사용 가능). |
| `seed` | `integer` | **예** | `N/A` | 이미지 생성을 위한 랜덤 시드 (출력의 무작위성에 영향을 줍니다). |
| `guidance` | `float` | **예** | `N/A` | 프롬프트 준수도를 제어하는 가이던스 스케일입니다. |
| `width` | `integer` | **예** | `N/A` | 출력 이미지의 픽셀 단위 너비입니다. |
| `height` | `integer` | **예** | `N/A` | 출력 이미지의 픽셀 단위 높이입니다. |

**요청 예시:**

```json
{
  "input": {
    "prompt": "the anime girl with massive fennec ears is wearing cargo pants while sitting on a log in the woods biting into a sandwich beside a beautiful alpine lake",
    "image_path": "https://path/to/your/reference.jpg",
    "seed": 12345,
    "guidance": 2.5,
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
2.  빌드가 완료되고 엔드포인트가 활성화되면 아래 API 참조에 따라 HTTP POST 요청을 통해 작업을 제출합니다.

### 📁 네트워크 볼륨 사용

Base64로 인코딩된 파일을 직접 전송하는 대신 RunPod의 Network Volumes를 사용하여 대용량 파일을 처리할 수 있습니다. 이는 특히 대용량 이미지 파일을 다룰 때 유용합니다.

1.  **네트워크 볼륨 생성 및 연결**: RunPod 대시보드에서 Network Volume(예: S3 기반 볼륨)을 생성하고 Serverless Endpoint 설정에 연결합니다.
2.  **파일 업로드**: 사용하려는 이미지 파일을 생성된 Network Volume에 업로드합니다.
3.  **경로 지정**: API 요청 시 Network Volume 내의 파일 경로를 `image_path`에 지정합니다. 예를 들어, 볼륨이 `/my_volume`에 마운트되고 `reference.jpg`를 사용하는 경우 경로는 `"/my_volume/reference.jpg"`가 됩니다.

## 🔧 워크플로우 구성

이 템플릿은 다음 워크플로우 구성을 포함합니다:

*   **flux_kontext_example.json**: 텍스트-투-이미지 생성 워크플로우

워크플로우는 ComfyUI를 기반으로 하며 Flux Kontext 처리를 위한 모든 필요한 노드를 포함합니다:
- 프롬프트를 위한 CLIP 텍스트 인코딩
- 향상된 텍스트 이해를 위한 이중 CLIP 로더
- VAE 로딩 및 처리
- Flux Kontext 모델을 사용한 UNET 로더
- 이미지 생성을 위한 사용자 정의 고급 샘플러
- 이미지 저장 및 출력 처리

## 🙏 원본 프로젝트

이 프로젝트는 다음 원본 저장소를 기반으로 합니다. 모델과 핵심 로직에 대한 모든 권리는 원본 작성자에게 있습니다.

*   **Flux Kontext:** [https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev](https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)

## 📄 라이선스

원본 Flux Kontext 프로젝트는 해당 라이선스를 따릅니다. 이 템플릿도 해당 라이선스를 준수합니다.
