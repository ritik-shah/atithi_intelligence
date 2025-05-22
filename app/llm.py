import os
from langchain_community.chat_models import ChatOpenAI

os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
os.environ["OPENAI_API_KEY"] = "sk-or-v1-xxxx"  # Replace with your key

OPENROUTER_MODEL = "mistralai/mixtral-8x7b-instruct"

def ask_llm(prompt: str) -> str:
    llm = ChatOpenAI(
        temperature=0.3,
        model=OPENROUTER_MODEL,
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key= "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",
    )
    return llm.predict(prompt)
