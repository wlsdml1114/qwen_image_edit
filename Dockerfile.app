# Build small application-only releases against a previously published,
# immutable Qwen runtime image. Pass a registry image digest as build arg.
ARG QWEN_RUNTIME_IMAGE
FROM ${QWEN_RUNTIME_IMAGE}

WORKDIR /
COPY handler.py /handler.py
COPY workflow/ /workflow/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
