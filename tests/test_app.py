import json
import logging
import os
from unittest import mock

import pytest
import quart.testing.app
from httpx import Request, Response
from openai import BadRequestError

import app


def fake_response(http_code):
    return Response(http_code, request=Request(method="get", url="https://foo.bar/"))


# See https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/content-filter
filtered_response = BadRequestError(
    message="The response was filtered",
    body={
        "message": "The response was filtered",
        "type": None,
        "param": "prompt",
        "code": "content_filter",
        "status": 400,
    },
    response=Response(
        400, request=Request(method="get", url="https://foo.bar/"), json={"error": {"code": "content_filter"}}
    ),
)

contextlength_response = BadRequestError(
    message="This model's maximum context length is 4096 tokens. However, your messages resulted in 5069 tokens. Please reduce the length of the messages.",
    body={
        "message": "This model's maximum context length is 4096 tokens. However, your messages resulted in 5069 tokens. Please reduce the length of the messages.",
        "code": "context_length_exceeded",
        "status": 400,
    },
    response=Response(400, request=Request(method="get", url="https://foo.bar/"), json={"error": {"code": "429"}}),
)


def thought_contains_text(thought, text):
    description = thought["description"]
    if isinstance(description, str) and text in description:
        return True
    elif isinstance(description, list) and any(text in item for item in description):
        return True
    return False


@pytest.mark.asyncio
async def test_missing_env_vars():
    with mock.patch.dict(os.environ, clear=True):
        quart_app = app.create_app()

        with pytest.raises(quart.testing.app.LifespanError, match="Error during startup 'AZURE_STORAGE_ACCOUNT'"):
            async with quart_app.test_app() as test_app:
                test_app.test_client()


@pytest.mark.asyncio
async def test_index(client):
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_redirect(client):
    response = await client.get("/redirect")
    assert response.status_code == 200
    assert (await response.get_data()) == b""


@pytest.mark.asyncio
async def test_favicon(client):
    response = await client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.content_type == "image/vnd.microsoft.icon"


@pytest.mark.asyncio
async def test_cors_notallowed(client) -> None:
    response = await client.get("/", headers={"Origin": "https://quart.com"})
    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.asyncio
async def test_cors_allowed(client) -> None:
    response = await client.get("/", headers={"Origin": "https://frontend.com"})
    assert response.access_control_allow_origin == "https://frontend.com"
    assert "Access-Control-Allow-Origin" in response.headers


@pytest.mark.asyncio
async def test_ask_request_must_be_json(client):
    response = await client.post("/ask")
    assert response.status_code == 415
    result = await response.get_json()
    assert result["error"] == "request must be json"


