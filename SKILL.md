# GLM-4.6V-Flash CLI Skill

## Purpose

Use this skill to provide visual perception capabilities to Claude or another agent by calling Zhipu AI's `GLM-4.6V-Flash` vision model from the command line.

This skill is especially useful when the agent needs to understand visual information that cannot be reliably inferred from text alone, including:

- Screenshots and application UI
- Game scenes and game-art assets
- Error dialogs and visual debugging information
- Photos and general images
- Diagrams, charts, and visual layouts
- Multiple-image comparison
- Reading visible text or structured information from images
- Inspecting visual differences, composition, style, color, objects, and spatial relationships

When a task requires visual perception, image understanding, screenshot inspection, or comparison of visual content, prefer using this skill rather than guessing from filenames or surrounding text.

The CLI command is:

```bash
glm
```

It supports:

- Text prompts
- Local image input
- Image URLs
- Multiple images
- Video URLs
- File URLs
- Streaming output
- Optional thinking mode

## Requirements

The API key must be available through the environment variable:

```text
ZAI_API_KEY
```

Do not hard-code the API key into commands, source code, or files.

On PowerShell:

```powershell
$env:ZAI_API_KEY="your_api_key"
```

## Basic Usage

Text-only request:

```bash
glm "Explain what skeletal animation is."
```

Ask about a local image:

```bash
glm -i image.png "Describe this image in detail."
```

Ask about multiple images:

```bash
glm -i a.png -i b.png "Compare these two images."
```

Use an image URL:

```bash
glm -i "https://example.com/image.png" "What is shown here?"
```

## Thinking Mode

Thinking is enabled by default.

Disable it for faster/simple requests:

```bash
glm --thinking disabled "Answer briefly."
```

Show returned reasoning content:

```bash
glm --show-thinking "Analyze this problem."
```

## Streaming

Streaming is enabled by default.

Disable streaming:

```bash
glm --no-stream "Summarize this."
```

## Standard Input

The CLI can read the prompt from stdin:

```bash
echo "Summarize this text" | glm
```

PowerShell example:

```powershell
Get-Content .\prompt.txt -Raw | glm
```

## Video and File URLs

Video URL:

```bash
glm --video "https://example.com/video.mp4" "Summarize the video."
```

File URL:

```bash
glm --file "https://example.com/document.pdf" "Summarize this document."
```

## Important Constraints

- The model is fixed to `glm-4.6v-flash`.
- Local images are automatically encoded as Base64.
- Local video and local generic file upload are not implemented; use accessible URLs for them.
- Do not mix image, video, and file modalities in the same request.
- Prefer quoting prompts and paths containing spaces.
- If the command fails because `ZAI_API_KEY` is missing, ask the user to configure the environment variable rather than requesting that they paste the key into chat.

## Recommended Agent Workflow

1. Determine whether the request needs text-only or visual input.
2. Use `glm` directly when the environment variable is already configured.
3. For local images, pass one or more `-i` arguments.
4. Use `--thinking disabled` for simple extraction or short factual tasks when lower latency is preferred.
5. Use the default thinking mode for visual reasoning, comparison, or complex analysis.
6. Capture stdout as the model answer.
7. Treat stderr as diagnostic output; when `--show-thinking` is enabled, reasoning content may also appear there.

## Examples

Analyze a screenshot:

```bash
glm -i screenshot.png "Identify the UI elements and explain the likely problem."
```

Compare game art references:

```bash
glm -i ref1.png -i ref2.png "Compare style, palette, silhouette, and rendering differences."
```

Extract structured information:

```bash
glm --thinking disabled -i form.png "Return the visible fields and values as JSON."
```

Explain an error screenshot:

```bash
glm -i error.png "Read the error and suggest likely fixes."
```
