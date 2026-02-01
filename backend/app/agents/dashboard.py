from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List
from ..prompts import load_prompt

class Insight(BaseModel):
    summary: str = Field(description="Brief summary of the feedback/text")
    sentiment_score: int = Field(description="Sentiment score from 0 (negative) to 100 (positive)")
    sentiment_label: str = Field(description="Positive, Neutral, or Negative")
    risks: List[str] = Field(description="List of identified risks")

class DashboardAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
        self.parser = JsonOutputParser(pydantic_object=Insight)

        # Load system prompt from localized prompts
        system_prompt_template = load_prompt("dashboard", "system")

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt_template),
            ("human", "{text}")
        ])

        self.chain = self.prompt | self.llm | self.parser

    async def analyze(self, text: str):
        return await self.chain.ainvoke({
            "text": text,
            "format_instructions": self.parser.get_format_instructions()
        })
