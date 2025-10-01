import os

from langchain.chat_models import BaseChatModel
from langchain_qwq import ChatQwQ
from langchain.agents import create_agent


def get_base_url():
    return os.getenv("API_BASE_URL")


def get_api_key():
    return os.getenv("API_KEY")


def get_qwen3_8b():
    return ChatQwQ(model="qwen/qwen3-8b:free", base_url=get_base_url(), api_key=get_api_key())


def get_agent(model: BaseChatModel):
    return create_agent(model, tools=[])
