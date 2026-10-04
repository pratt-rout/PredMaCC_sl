from agents.base import Agent

maintenance_knowledge = Agent(
    name="Maintenance Knowledge Agent",
    description="Answers from the SOPs and maintenance guides indexed from the knowledge/ folder, with sources.",
    agent_fqn="PREDMACC_DB.APP.MAINTENANCE_KNOWLEDGE_AGENT",
    starter_questions=[
        "What is the procedure for guide pin realignment?",
        "What should I do if die temperature goes above 70 C?",
        "How do I check the cushion seals?",
    ],
)
