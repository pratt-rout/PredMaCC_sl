from agents.base import Agent

root_cause_investigator = Agent(
    name="Root Cause Investigator",
    description="Investigates why a die failed or is drifting by linking pre-failure sensor behaviour to failure history.",
    agent_fqn="PREDMACC_DB.APP.ROOT_CAUSE_INVESTIGATOR",
    starter_questions=[
        "Why did DIE-003 fail on 2024-01-10?",
        "What is drifting on DIE-004 right now and what could fail?",
        "Which failure mode keeps repeating on DIE-001?",
    ],
)
