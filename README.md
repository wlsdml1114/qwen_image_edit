# Qwen Image Edit for RunPod Serverless
[한국어 README 보기](README_kr.md)

This project is a template designed to easily deploy and use an image editing workflow (Qwen Image Edit via ComfyUI) in the RunPod Serverless environment.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/qwen_image_edit)](https://console.runpod.io/hub/wlsdml1114/qwen_image_edit)

The template performs prompt-guided image editing using ComfyUI workflows. It supports one or two input images and accepts inputs as path, URL, or Base64.

## 🎨 Engui Studio Integration

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

This Qwen Image Edit template is primarily designed for **Engui Studio**, a comprehensive AI model management platform. While it can be used via API, Engui Studio provides enhanced features and broader model support.

**Engui Studio Benefits:**
- **Expanded Model Support**: Access to a wide variety of AI models beyond what's available through API
- **Enhanced User Interface**: Intuitive workflow management and model selection
- **Advanced Features**: Additional tools and capabilities for AI model deployment
- **Seamless Integration**: Optimized for Engui Studio's ecosystem

> **Note**: While this template works perfectly with API calls, Engui Studio users will have access to additional models and features that are planned for future releases.

## ✨ Key Features

*   **Prompt-Guided Image Editing**: Edit images based on a text prompt.
*   **One or Two Input Images**: Automatically selects single- or dual-image workflow.
*   **Flexible Inputs**: Provide images via file path, URL, or Base64 string.
*   **Customizable Parameters**: Control seed, width, height, and prompt.
*   **ComfyUI Integration**: Built on top of ComfyUI for flexible workflow management.

## 🚀 RunPod Serverless Template

This template includes all the necessary components to run Qwen Image Edit as a RunPod Serverless Worker.

*   **Dockerfile**: Configures the environment and installs all dependencies required for model execution.
*   **handler.py**: Implements the handler function that processes requests for RunPod Serverless.
*   **entrypoint.sh**: Performs initialization tasks when the worker starts.
*   **qwen_image_edit_1.json / qwen_image_edit_2.json**: ComfyUI workflows for single- or dual-image editing.

### Input

The `input` object must contain the following fields. Image inputs support **URL, file path, or Base64 encoded string**.

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | **Yes** | `N/A` | Text prompt that guides the edit. |
| `image_path` or `image_url` or `image_base64` | `string` | **Yes** | `N/A` | First image input (path/URL/Base64). |
| `image_path_2` or `image_url_2` or `image_base64_2` | `string` | No | `N/A` | Optional second image input (path/URL/Base64). Enables dual-image workflow. |
| `seed` | `integer` | **Yes** | `N/A` | Random seed for deterministic output. |
| `width` | `integer` | **Yes** | `N/A` | Output image width in pixels. |
| `height` | `integer` | **Yes** | `N/A` | Output image height in pixels. |

Notes:
- Guidance is not used by the current handler.
- If any of the `*_2` fields are provided, the dual-image workflow is selected automatically.

**Request Example (single image via URL):**

```json
{
  "input": {
    "prompt": "add watercolor style, soft pastel tones",
    "image_url": "https://path/to/your/reference.jpg",
    "seed": 12345,
    "width": 768,
    "height": 1024
  }
}
```

**Request Example (dual images, path + URL):**

```json
{
  "input": {
    "prompt": "blend subject A and subject B, cinematic lighting",
    "image_path": "/network_volume/img_a.jpg",
    "image_url_2": "https://path/to/img_b.jpg",
    "seed": 7777,
    "width": 1024,
    "height": 1024
  }
}
```

**Request Example (single image via Base64):**

```json
{
  "input": {
    "prompt": "vintage look, grain, warm tones",
    "image_base64": "<BASE64_STRING>",
    "seed": 42,
    "width": 512,
    "height": 512
  }
}
```

### Output

#### Success

If the job is successful, it returns a JSON object with the generated image Base64 encoded.

| Parameter | Type | Description |
| --- | --- | --- |
| `image` | `string` | Base64 encoded image file data. |

**Success Response Example:**

```json
{
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

#### Error

If the job fails, it returns a JSON object containing an error message.

| Parameter | Type | Description |
| --- | --- | --- |
| `error` | `string` | Description of the error that occurred. |

**Error Response Example:**

```json
{
  "error": "이미지를 찾을 수 없습니다."
}
```

## 🛠️ Usage and API Reference

1.  Create a Serverless Endpoint on RunPod based on this repository.
2.  Once the build is complete and the endpoint is active, submit jobs via HTTP POST requests according to the API Reference above.

### 📁 Using Network Volumes

Instead of directly transmitting Base64 encoded files, you can use RunPod's Network Volumes to handle large files. This is especially useful when dealing with large image files.

1.  **Create and Connect Network Volume**: Create a Network Volume (e.g., S3-based volume) from the RunPod dashboard and connect it to your Serverless Endpoint settings.
2.  **Upload Files**: Upload the image files you want to use to the created Network Volume.
3.  **Specify Paths**: When making an API request, specify the file paths within the Network Volume for `image_path` or `image_path_2`. For example, if the volume is mounted at `/my_volume` and you use `reference.jpg`, the path would be `"/my_volume/reference.jpg"`.

## 🔧 Workflow Configuration

This template includes the following workflow configurations:

*   **qwen_image_edit_1.json**: Single-image editing workflow
*   **qwen_image_edit_2.json**: Dual-image editing workflow

The workflows are based on ComfyUI and include necessary nodes for prompt-guided image editing and output processing.

## 🙏 Original Project

This project is based on the following repositories. All rights to the model and core logic belong to the original authors.

*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **Qwen (project group):** [https://github.com/QwenLM/Qwen-Image](https://github.com/QwenLM/Qwen-Image)

## 📄 License

This template adheres to the licenses of the original projects.
