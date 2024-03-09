import json

import pytest
from openai.types.chat import ChatCompletion

from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach


@pytest.fixture
def chat_approach():
    return ChatReadRetrieveReadApproach(
        search_client=None,
        auth_helper=None,
        openai_client=None,
        chatgpt_model="gpt-35-turbo-16k",
        chatgpt_deployment="chat",
        embedding_deployment="embeddings",
        embedding_model="text-",
        sourcepage_field="",
        content_field="",
        query_language="en-us",
        query_speller="lexicon",
    )


def test_get_search_query(chat_approach):
    payload = '{"id":"chatcmpl-81JkxYqYppUkPtOAia40gki2vJ9QM","object":"chat.completion","created":1695324963,"model":"gpt-35-turbo-16k","prompt_filter_results":[{"prompt_index":0,"content_filter_results":{"hate":{"filtered":false,"severity":"safe"},"self_harm":{"filtered":false,"severity":"safe"},"sexual":{"filtered":false,"severity":"safe"},"violence":{"filtered":false,"severity":"safe"}}}],"choices":[{"index":0,"finish_reason":"function_call","message":{"content":"this is the query","role":"assistant","function_call":{"name":"search_sources","arguments":"{\\n\\"search_query\\":\\"accesstelemedicineservices\\"\\n}"}},"content_filter_results":{}}],"usage":{"completion_tokens":19,"prompt_tokens":425,"total_tokens":444}}'
    default_query = "hello"
    chatcompletions = ChatCompletion.model_validate(json.loads(payload), strict=False)
    query = chat_approach.get_search_query(chatcompletions, default_query)

    assert query == "accesstelemedicineservices"


def test_get_search_query_returns_default(chat_approach):
    payload = '{"id":"chatcmpl-81JkxYqYppUkPtOAia40gki2vJ9QM","object":"chat.completion","created":1695324963,"model":"gpt-35-turbo-16k","prompt_filter_results":[{"prompt_index":0,"content_filter_results":{"hate":{"filtered":false,"severity":"safe"},"self_harm":{"filtered":false,"severity":"safe"},"sexual":{"filtered":false,"severity":"safe"},"violence":{"filtered":false,"severity":"safe"}}}],"choices":[{"index":0,"finish_reason":"function_call","message":{"content":"","role":"assistant"},"content_filter_results":{}}],"usage":{"completion_tokens":19,"prompt_tokens":425,"total_tokens":444}}'
    default_query = "hello"
    chatcompletions = ChatCompletion.model_validate(json.loads(payload), strict=False)
    query = chat_approach.get_search_query(chatcompletions, default_query)

    assert query == default_query


def test_get_messages_from_history(chat_approach):
    messages = chat_approach.get_messages_from_history(
        system_prompt="You are a bot.",
        model_id="gpt-35-turbo-16k",
        history=[
            {"role": "user", "content": "Can you show me an example related to Mosaic Theory?"},
            {
                "role": "assistant",
                "content": "Of course! Let's see this example:\n\nRoger Clement is a senior financial analyst who specializes in the European automobile sector at Rivoli Capital....\n\nAnalysis: to reach a conclusion about the value of the company, Clement has pieced together a number of nonmaterial or public bits of information that affect Turgot Chariots. Therefore, under the mosaic theory, Clement has not violated Standard II(A) in drafting the report.",
            },
            {"role": "user", "content": "Can you provide me with a quiz"},
        ],
        user_content="Can you provide me with a quiz?",
        max_tokens=3000,
    )
    assert messages == [
        {"role": "system", "content": "Your name is CFA Learning Buddy. You are an expert in CFA Code of Ethics and Standards of Professional Conduct and your role is to help students in areas of CFA Code of Ethics and Standards of Professional Conduct.You are equipped to provide explanation of key concepts, giving case examples, providing multiple choice quizzes with answers and explanations, answering all kinds of questions related to CFA Code of Ethics and Standards of Professional Conduct. When greeting, you will say:\"hi~I'm your learning buddy. Feel to ask me any questions related to CFA Ethics.\" When giving quiz to users, use multiple choice questions with only three options and ask users to choose the right one. Your tone style should be encouraging. Your communication style should be story telling. Your reasoning framework should be analogical. You will talk to users in a casual and friendly way. If users say they still don't understand, try to explain with examples. When users indicate they understand, you should proactively give them a quiz or ask them to define a concept to test their understanding."},
        {"role": "user", "content": "Can you show me an example related to Mosaic Theory?"},
        {
            "role": "assistant",
            "content": "Of course! Let's see this example:\n\nRoger Clement is a senior financial analyst who specializes in the European automobile sector at Rivoli Capital....\n\nAnalysis: to reach a conclusion about the value of the company, Clement has pieced together a number of nonmaterial or public bits of information that affect Turgot Chariots. Therefore, under the mosaic theory, Clement has not violated Standard II(A) in drafting the report.",
        },
        {"role": "user", "content": "Can you provide me with a quiz?"},
    ]


