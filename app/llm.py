import os
from langchain_community.chat_models import ChatOpenAI

# os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
# os.environ["OPENAI_API_KEY"] = "sk-or-v1-xxxx"  # Replace with your key

OPENROUTER_MODEL = "mistralai/mixtral-8x7b-instruct"

def ask_llm(prompt: str) -> str:
    llm = ChatOpenAI(
        temperature=0.3,
        model=OPENROUTER_MODEL,
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key= "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",
    )
    return llm.predict(prompt)