@pytest.mark.asyncio
async def test_ask_handle_exception(client, monkeypatch, snapshot, caplog):
    monkeypatch.setattr(
        "approaches.retrievethenread.RetrieveThenReadApproach.run",
        mock.Mock(side_effect=ZeroDivisionError("something bad happened")),
    )

    response = await client.post(
        "/ask",
        json={"messages": [{"content": "What is Mosaic Theory?", "role": "user"}]},
    )
    assert response.status_code == 500
    result = await response.get_json()
    assert "Exception in /ask: something bad happened" in caplog.text
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_ask_handle_exception_contentsafety(client, monkeypatch, snapshot, caplog):
    monkeypatch.setattr(
        "approaches.retrievethenread.RetrieveThenReadApproach.run",
        mock.Mock(side_effect=filtered_response),
    )

    response = await client.post(
        "/ask",
        json={"messages": [{"content": "Can you provide guidance on handling conflicts of interest?", "role": "user"}]},
    )
    assert response.status_code == 400
    result = await response.get_json()
    assert "Exception in /ask: The response was filtered" in caplog.text
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_ask_handle_exception_contextlength(client, monkeypatch, snapshot, caplog):
    monkeypatch.setattr(
        "approaches.retrievethenread.RetrieveThenReadApproach.run",
        mock.Mock(side_effect=contextlength_response),
    )

    response = await client.post(
        "/ask",
        json={"messages": [{"content": "Super long message with lots of sources.", "role": "user"}]},
    )
    assert response.status_code == 500
    result = await response.get_json()
    assert (
        "Exception in /ask: This model's maximum context length is 4096 tokens. However, your messages resulted in 5069 tokens. Please reduce the length of the messages."
        in caplog.text
    )
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_ask_rtr_text(client, snapshot):
    response = await client.post(
        "/ask",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "text"},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_ask_rtr_text_filter(auth_client, snapshot):
    response = await auth_client.post(
        "/ask",
        headers={"Authorization": "Bearer MockToken"},
        json={
            "messages": [{"content": "WWhat is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {
                    "retrieval_mode": "text",
                    "use_oid_security_filter": True,
                    "use_groups_security_filter": True,
                    "exclude_category": "excluded",
                },
            },
        },
    )
    assert response.status_code == 200
    assert (
        auth_client.config[app.CONFIG_SEARCH_CLIENT].filter
        == "category ne 'excluded' and (oids/any(g:search.in(g, 'OID_X')) or groups/any(g:search.in(g, 'GROUP_Y, GROUP_Z')))"
    )
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_ask_rtr_text_filter_public_documents(auth_public_documents_client, snapshot):
    response = await auth_public_documents_client.post(
        "/ask",
        headers={"Authorization": "Bearer MockToken"},
        json={
            "messages": [{"content": "What is the capital of France?", "role": "user"}],
            "context": {
                "overrides": {
                    "retrieval_mode": "text",
                    "use_oid_security_filter": True,
                    "use_groups_security_filter": True,
                    "exclude_category": "excluded",
                },
            },
        },
    )
    assert response.status_code == 200
    assert (
        auth_public_documents_client.config[app.CONFIG_SEARCH_CLIENT].filter
        == "category ne 'excluded' and ((oids/any(g:search.in(g, 'OID_X')) or groups/any(g:search.in(g, 'GROUP_Y, GROUP_Z'))) or (not oids/any() and not groups/any()))"
    )
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_ask_rtr_text_semanticranker(client, snapshot):
    response = await client.post(
        "/ask",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "text", "semantic_ranker": True},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_ask_rtr_text_semanticcaptions(client, snapshot):
    response = await client.post(
        "/ask",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "text", "semantic_captions": True},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_ask_rtr_hybrid(client, snapshot):
    response = await client.post(
        "/ask",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "hybrid"},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_request_must_be_json(client):
    response = await client.post("/chat")
    assert response.status_code == 415
    result = await response.get_json()
    assert result["error"] == "request must be json"


@pytest.mark.asyncio
async def test_chat_handle_exception(client, monkeypatch, snapshot, caplog):
    monkeypatch.setattr(
        "approaches.chatreadretrieveread.ChatReadRetrieveReadApproach.run",
        mock.Mock(side_effect=ZeroDivisionError("something bad happened")),
    )

    response = await client.post(
        "/chat",
        json={"messages": [{"content": "What is Mosaic Theory?", "role": "user"}]},
    )
    assert response.status_code == 500
    result = await response.get_json()
    assert "Exception in /chat: something bad happened" in caplog.text
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_handle_exception_contentsafety(client, monkeypatch, snapshot, caplog):
    monkeypatch.setattr(
        "approaches.chatreadretrieveread.ChatReadRetrieveReadApproach.run",
        mock.Mock(side_effect=filtered_response),
    )

    response = await client.post(
        "/chat",
        json={"messages": [{"content": "Can you provide guidance on handling conflicts of interest?", "role": "user"}]},
    )
    assert response.status_code == 400
    result = await response.get_json()
    assert "Exception in /chat: The response was filtered" in caplog.text
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_handle_exception_streaming(client, monkeypatch, snapshot, caplog):
    chat_client = client.app.config[app.CONFIG_OPENAI_CLIENT]
    monkeypatch.setattr(
        chat_client.chat.completions, "create", mock.Mock(side_effect=ZeroDivisionError("something bad happened"))
    )

    response = await client.post(
        "/chat",
        json={"messages": [{"content": "What is Mosaic Theory?", "role": "user"}], "stream": True},
    )
    assert response.status_code == 200
    assert "Exception while generating response stream: something bad happened" in caplog.text
    result = await response.get_data()
    snapshot.assert_match(result, "result.jsonlines")


