from agents.base import Agent

health_analyst = Agent(
    name="Die Health Analyst",
    description="Ask about die health, sensor readings, failures, downtime, maintenance cost and work orders. Can draw charts.",
    agent_fqn="PREDMACC_DB.APP.DIE_HEALTH_ANALYST",
    starter_questions=[
        "Which die has the most downtime and how many failures did it have?",
        "Which dies have open or overdue work orders?",
        "Show the anomaly rate by die as a chart.",
    ],
)
