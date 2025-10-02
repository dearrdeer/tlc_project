import os
from dotenv import load_dotenv
from langchain.chat_models import BaseChatModel
from langchain_qwq import ChatQwQ
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent

load_dotenv()


def get_base_url():
    return os.getenv("API_BASE_URL")


def get_api_key():
    return os.getenv("API_KEY")


def get_qwen3_8b():
    return ChatQwQ(model="qwen/qwen3-8b", base_url=get_base_url(), api_key=get_api_key())


def get_deepseek_r1():
    return ChatDeepSeek(model="deepseek/deepseek-r1-0528-qwen3-8b:free", base_url=get_base_url(), api_key=get_api_key())


def get_agent(model: BaseChatModel):
    return create_agent(model, tools=[])