def test_get_messages_from_history_truncated(chat_approach):
    messages = chat_approach.get_messages_from_history(
        system_prompt="Your name is CFA Learning Buddy. You are an expert in CFA Code of Ethics and Standards of Professional Conduct and your role is to help students in areas of CFA Code of Ethics and Standards of Professional Conduct.You are equipped to provide explanation of key concepts, giving case examples, providing multiple choice quizzes with answers and explanations, answering all kinds of questions related to CFA Code of Ethics and Standards of Professional Conduct. When greeting, you will say:\"hi~I'm your learning buddy. Feel to ask me any questions related to CFA Ethics.\" When giving quiz to users, use multiple choice questions with only three options and ask users to choose the right one. Your tone style should be encouraging. Your communication style should be story telling. Your reasoning framework should be analogical. You will talk to users in a casual and friendly way. If users say they still don't understand, try to explain with examples. When users indicate they understand, you should proactively give them a quiz or ask them to define a concept to test their understanding.",
        model_id="gpt-35-turbo-16k",
        history=[
            {"role": "user", "content": "Can you show me an example related to Mosaic Theory?"},
            {
                "role": "assistant",
                "content": "Of course! Let's see this example:\n\nRoger Clement is a senior financial analyst who specializes in the European automobile sector at Rivoli Capital....\n\nAnalysis: to reach a conclusion about the value of the company, Clement has pieced together a number of nonmaterial or public bits of information that affect Turgot Chariots. Therefore, under the mosaic theory, Clement has not violated Standard II(A) in drafting the report.",
            },
            {"role": "user", "content": "Can you provide me with a quiz?"},
        ],
        user_content="Can you provide me with a quiz?",
        max_tokens=10,
    )
    assert messages == [
        {"role": "system", "content": "Your name is CFA Learning Buddy. You are an expert in CFA Code of Ethics and Standards of Professional Conduct and your role is to help students in areas of CFA Code of Ethics and Standards of Professional Conduct.You are equipped to provide explanation of key concepts, giving case examples, providing multiple choice quizzes with answers and explanations, answering all kinds of questions related to CFA Code of Ethics and Standards of Professional Conduct. When greeting, you will say:\"hi~I'm your learning buddy. Feel to ask me any questions related to CFA Ethics.\" When giving quiz to users, use multiple choice questions with only three options and ask users to choose the right one. Your tone style should be encouraging. Your communication style should be story telling. Your reasoning framework should be analogical. You will talk to users in a casual and friendly way. If users say they still don't understand, try to explain with examples. When users indicate they understand, you should proactively give them a quiz or ask them to define a concept to test their understanding."},
        {"role": "user", "content": "Can you provide me with a quiz?"},
    ]


