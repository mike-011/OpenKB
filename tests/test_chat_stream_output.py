"""Regression tests: streamed chat text must be rendered exactly once.

SLM-Wiki f7468a4 removed a rich Live segment path in chat._run_turn that
duplicated streamed text on real terminals (cumulative Live redraws on
newline chunks). The pre-fix renderer is forced into terminal mode here so
the duplication is observable in a buffer.
"""

from __future__ import annotations

import asyncio
import io
from unittest.mock import MagicMock

import pytest
from agents import RawResponsesStreamEvent
from openai.types.responses import ResponseTextDeltaEvent
from rich.console import Console

from openkb.agent import chat


def _delta(text: str) -> RawResponsesStreamEvent:
    data = ResponseTextDeltaEvent.model_construct(
        delta=text,
        item_id="msg-1",
        output_index=0,
        content_index=0,
        logprobs=[],
        sequence_number=0,
        type="response.output_text.delta",
    )
    return RawResponsesStreamEvent(data=data, type="raw_response_event")


class _FakeResult:
    final_output = "Hello world"

    def __init__(self, chunks: list[str]):
        self._chunks = chunks

    async def stream_events(self):
        for chunk in self._chunks:
            yield _delta(chunk)

    def to_input_list(self):
        return []


@pytest.mark.parametrize("use_color", [True, False])
def test_streamed_text_rendered_exactly_once(monkeypatch, capsys, use_color):
    # Chunks carry newlines on purpose: the pre-fix Live renderer only
    # redrew on newline-containing chunks (cumulative redraw = duplication).
    chunks = ["Hello\n", "world"]
    monkeypatch.setattr(
        "agents.Runner.run_streamed",
        lambda *args, **kwargs: _FakeResult(chunks),
    )
    session = MagicMock()
    session.history = []
    rich_out = io.StringIO()
    monkeypatch.setattr(
        chat,
        "_make_rich_console",
        lambda: Console(file=rich_out, force_terminal=True, width=80),
    )

    asyncio.run(
        chat._run_turn(
            MagicMock(),
            session,
            "hi",
            MagicMock(),
            use_color=use_color,
        )
    )

    everything = capsys.readouterr().out + rich_out.getvalue()
    assert everything.count("Hello") == 1
    assert everything.count("world") == 1
