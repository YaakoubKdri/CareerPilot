# CrewAI Integration - loads agents from YAML

import yaml
import os
from pathlib import Path
from crewai import Agent
from typing import Dict, Any, List

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def load_agents_config() -> List[Dict]:
    with open(CONFIG_DIR / "agents.yaml") as f:
        return yaml.safe_load(f)["agents"]


def create_agents() -> Dict[str, Agent]:
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

    agents_config = load_agents_config()
    agents = {}

    for cfg in agents_config:
        agents[cfg["name"]] = Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            verbose=True
        )

    return agents