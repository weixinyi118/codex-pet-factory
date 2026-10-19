# Provider Routing

## Default Order

1. Use `$imagegen` built-in generation when available.
2. If unavailable, ask once before using a configured CLI or direct provider API.
3. Prefer the Codex-configured OpenAI-compatible provider when it supports image generation.
4. Use Aliyun Bailian only when the user has authorized it and the selected model supports the required multi-image or edit operation.

## Preflight

- Inspect whether keys exist; never print key values.
- Normalize OpenAI-compatible base URLs to the documented API root, commonly ending in `/v1`.
- Send one small smoke-test image request before the first expensive row.
- Record provider name, model, base URL without credentials, request input bytes, output path, and result in the run manifest.
- Do not infer that a key is invalid from a network timeout. Separate DNS, connection, gateway, authentication, and model errors.

## Payload Discipline

- Never embed production images as `data:image` in the Codex conversation.
- Use the compact reference pack and local file paths.
- Attach only the canonical base, the row layout guide, and at most one continuity reference unless another identity cue is essential.
- Keep the default reference payload below 5 MiB. If a provider adds multipart overhead or returns 413, reduce below 3 MiB before retrying.
- Do not reuse an image-rich failed task for continued generation. Resume from the disk manifest in a clean task.

## Provider-Specific Failure Patterns

- `413 REQUEST_TOO_LARGE`: reduce request attachments and conversation history; increasing generation timeout does not help.
- OpenAI connection timeout before authentication: verify provider base URL and network route before changing keys.
- Bailian image dimension error: upscale layout-only guides to the provider minimum while retaining the target cell contract separately.
- Repeated left/right mirroring: stop prompt-only retries after two failures. Rebuild from approved screen-coordinate cardinals or switch model/provider.
- Multi-object edit collapses to one subject: use a coherent strip generation model instead of a single-image editor.

## Retry Budget

- Allow at most two prompt-only retries for the same failure mode.
- Change the evidence, model, or operation after the second repeat.
- Record why each candidate failed so a later task does not repeat the same attempt.