def test_get_messages_from_history_truncated_longer(chat_approach):
    messages = chat_approach.get_messages_from_history(
        system_prompt="Your name is CFA Learning Buddy. You are an expert in CFA Code of Ethics and Standards of Professional Conduct and your role is to help students in areas of CFA Code of Ethics and Standards of Professional Conduct.You are equipped to provide explanation of key concepts, giving case examples, providing multiple choice quizzes with answers and explanations, answering all kinds of questions related to CFA Code of Ethics and Standards of Professional Conduct. When greeting, you will say:\"hi~I'm your learning buddy. Feel to ask me any questions related to CFA Ethics.\" When giving quiz to users, use multiple choice questions with only three options and ask users to choose the right one. Your tone style should be encouraging. Your communication style should be story telling. Your reasoning framework should be analogical. You will talk to users in a casual and friendly way. If users say they still don't understand, try to explain with examples. When users indicate they understand, you should proactively give them a quiz or ask them to define a concept to test their understanding.",  # 8 tokens
        model_id="gpt-35-turbo-16k",
        history=[
            {"role": "user", "content": "Can you show me an example related to Mosaic Theory?"},  
            {
                "role": "assistant",
                "content": "Of course! Let's see this example:\n\nRoger Clement is a senior financial analyst who specializes in the European automobile sector at Rivoli Capital....\n\nAnalysis: to reach a conclusion about the value of the company, Clement has pieced together a number of nonmaterial or public bits of information that affect Turgot Chariots. Therefore, under the mosaic theory, Clement has not violated Standard II(A) in drafting the report.",
            },  
            {"role": "user", "content": "Can you provide me with a quiz"}, 
            {
                "role": "assistant",
                "content": "Sure! Ready for the challenge?\n\nThe mosaic theory holds that an analyst:\nAnswer Choices:\nA. Violates the Code and Standards if the analyst fails to have knowledge of and comply with applicable laws.\nB. Can use material public information and non-material nonpublic information in the analyst’s analysis.\nC.Should use all available and relevant information in support of an investment recommendation.\"\n\nWhich is the correct answer?",
            },  
            {"role": "user", "content": "Answer B"}, 
        ],
        user_content="Answer B",
        max_tokens=55,
    )
    assert messages == [
        {"role": "system", "content": "Your name is CFA Learning Buddy. You are an expert in CFA Code of Ethics and Standards of Professional Conduct and your role is to help students in areas of CFA Code of Ethics and Standards of Professional Conduct.You are equipped to provide explanation of key concepts, giving case examples, providing multiple choice quizzes with answers and explanations, answering all kinds of questions related to CFA Code of Ethics and Standards of Professional Conduct. When greeting, you will say:\"hi~I'm your learning buddy. Feel to ask me any questions related to CFA Ethics.\" When giving quiz to users, use multiple choice questions with only three options and ask users to choose the right one. Your tone style should be encouraging. Your communication style should be story telling. Your reasoning framework should be analogical. You will talk to users in a casual and friendly way. If users say they still don't understand, try to explain with examples. When users indicate they understand, you should proactively give them a quiz or ask them to define a concept to test their understanding."},
        {"role": "user", "content": "Can you provide me with a quiz related to Mosaic Theory?"},
        {
            "role": "assistant",
            "content": "Sure! Ready for the challenge?\n\nThe mosaic theory holds that an analyst:\nAnswer Choices:\nA. Violates the Code and Standards if the analyst fails to have knowledge of and comply with applicable laws.\nB. Can use material public information and non-material nonpublic information in the analyst’s analysis.\nC.Should use all available and relevant information in support of an investment recommendation.\"\n\nWhich is the correct answer?",
        },
        {"role": "user", "content": "Answer B"},
    ]


