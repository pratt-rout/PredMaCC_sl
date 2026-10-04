from agents.auto_router import auto_router
from agents.health_analyst import health_analyst
from agents.knowledge import maintenance_knowledge
from agents.root_cause import root_cause_investigator

AGENTS = {
    a.name: a
    for a in (auto_router, health_analyst, root_cause_investigator, maintenance_knowledge)
}
