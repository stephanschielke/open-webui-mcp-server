"""
title: Opencode Zen Go Manifold Pipe
authors: https://github.com/stephanschielke (conversion to use with opencode zen)
authors: justinh-rahb and christian-taillon (+ modifications)
author_url: https://github.com/justinh-rahb
version: 0.4.0
required_open_webui_version: 0.3.17
license: MIT
"""

import os
import requests
import json
import time
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field
from open_webui.utils.misc import pop_system_message


class Pipe:
    class Valves(BaseModel):
        OPENCODE_API_KEY: str = Field(default="")

    def __init__(self):
        self.type = "manifold"
        self.id = "opencode-go"
        self.name = "opencode-go/"
        self.valves = self.Valves(
            **{"OPENCODE_API_KEY": os.getenv("OPENCODE_API_KEY", "")}
        )
        self.MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB per image

        # Model list cache
        self._models_cache: List[dict] = []
        self._models_cache_ts: float = 0.0
        self._models_cache_ttl_s: int = 300  # refresh every 5 minutes

    def _opencode_go_headers(self) -> dict:
        return {
            "x-api-key": self.valves.OPENCODE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def _fetch_models(self) -> List[dict]:
        # """
        # Fetch available models from the Anthropic API with a 5-minute cache.
        # Falls back to an empty list on failure (caller handles fallback).
        # """
        now = time.time()
        if (
                self._models_cache
                and (now - self._models_cache_ts) < self._models_cache_ttl_s
        ):
            return self._models_cache

        # r = requests.get(
        #     "https://api.anthropic.com/v1/models",
        #     headers=self._opencode_go_headers(),
        #     timeout=(3.05, 30),
        # )
        # if r.status_code != 200:
        #     raise Exception(f"HTTP Error {r.status_code}: {r.text}")
        #
        # data = r.json()
        # raw_models = data.get("data", data if isinstance(data, list) else [])
        #
        # def _make_name(model_id: str) -> str:
        #     # Strip snapshot date suffix (8 digits): "claude-haiku-4-5-20251001" -> "claude-haiku-4-5"
        #     import re
        #
        #     name = re.sub(r"-\d{8}$", "", model_id)
        #     # Restore dotted version: "claude-sonnet-4-6" -> "claude-sonnet-4.6"
        #     # Only treat trailing short numeric segments as version parts (not dates)
        #     parts = name.split("-")
        #     version_start = len(parts)
        #     for i in range(len(parts) - 1, -1, -1):
        #         if parts[i].isdigit() and len(parts[i]) <= 2:
        #             version_start = i
        #         else:
        #             break
        #     if version_start < len(parts):
        #         base = "-".join(parts[:version_start])
        #         version = ".".join(parts[version_start:])
        #         return f"{base}-{version}" if base else version
        #     return name
        #
        # models = [
        #     {"id": m["id"], "name": _make_name(m["id"])}
        #     for m in raw_models
        #     if m.get("id")
        # ]
        models = [
            {"id": "minimax-m2.7", "name": "minimax-m2.7"},
            {"id": "minimax-m2.5", "name": "minimax-m2.5"},
        ]
        models.sort(key=lambda x: x["id"])

        self._models_cache = models
        self._models_cache_ts = now
        return models

    def pipes(self) -> List[dict]:
        try:
            return self._fetch_models()
        except Exception as e:
            print(f"Failed to fetch opencode-go models: {e}")
            return []

    def process_image(self, image_data):
        """Process image data with size validation."""
        if image_data["image_url"]["url"].startswith("data:image"):
            mime_type, base64_data = image_data["image_url"]["url"].split(",", 1)
            media_type = mime_type.split(":")[1].split(";")[0]

            image_size = len(base64_data) * 3 / 4
            if image_size > self.MAX_IMAGE_SIZE:
                raise ValueError(
                    f"Image size exceeds 5MB limit: {image_size / (1024 * 1024):.2f}MB"
                )
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64_data,
                },
            }
        else:
            url = image_data["image_url"]["url"]
            response = requests.head(url, allow_redirects=True, timeout=(3.05, 30))
            content_length = int(response.headers.get("content-length", 0))
            if content_length > self.MAX_IMAGE_SIZE:
                raise ValueError(
                    f"Image at URL exceeds 5MB limit: {content_length / (1024 * 1024):.2f}MB"
                )
            return {"type": "image", "source": {"type": "url", "url": url}}

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        system_message, messages = pop_system_message(body["messages"])

        processed_messages = []
        total_image_size = 0

        for message in messages:
            processed_content = []
            if isinstance(message.get("content"), list):
                for item in message["content"]:
                    if item["type"] == "text":
                        processed_content.append({"type": "text", "text": item["text"]})
                    elif item["type"] == "image_url":
                        processed_image = self.process_image(item)
                        processed_content.append(processed_image)
                        if processed_image["source"]["type"] == "base64":
                            total_image_size += (
                                    len(processed_image["source"]["data"]) * 3 / 4
                            )
                            if total_image_size > 100 * 1024 * 1024:
                                raise ValueError(
                                    "Total size of images exceeds 100 MB limit"
                                )
            else:
                processed_content = [
                    {"type": "text", "text": message.get("content", "")}
                ]

            processed_messages.append(
                {"role": message["role"], "content": processed_content}
            )

        # Claude 4.x+ models reject requests with both temperature and top_p/top_k set.
        # Priority: temperature > top_p/top_k > default temperature.
        temperature = body.get("temperature")
        top_p = body.get("top_p")
        top_k = body.get("top_k")

        if temperature is not None:
            sampling_params = {"temperature": temperature}
        elif top_p is not None or top_k is not None:
            sampling_params = {}
            if top_p is not None:
                sampling_params["top_p"] = top_p
            if top_k is not None:
                sampling_params["top_k"] = top_k
        else:
            sampling_params = {"temperature": 0.8}

        payload = {
            "model": body["model"][body["model"].find(".") + 1:],
            "messages": processed_messages,
            "max_tokens": body.get("max_tokens", 4096),
            **sampling_params,
            "stop_sequences": body.get("stop", []),
            **({"system": str(system_message)} if system_message else {}),
            "stream": body.get("stream", False),
        }

        try:
            if body.get("stream", False):
                return self.stream_response(self._opencode_go_headers(), payload)
            else:
                return self.non_stream_response(self._opencode_go_headers(), payload)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return f"Error: Request failed: {e}"
        except Exception as e:
            print(f"Error in pipe method: {e}")
            return f"Error: {e}"

    def stream_response(self, headers, payload):
        url = "https://opencode.ai/zen/go/v1/messages"
        try:
            with requests.post(
                    url, headers=headers, json=payload, stream=True, timeout=(3.05, 60)
            ) as response:
                if response.status_code != 200:
                    raise Exception(
                        f"HTTP Error {response.status_code}: {response.text}"
                    )

                for line in response.iter_lines():
                    if not line:
                        continue
                    line = line.decode("utf-8")
                    if not line.startswith("data: "):
                        continue
                    try:
                        data = json.loads(line[6:])
                        if data["type"] == "content_block_start":
                            yield data["content_block"].get("text", "")
                        elif data["type"] == "content_block_delta":
                            yield data["delta"].get("text", "")
                        elif data["type"] == "message_stop":
                            break
                        elif data["type"] == "message":
                            for content in data.get("content", []):
                                if content["type"] == "text":
                                    yield content["text"]
                        time.sleep(0.01)
                    except json.JSONDecodeError:
                        print(f"Failed to parse JSON: {line}")
                    except KeyError as e:
                        print(f"Unexpected data structure: {e} | data: {data}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            yield f"Error: Request failed: {e}"
        except Exception as e:
            print(f"General error in stream_response: {e}")
            yield f"Error: {e}"

    def non_stream_response(self, headers, payload):
        url = "https://opencode.ai/zen/go/v1/messages"
        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=(3.05, 60)
            )
            if response.status_code != 200:
                raise Exception(f"HTTP Error {response.status_code}: {response.text}")
            res = response.json()
            return res["content"][0]["text"] if res.get("content") else ""
        except requests.exceptions.RequestException as e:
            print(f"Failed non-stream request: {e}")
            return f"Error: {e}"
