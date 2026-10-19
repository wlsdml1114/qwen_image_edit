# Qwen worker build separation

## What the supplied Runpod build log proves

The log covers a completed 38.53 GB worker image build. The four Qwen model
download steps took 136.3 seconds in total (84.9 + 5.4 + 43.9 + 2.1 seconds).
The final image export took 808.3 seconds, including 576.2 seconds exporting
layers and 232.1 seconds sending the export tarball. Build-cache export took a
further 358.9 seconds. Registry push took 90.9 seconds; 24.88 GB of layer data
was reported uploaded. Therefore the main measured delay in this log is image
export/cache serialization and upload, not Qwen GPU initialization or 30
minutes of model downloading. The displayed dependency installs were seconds
to about a minute each, not the dominant phase.

This is a measured build, not a cold-start or warm-inference benchmark. The log
contains no worker startup or per-request timings.

## What this changes

`Dockerfile.runtime` is the slow, infrequent image: Python dependencies,
ComfyUI/custom nodes, and Qwen weights are installed there. Build and publish
it only when those components or model files need an update. For production,
prefer promoting the currently validated runtime image into the chosen registry
and recording its digest instead of rebuilding it from mutable upstream sources.

`Dockerfile.app` is the frequent, small image: it copies only `handler.py`,
the ComfyUI workflow JSONs, and the entrypoint over the immutable runtime
image. Use a registry digest (not a mutable tag) for `QWEN_RUNTIME_IMAGE`.
The existing `Dockerfile` is retained as the original all-in-one fallback.

## Required one-time deployment setup

1. Promote the currently validated runtime image into the chosen container
   registry and record its immutable digest. It contains the large model and
   dependency layers. Do not rebuild `Dockerfile.runtime` as part of ordinary
   app updates.
2. Add that exact digest as the GitHub repository variable
   `QWEN_RUNTIME_IMAGE`. Configure the persistent Linux runner described in
   `.github/workflows/build-qwen-app-image.yml`; it needs enough free disk to
   retain the 38.53 GB runtime layers.
3. Push a handler/workflow change. The workflow builds and pushes the small app
   image to GHCR, reusing the runtime layers. The PowerShell helper can also
   build it manually.
4. Configure a staging Runpod Serverless endpoint to pull the published image
   (and GHCR credentials if the package is private). Verify 1-image, 2-image,
   and 3-image requests, then change production endpoint image to the tested
   immutable app digest. Keep the prior digest for rollback.
5. Later handler/workflow edits publish app images only. Rebuild the runtime
   only for dependency, ComfyUI/custom-node, CUDA/base-image, or model changes.

## Limits and cost controls

- This repository cannot confirm or change the live endpoint's Build source,
  image registry credentials, Network Volume, cached-model selection, active
  workers, idle timeout, or FlashBoot settings.
- No Runpod endpoint, paid storage, or always-on worker setting is changed here.
- A persistent self-hosted runner is a prerequisite for the included fast
  workflow. GitHub-hosted runner disk capacity is not assumed sufficient for
  the 38.53 GB base image. Creating a runner may have infrastructure cost; do
  not provision one without choosing/approving its host and cost.
- A first runtime image build still downloads the models. The supplied log
  reports a 38.53 GB image; keeping the runtime digest unchanged lets app-only
  images reuse its existing registry layers. The actual result depends on the
  registry and endpoint deployment path.
- The runtime Dockerfile currently follows upstream default branches and
  Hugging Face `main` URLs, as the existing deployment does. The built runtime
  image digest freezes the exact artifact used by app-only releases. Before
  intentionally rebuilding that runtime, record/pin upstream commits and
  verify model file revisions/checksums.

## Timing evidence

Runpod's Builds tab reports separate Pending, Building, Uploading, Testing, and
Completed phases. Worker logs now report startup and per-request phase timings.
Compare Build-tab durations with first-job delay/execution metrics and a second
warm request. The exact supplied log identifies export/cache/push as the build
bottleneck; it does not measure GPU startup or warm latency.