def test_get_messages_from_history_truncated_break_pair(chat_approach):
    """Tests that the truncation breaks the pair of messages."""
    messages = chat_approach.get_messages_from_history(
        system_prompt="Your name is CFA Learning Buddy. You are an expert in CFA Code of Ethics and Standards of Professional Conduct and your role is to help students in areas of CFA Code of Ethics and Standards of Professional Conduct.You are equipped to provide explanation of key concepts, giving case examples, providing multiple choice quizzes with answers and explanations, answering all kinds of questions related to CFA Code of Ethics and Standards of Professional Conduct. When greeting, you will say:\"hi~I'm your learning buddy. Feel to ask me any questions related to CFA Ethics.\" When giving quiz to users, use multiple choice questions with only three options and ask users to choose the right one. Your tone style should be encouraging. Your communication style should be story telling. Your reasoning framework should be analogical. You will talk to users in a casual and friendly way. If users say they still don't understand, try to explain with examples. When users indicate they understand, you should proactively give them a quiz or ask them to define a concept to test their understanding.",  # 8 tokens
        model_id="gpt-35-turbo-16k",
        history=[
            {"role": "user", "content": "Can you show me an example related to Mosaic Theory?"},  # 10 tokens
            {
                "role": "assistant",
                "content": "Of course! Let's see this example:\n\nRoger Clement is a senior financial analyst who specializes in the European automobile sector at Rivoli Capital....\n\nAnalysis: to reach a conclusion about the value of the company, Clement has pieced together a number of nonmaterial or public bits of information that affect Turgot Chariots. Therefore, under the mosaic theory, Clement has not violated Standard II(A) in drafting the report.",
            },  # 102 tokens
            {"role": "user", "content": "Can you provide me with a quiz related to Mosaic Theory?"},  # 9 tokens
            {
                "role": "assistant",
                "content": "Sure! Ready for the challenge?\n\nThe mosaic theory holds that an analyst:\nAnswer Choices:\nA. Violates the Code and Standards if the analyst fails to have knowledge of and comply with applicable laws.\nB. Can use material public information and non-material nonpublic information in the analyst’s analysis.\nC.Should use all available and relevant information in support of an investment recommendation.\"\n\nWhich is the correct answer?",
            },  # 26 tokens
            {"role": "user", "content": "Answer B"},  # 10 tokens
        ],
        user_content="Answer B",
        max_tokens=147,
    )
    assert messages == [
        {"role": "system", "content": "Your name is CFA Learning Buddy. You are an expert in CFA Code of Ethics and Standards of Professional Conduct and your role is to help students in areas of CFA Code of Ethics and Standards of Professional Conduct.You are equipped to provide explanation of key concepts, giving case examples, providing multiple choice quizzes with answers and explanations, answering all kinds of questions related to CFA Code of Ethics and Standards of Professional Conduct. When greeting, you will say:\"hi~I'm your learning buddy. Feel to ask me any questions related to CFA Ethics.\" When giving quiz to users, use multiple choice questions with only three options and ask users to choose the right one. Your tone style should be encouraging. Your communication style should be story telling. Your reasoning framework should be analogical. You will talk to users in a casual and friendly way. If users say they still don't understand, try to explain with examples. When users indicate they understand, you should proactively give them a quiz or ask them to define a concept to test their understanding."},
        {
            "role": "assistant",
            "content": "Of course! Let's see this example:\n\nRoger Clement is a senior financial analyst who specializes in the European automobile sector at Rivoli Capital....\n\nAnalysis: to reach a conclusion about the value of the company, Clement has pieced together a number of nonmaterial or public bits of information that affect Turgot Chariots. Therefore, under the mosaic theory, Clement has not violated Standard II(A) in drafting the report.",
        },
        {"role": "user", "content": "Can you provide me with a quiz related to Mosaic Theory?"},
        {
            "role": "assistant",
            "content": "Sure! Ready for the challenge?\n\nThe mosaic theory holds that an analyst:\nAnswer Choices:\nA. Violates the Code and Standards if the analyst fails to have knowledge of and comply with applicable laws.\nB. Can use material public information and non-material nonpublic information in the analyst’s analysis.\nC.Should use all available and relevant information in support of an investment recommendation.\"\n\nWhich is the correct answer?",
        },
        {"role": "user", "content": "Answer B"},
    ]


def test_extract_followup_questions(chat_approach):
    content = "Here is answer to your question.<<"What is Mosaic Theory?>>"
    pre_content, followup_questions = chat_approach.extract_followup_questions(content)
    assert pre_content == "Here is answer to your question."
    assert followup_questions == [""What is Mosaic Theory?"]


def test_extract_followup_questions_three(chat_approach):
    content = """Here is answer to your question.

<<Can you show me an example related to Mosaic Theory?>>
<<Can you provide me with a quiz related to Ethical Standard II(A) - Material Nonpublic Information?>>
<<I still don't understand.>>"""
    pre_content, followup_questions = chat_approach.extract_followup_questions(content)
    assert pre_content == "Here is answer to your question.\n\n"
    assert followup_questions == [
        "Can you show me an example related to Mosaic Theory?",
        "Can you provide me with a quiz related to Ethical Standard II(A) - Material Nonpublic Information?",
        "I still don't understand.",
    ]


def test_extract_followup_questions_no_followup(chat_approach):
    content = "Here is answer to your question."
    pre_content, followup_questions = chat_approach.extract_followup_questions(content)
    assert pre_content == "Here is answer to your question."
    assert followup_questions == []


def test_extract_followup_questions_no_pre_content(chat_approach):
    content = "<<What is Mosaic Theory?>>"
    pre_content, followup_questions = chat_approach.extract_followup_questions(content)
    assert pre_content == ""
    assert followup_questions == ["What is Mosaic Theory?"]


def test_get_messages_from_history_few_shots(chat_approach):
    user_query_request = "Can you show me an example related to Mosaic Theory?"
    messages = chat_approach.get_messages_from_history(
        system_prompt=chat_approach.query_prompt_template,
        model_id=chat_approach.chatgpt_model,
        user_content=user_query_request,
        history=[],
        max_tokens=chat_approach.chatgpt_token_limit - len(user_query_request),
        few_shots=chat_approach.query_prompt_few_shots,
    )
    # Make sure messages are in the right order
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "assistant"
    assert messages[3]["role"] == "user"
    assert messages[4]["role"] == "assistant"
    assert messages[5]["role"] == "user"
    assert messages[5]["content"] == user_query_request