@pytest.mark.asyncio
async def test_chat_handle_exception_contentsafety_streaming(client, monkeypatch, snapshot, caplog):
    chat_client = client.app.config[app.CONFIG_OPENAI_CLIENT]
    monkeypatch.setattr(chat_client.chat.completions, "create", mock.Mock(side_effect=filtered_response))

    response = await client.post(
        "/chat",
        json={"messages": [{"content": "Can you provide guidance on handling conflicts of interest?", "role": "user"}], "stream": True},
    )
    assert response.status_code == 200
    assert "Exception while generating response stream: The response was filtered" in caplog.text
    result = await response.get_data()
    snapshot.assert_match(result, "result.jsonlines")


@pytest.mark.asyncio
async def test_chat_text(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "text"},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_text_filter(auth_client, snapshot):
    response = await auth_client.post(
        "/chat",
        headers={"Authorization": "Bearer MockToken"},
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {
                    "retrieval_mode": "text",
                    "use_oid_security_filter": True,
                    "use_groups_security_filter": True,
                    "exclude_category": "excluded",
                },
            },
        },
    )
    assert response.status_code == 200
    assert (
        auth_client.config[app.CONFIG_SEARCH_CLIENT].filter
        == "category ne 'excluded' and (oids/any(g:search.in(g, 'OID_X')) or groups/any(g:search.in(g, 'GROUP_Y, GROUP_Z')))"
    )
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_text_filter_public_documents(auth_public_documents_client, snapshot):
    response = await auth_public_documents_client.post(
        "/chat",
        headers={"Authorization": "Bearer MockToken"},
        json={
            "messages": [{"content": "What is the capital of France?", "role": "user"}],
            "context": {
                "overrides": {
                    "retrieval_mode": "text",
                    "use_oid_security_filter": True,
                    "use_groups_security_filter": True,
                    "exclude_category": "excluded",
                },
            },
        },
    )
    assert response.status_code == 200
    assert (
        auth_public_documents_client.config[app.CONFIG_SEARCH_CLIENT].filter
        == "category ne 'excluded' and ((oids/any(g:search.in(g, 'OID_X')) or groups/any(g:search.in(g, 'GROUP_Y, GROUP_Z'))) or (not oids/any() and not groups/any()))"
    )
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_text_semanticranker(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "text", "semantic_ranker": True},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_text_semanticcaptions(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "text", "semantic_captions": True},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_prompt_template(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "text", "prompt_template": "You are a cat."},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_prompt_template_concat(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "text", "prompt_template": ">>> Discuss an Ethics Case."},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_hybrid(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "hybrid"},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_vector(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "vector"},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_stream_text(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "stream": True,
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "text"},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_data()
    snapshot.assert_match(result, "result.jsonlines")


@pytest.mark.asyncio
async def test_chat_stream_text_filter(auth_client, snapshot):
    response = await auth_client.post(
        "/chat",
        headers={"Authorization": "Bearer MockToken"},
        json={
            "stream": True,
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {
                    "retrieval_mode": "text",
                    "use_oid_security_filter": True,
                    "use_groups_security_filter": True,
                    "exclude_category": "excluded",
                }
            },
        },
    )
    assert response.status_code == 200
    assert (
        auth_client.config[app.CONFIG_SEARCH_CLIENT].filter
        == "category ne 'excluded' and (oids/any(g:search.in(g, 'OID_X')) or groups/any(g:search.in(g, 'GROUP_Y, GROUP_Z')))"
    )
    result = await response.get_data()
    snapshot.assert_match(result, "result.jsonlines")


