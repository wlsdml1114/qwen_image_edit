# Flux Kontext for RunPod Serverless
[한국어 README 보기](README_kr.md)

This project is a template designed to easily deploy and use [Flux Kontext](https://github.com/Comfy-Org/Flux_Kontext) in the RunPod Serverless environment.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/Flux-tontext_Runpod_hub)](https://console.runpod.io/hub/wlsdml1114/Flux-tontext_Runpod_hub)

Flux Kontext is an advanced AI model that generates high-quality images with contextual understanding and creative text-to-image capabilities using the Flux architecture.

## 🎨 Engui Studio Integration

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

This InfiniteTalk template is primarily designed for **Engui Studio**, a comprehensive AI model management platform. While it can be used via API, Engui Studio provides enhanced features and broader model support.

**Engui Studio Benefits:**
- **Expanded Model Support**: Access to a wider variety of AI models beyond what's available through API
- **Enhanced User Interface**: Intuitive workflow management and model selection
- **Advanced Features**: Additional tools and capabilities for AI model deployment
- **Seamless Integration**: Optimized for Engui Studio's ecosystem

> **Note**: While this template works perfectly with API calls, Engui Studio users will have access to additional models and features that are planned for future releases.

## ✨ Key Features

*   **Text-to-Image Generation**: Creates high-quality images from text descriptions with contextual understanding.
*   **Advanced Flux Architecture**: Utilizes the latest Flux model for superior image generation quality.
*   **Customizable Parameters**: Control image generation with various parameters including seed, guidance, width, height, and prompts.
*   **ComfyUI Integration**: Built on top of ComfyUI for flexible workflow management.
*   **Dual CLIP Support**: Enhanced text understanding with dual CLIP model integration.

## 🚀 RunPod Serverless Template

This template includes all the necessary components to run Flux Kontext as a RunPod Serverless Worker.

*   **Dockerfile**: Configures the environment and installs all dependencies required for model execution.
*   **handler.py**: Implements the handler function that processes requests for RunPod Serverless.
*   **entrypoint.sh**: Performs initialization tasks when the worker starts.
*   **flux_kontext_example.json**: Text-to-image generation workflow configuration.

### Input

The `input` object must contain the following fields. `image_path` supports **URL, file path, or Base64 encoded string**.

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | **Yes** | `N/A` | Description text for the image to be generated. |
| `image_path` | `string` | **Yes** | `N/A` | Path, URL, or Base64 string of the reference image (optional, can be example image). |
| `seed` | `integer` | **Yes** | `N/A` | Random seed for image generation (affects output randomness). |
| `guidance` | `float` | **Yes** | `N/A` | Guidance scale for controlling generation adherence to prompt. |
| `width` | `integer` | **Yes** | `N/A` | Width of the output image in pixels. |
| `height` | `integer` | **Yes** | `N/A` | Height of the output image in pixels. |

**Request Example:**

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
2.  Once the build is complete and the endpoint is active, submit jobs via HTTP POST requests according to the API Reference below.

### 📁 Using Network Volumes

Instead of directly transmitting Base64 encoded files, you can use RunPod's Network Volumes to handle large files. This is especially useful when dealing with large image files.

1.  **Create and Connect Network Volume**: Create a Network Volume (e.g., S3-based volume) from the RunPod dashboard and connect it to your Serverless Endpoint settings.
2.  **Upload Files**: Upload the image files you want to use to the created Network Volume.
3.  **Specify Paths**: When making an API request, specify the file paths within the Network Volume for `image_path`. For example, if the volume is mounted at `/my_volume` and you use `reference.jpg`, the path would be `"/my_volume/reference.jpg"`.

## 🔧 Workflow Configuration

This template includes the following workflow configuration:

*   **flux_kontext_example.json**: Text-to-image generation workflow

The workflow is based on ComfyUI and includes all necessary nodes for Flux Kontext processing:
- CLIP Text Encoding for prompts
- Dual CLIP Loader for enhanced text understanding
- VAE Loading and processing
- UNET Loader with Flux Kontext model
- Custom Advanced Sampler for image generation
- Image saving and output processing

## 🙏 Original Project

This project is based on the following original repository. All rights to the model and core logic belong to the original authors.

*   **Flux Kontext:** [https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev](https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)

## 📄 License

The original Flux Kontext project follows its respective license. This template also adheres to that license.
