# Use specific version of nvidia cuda image
FROM wlsdml1114/multitalk-base:1.7 as runtime

# wget 설치 (URL 다운로드를 위해)
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

RUN pip install -U "huggingface_hub[hf_transfer]"
RUN pip install runpod websocket-client librosa

# Set working directory
WORKDIR /

RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && \
    pip install --no-cache-dir -r requirements.txt
RUN cd /ComfyUI/custom_nodes/ && \
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git && \
    cd ComfyUI-Manager && \
    pip install --no-cache-dir -r requirements.txt

# Download models
RUN hf download Comfy-Org/flux1-kontext-dev_ComfyUI split_files/diffusion_models/flux1-dev-kontext_fp8_scaled.safetensors --local-dir /ComfyUI/models/unet/
RUN hf download comfyanonymous/flux_text_encoders clip_l.safetensors --local-dir=/ComfyUI/models/clip/
RUN hf download comfyanonymous/flux_text_encoders t5xxl_fp16.safetensors --local-dir=/ComfyUI/models/clip/
RUN wget -q https://huggingface.co/Comfy-Org/Lumina_Image_2.0_Repackaged/resolve/main/split_files/vae/ae.safetensors -O /ComfyUI/models/vae/ae.safetensors


COPY . .
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]