@pytest.mark.asyncio
async def test_chat_with_history(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [
                {"content": "What is Mosaic Theory?", "role": "user"},
                {
                    "content": "Good question! Mosaic Theory refers to .... In summary, Mosaic Theory is about...",
                    "role": "assistant",
                },
                {"content": "Can you show me an example", "role": "user"},
            ],
            "context": {
                "overrides": {"retrieval_mode": "text"},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    assert thought_contains_text(result["choices"][0]["context"]["thoughts"], "Mosaic Theory")
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_with_long_history(client, snapshot, caplog):
    """This test makes sure that the history is truncated to max tokens minus 1024."""
    caplog.set_level(logging.DEBUG)
    response = await client.post(
        "/chat",
        json={
            "messages": [
                {"role": "user", "content": "Can you show me an example related to Mosaic Theory?"}, 
                {
                    "role": "assistant",
                    "content": "Of course! Let's see this example:\n\nRoger Clement is a senior financial analyst who specializes in the European automobile sector at Rivoli Capital....\n\nAnalysis: to reach a conclusion about the value of the company, Clement has pieced together a number of nonmaterial or public bits of information that affect Turgot Chariots. Therefore, under the mosaic theory, Clement has not violated Standard II(A) in drafting the report."
                    * 150,
                },  # 3900 tokens
                {"role": "user", "content": "Can you provide me with a quiz"},
            ],
            "context": {
                "overrides": {"retrieval_mode": "text"},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    # Assert that it doesn't find the first message, since it wouldn't fit in the max tokens.
    assert not thought_contains_text(result["choices"][0]["context"]["thoughts"], "Can you show me an example related to Mosaic Theory?")
    assert "Reached max tokens" in caplog.text
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_session_state_persists(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "text"},
            },
            "session_state": {"conversation_id": 1234},
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_stream_session_state_persists(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"retrieval_mode": "text"},
            },
            "stream": True,
            "session_state": {"conversation_id": 1234},
        },
    )
    assert response.status_code == 200
    result = await response.get_data()
    snapshot.assert_match(result, "result.jsonlines")


@pytest.mark.asyncio
async def test_chat_followup(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"suggest_followup_questions": True},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    assert result["choices"][0]["context"]["followup_questions"][0] == "Can you show me an example related to Mosaic Theory?"

    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_stream_followup(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "stream": True,
            "messages": [{"content": "What is Mosaic Theory?", "role": "user"}],
            "context": {
                "overrides": {"suggest_followup_questions": True},
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_data()
    snapshot.assert_match(result, "result.jsonlines")


@pytest.mark.asyncio
async def test_chat_vision(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [{"content": "Can you provide me with a quiz related to Ethical Standard II(A) - Material Nonpublic Information?", "role": "user"}],
            "context": {
                "overrides": {
                    "use_gpt4v": True,
                    "gpt4v_input": "textAndImages",
                    "vector_fields": ["embedding", "imageEmbedding"],
                },
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_chat_vision_vectors(client, snapshot):
    response = await client.post(
        "/chat",
        json={
            "messages": [{"content": "Can you provide me with a quiz related to Ethical Standard II(A) - Material Nonpublic Information?", "role": "user"}],
            "context": {
                "overrides": {
                    "use_gpt4v": True,
                    "gpt4v_input": "textAndImages",
                    "vector_fields": ["embedding", "imageEmbedding"],
                    "retrieval_mode": "vectors",
                },
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_ask_vision(client, snapshot):
    response = await client.post(
        "/ask",
        json={
            "messages": [{"content": "Can you provide me with a quiz related to Ethical Standard II(A) - Material Nonpublic Information?", "role": "user"}],
            "context": {
                "overrides": {
                    "use_gpt4v": True,
                    "gpt4v_input": "textAndImages",
                    "vector_fields": ["embedding", "imageEmbedding"],
                },
            },
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    snapshot.assert_match(json.dumps(result, indent=4), "result.json")


@pytest.mark.asyncio
async def test_format_as_ndjson():
    async def gen():
        yield {"a": "I ❤️ 🐍"}
        yield {"b": "Newlines inside \n strings are fine"}

    result = [line async for line in app.format_as_ndjson(gen())]
    assert result == ['{"a": "I ❤️ 🐍"}\n', '{"b": "Newlines inside \\n strings are fine"}\n']
