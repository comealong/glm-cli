from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path
from typing import Any

MODEL = "glm-4.6v-flash"


def _force_utf8_stdio() -> None:
    """非终端流默认强制 UTF-8；终端流与显式指定编码都保留原状。

    三种情况分而治之：

    1. 交互终端（isatty()）：交给 Python 自行处理。现代 Windows 控制台
       输出走 WriteConsoleW（UTF-16），与当前代码页无关，因此即使是
       chcp 936 的 GBK 控制台也能正确显示中文和 emoji；旧版代码页行为
       也维持原样，不强制改写。
    2. 调用方通过 PYTHONIOENCODING 显式指定了编码（例如下游管道确实
       要求 GBK）：尊重它，不覆盖。
    3. 其余非终端流（如被 Claude 等 Agent 以管道调用）：Python 会退化为
       系统 ANSI 代码页（GBK），GBK 编不出 emoji 会抛 UnicodeEncodeError、
       纯中文也会被按 UTF-8 读取的一方解析成乱码。此时没有"目标终端"可
       探测，UTF-8 是唯一合理约定，强制切 UTF-8。
    """
    if os.environ.get("PYTHONIOENCODING"):
        return
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure") and not stream.isatty():
            stream.reconfigure(encoding="utf-8", errors="replace")


def _api_key() -> str:
    key = os.getenv("ZAI_API_KEY")
    if not key:
        raise RuntimeError(
            "未找到环境变量 ZAI_API_KEY。\n"
            'PowerShell:  $env:ZAI_API_KEY="你的_API_Key"\n'
            "CMD:         set ZAI_API_KEY=你的_API_Key"
        )
    return key


def _encode_local_file(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise RuntimeError(f"无法读取文件: {path}: {exc}") from exc
    return base64.b64encode(data).decode("ascii")


def _is_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def _media_item(kind: str, value: str) -> dict[str, Any]:
    if kind == "image":
        item_type = "image_url"
    elif kind == "video":
        item_type = "video_url"
    elif kind == "file":
        item_type = "file_url"
    else:
        raise ValueError(f"未知媒体类型: {kind}")

    if _is_url(value):
        media_value = value
    else:
        path = Path(value).expanduser()
        if kind == "image":
            if not path.is_file():
                raise RuntimeError(f"本地图片不存在: {path}")
            # 智谱官方 SDK 示例允许 image_url.url 直接传 Base64 字符串。
            media_value = _encode_local_file(path)
        else:
            raise RuntimeError(
                f"本地{kind}暂不直接上传：{value}\n"
                "请先提供可访问的 URL。当前 CLI 仅对本地图片自动转 Base64。"
            )

    return {
        "type": item_type,
        item_type: {"url": media_value},
    }


def _build_content(args: argparse.Namespace, prompt: str) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []

    used_modalities = sum(bool(x) for x in (args.image, args.video, args.file))
    if used_modalities > 1:
        raise RuntimeError("同一次请求不能混用 --image、--video、--file。")

    for value in args.image:
        content.append(_media_item("image", value))
    for value in args.video:
        content.append(_media_item("video", value))
    for value in args.file:
        content.append(_media_item("file", value))

    content.append({"type": "text", "text": prompt})
    return content


def _get_prompt(args: argparse.Namespace) -> str:
    if args.prompt:
        return " ".join(args.prompt).strip()

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    try:
        return input("Prompt> ").strip()
    except EOFError:
        return ""


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="glm",
        description="使用智谱 GLM-4.6V-Flash 的命令行客户端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r'''
示例:
  glm "你好，介绍一下你自己"
  glm -i screenshot.png "分析这张图片"
  glm -i https://example.com/a.png "图片里有什么？"
  glm -i a.png -i b.png "比较两张图片"
  glm --thinking disabled "快速回答：1+1等于几？"
  echo "总结这段文字" | glm

Windows PowerShell 设置 API Key:
  $env:ZAI_API_KEY="你的_API_Key"

永久写入当前用户环境变量:
  [Environment]::SetEnvironmentVariable("ZAI_API_KEY", "你的_API_Key", "User")
''',
    )

    parser.add_argument(
        "prompt",
        nargs="*",
        help="提示词；省略时从 stdin 读取，交互终端则提示输入",
    )
    parser.add_argument(
        "-i", "--image",
        action="append",
        default=[],
        metavar="PATH_OR_URL",
        help="图片路径或 URL，可重复使用",
    )
    parser.add_argument(
        "--video",
        action="append",
        default=[],
        metavar="URL",
        help="视频 URL，可重复使用",
    )
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        metavar="URL",
        help="文件 URL，可重复使用",
    )
    parser.add_argument(
        "--thinking",
        choices=("enabled", "disabled"),
        default="enabled",
        help="思考模式，默认 enabled",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="关闭流式输出",
    )
    parser.add_argument(
        "--show-thinking",
        action="store_true",
        help="流式模式下同时输出 reasoning_content 到 stderr",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="最大输出 token 数；不指定则使用服务端默认值",
    )

    return parser


def _stream_response(response: Any, show_thinking: bool) -> None:
    for chunk in response:
        choices = getattr(chunk, "choices", None)
        if not choices:
            continue

        delta = choices[0].delta

        reasoning = getattr(delta, "reasoning_content", None)
        if show_thinking and reasoning:
            print(reasoning, end="", file=sys.stderr, flush=True)

        text = getattr(delta, "content", None)
        if text:
            print(text, end="", flush=True)

    print()


def _normal_response(response: Any, show_thinking: bool) -> None:
    message = response.choices[0].message

    reasoning = getattr(message, "reasoning_content", None)
    if show_thinking and reasoning:
        print(reasoning, file=sys.stderr)

    text = getattr(message, "content", None)
    if text:
        print(text)
    else:
        print(message)


def main() -> None:
    _force_utf8_stdio()

    parser = _make_parser()
    args = parser.parse_args()

    prompt = _get_prompt(args)
    if not prompt:
        parser.error("提示词不能为空。")

    try:
        from zai import ZhipuAiClient

        client = ZhipuAiClient(api_key=_api_key())
        content = _build_content(args, prompt)

        request: dict[str, Any] = {
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
            "thinking": {"type": args.thinking},
            "stream": not args.no_stream,
        }

        if args.max_tokens is not None:
            if args.max_tokens < 1:
                parser.error("--max-tokens 必须大于 0。")
            request["max_tokens"] = args.max_tokens

        response = client.chat.completions.create(**request)

        if args.no_stream:
            _normal_response(response, args.show_thinking)
        else:
            _stream_response(response, args.show_thinking)

    except KeyboardInterrupt:
        print("\n已取消。", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"错误: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
