from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List
from .knowledge import KnowledgeAgent

class ActionItem(BaseModel):
    title: str = Field(description="The actionable step title")
    priority: str = Field(description="Priority: high, medium, or low")
    assignee: str = Field(description="Suggested role or person to assign")
    dueDate: str = Field(description="Relative due date, e.g., 'Next Week'")

class Plan(BaseModel):
    actions: List[ActionItem]

class OrchestratorAgent:
    def __init__(self, knowledge_agent: KnowledgeAgent):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.knowledge_agent = knowledge_agent
        
        self.parser = JsonOutputParser(pydantic_object=Plan)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Central Brain of Sentio, an AI Change Management Architect.
            Task: Break the user goal down into specific, actionable steps following the ADKAR framework (Awareness, Desire, Knowledge, Ability, Reinforcement).
            
            Context provided:
            {context}
            
            {format_instructions}
            """),
            ("human", "User Goal: {goal}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    async def generate_plan(self, goal: str, project_id: str):
        # Step 1: Gather Information
        retrieval_result = await self.knowledge_agent.retrieve_context(goal, project_id)
        context = retrieval_result.get("context", "")
        
        # Step 2: Planning & Reasoning
        result = await self.chain.ainvoke({
            "goal": goal,
            "context": context,
            "format_instructions": self.parser.get_format_instructions()
        })
        
        # Step 3: Action Creation (Mock save to DB for now)
        # In a real app, we would save these to a database here.
        
        return result
