from __future__ import annotations

import tiktoken
import os
from openai import AzureOpenAI

MODELS_2_TOKEN_LIMITS = {
    "gpt-35-turbo": 4000,
    "gpt-3.5-turbo": 4000,
    "gpt-35-turbo-16k": 16000,
    "gpt-3.5-turbo-16k": 16000,
    "gpt-4": 8100,
    "gpt-4-32k": 32000,
    "gpt-4v": 128000,
}


AOAI_2_OAI = {"gpt-35-turbo": "gpt-3.5-turbo", "gpt-35-turbo-16k": "gpt-3.5-turbo-16k", "gpt-4v": "gpt-4-turbo-vision"}


def get_token_limit(model_id: str) -> int:
    if model_id not in MODELS_2_TOKEN_LIMITS:
        raise ValueError(f"Expected model gpt-35-turbo and above. Received: {model_id}")
    return MODELS_2_TOKEN_LIMITS[model_id]


def num_tokens_from_messages(message: dict[str, str], model: str) -> int:
    """
    Calculate the number of tokens required to encode a message.
    Args:
        message (dict): The message to encode, represented as a dictionary.
        model (str): The name of the model to use for encoding.
    Returns:
        int: The total number of tokens required to encode the message.
    Example:
        message = {'role': 'user', 'content': 'Hello, how are you?'}
        model = 'gpt-3.5-turbo'
        num_tokens_from_messages(message, model)
        output: 11
    """

    encoding = tiktoken.encoding_for_model(get_oai_chatmodel_tiktok(model))
    num_tokens = 2  # For "role" and "content" keys
    for key, value in message.items():
        if isinstance(value, list):
            for v in value:
                # TODO: Update token count for images https://github.com/openai/openai-cookbook/pull/881/files
                if isinstance(v, str):
                    num_tokens += len(encoding.encode(v))
        else:
            num_tokens += len(encoding.encode(value))
    return num_tokens


def get_oai_chatmodel_tiktok(aoaimodel: str) -> str:
    message = "Expected Azure OpenAI ChatGPT model name"
    if aoaimodel == "" or aoaimodel is None:
        raise ValueError(message)
    if aoaimodel not in AOAI_2_OAI and aoaimodel not in MODELS_2_TOKEN_LIMITS:
        raise ValueError(message)
    return AOAI_2_OAI.get(aoaimodel) or aoaimodel

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-12-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")  # Your Azure OpenAI resource's endpoint value.
)

system_message = {"role": "system", "content": "You are a helpful assistant."}
max_response_tokens = 250
token_limit = 4096
conversation = []
conversation.append(system_message)

# 用户输入循环
while True:
    user_input = input("Q:")
    conversation.append({"role": "user", "content": user_input})
    
    # 检查是否超过令牌限制，如果是，则删除最早的历史对话消息
    while num_tokens_from_messages(conversation, "gpt-35-turbo-16k") > token_limit:
        del conversation[1]

    # 生成助手的回复
    response = client.chat.completions.create(
        model="gpt-35-turbo-16k",  # 模型 = "deployment_name".
        messages=conversation,
        temperature=0.7,
        max_tokens=max_response_tokens
    )

    # 将助手的回复添加到对话中并显示
    assistant_response = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": assistant_response})
    print("\n" + assistant_response + "\n")
