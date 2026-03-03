Building a tinyc Docker image

This image is a convenience container that provides a `tinyc` executable inside
the container. It supports two modes:

- If you have a custom `tinyc` binary (Linux ELF), place it at
  `docker/tinyc/tinyc` and build the image. The Dockerfile will copy that
  binary into `/usr/local/bin/tinyc` and use it as the container entrypoint.

- If you do not provide a `tinyc` binary, the Dockerfile attempts to clone and
  build `tinycc` from source and symlink the `tcc` binary to `/usr/local/bin/tinyc`.

Build (from repo root):

```bash
cd docker/tinyc
# Option A: build using provided local tinyc binary (if you copied one to ./tinyc)
docker build -t mini-compiler-tinyc:local .

# Option B: let the Dockerfile build tinycc from source (may take a minute)
docker build -t mini-compiler-tinyc:local .
```

Use in backend

Set environment variable `TINYC_DOCKER_IMAGE=mini-compiler-tinyc:local` (or the tag you chose).

You can also set `TINYC_DOCKER_CMD` if your binary uses a different command name.
