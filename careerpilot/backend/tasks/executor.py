# Task definitions and execution

from crewai import Task, Crew
from typing import Dict, Any, List
import os
import yaml
import traceback
from pathlib import Path

DEBUG = os.getenv("CAREERPILOT_DEBUG", "0").strip() in {"1", "true", "True", "yes", "on"}


def load_tasks_config() -> List[Dict[str, Any]]:
    """Load task configuration from tasks.yaml"""
    config_path = Path(__file__).parent.parent.parent / "config" / "tasks.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config.get("tasks", [])


def create_tasks_with_dependencies(agents: Dict[str, Any]) -> Dict[str, Task]:
    tasks_config = load_tasks_config()

    tasks = {}
    for cfg in tasks_config:
        agent = agents.get(cfg["agent"])
        if agent is None:
            raise ValueError(f"Task '{cfg.get('name')}' references unknown agent '{cfg.get('agent')}'")
        task = Task(
            description=cfg["description"],
            expected_output=cfg["expected_output"],
            agent=agent,
        )
        tasks[cfg["name"]] = task

    # Set up dependencies using context
    for cfg in tasks_config:
        depends_on = cfg.get("depends_on", [])
        if depends_on:
            tasks[cfg["name"]].context = [tasks[dep] for dep in depends_on if dep in tasks]

    return tasks


def _stringify_task_output(task_output: Any) -> str:
    
    for attr in ("raw", "output", "result", "final", "content"):
        if hasattr(task_output, attr):
            try:
                value = getattr(task_output, attr)
                if value is not None:
                    return str(value)
            except Exception:
                pass
    if isinstance(task_output, dict):
        for k in ("raw", "output", "result", "final", "content"):
            if k in task_output and task_output[k] is not None:
                return str(task_output[k])
    return str(task_output)


def _maybe_parse_json(text: str) -> Any:
    text = (text or "").strip()
    if not text:
        return text
    
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1]).strip()
        
        if text.lower().startswith("json"):
            
            parts = text.split("\n", 1)
            if len(parts) == 2 and parts[1].lstrip().startswith(("{", "[")):
                text = parts[1].strip()
    if not (text.startswith("{") or text.startswith("[")):
        return text
    import json
    try:
        return json.loads(text)
    except Exception:
        return text


def extract_task_outputs(result: Any, tasks: Dict[str, Task], tasks_config: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract outputs from CrewAI tasks, keyed by tasks.yaml output_key."""
    outputs: Dict[str, Any] = {}

    if DEBUG:
        print(f"[DEBUG] Result type: {type(result)}")
        print(f"[DEBUG] Result attributes: {dir(result)}")

    
    for cfg in tasks_config:
        name = cfg.get("name")
        output_key = cfg.get("output_key")
        if not name or not output_key:
            continue
        task = tasks.get(name)
        if task is None:
            continue

        task_out = getattr(task, "output", None)
        if task_out is None:
            continue

        raw_text = _stringify_task_output(task_out)
        outputs[output_key] = _maybe_parse_json(raw_text)

    
    if not outputs:
        if hasattr(result, "json_dict"):
            try:
                jd = result.json_dict
                if isinstance(jd, dict) and jd:
                    return jd
            except Exception:
                pass
        if hasattr(result, "output"):
            try:
                outputs["raw_output"] = str(result.output)
            except Exception:
                outputs["raw_output"] = str(result)
        else:
            outputs["raw_output"] = str(result)

    if DEBUG:
        print(f"[DEBUG] Final outputs keys: {list(outputs.keys())}")

    return outputs


def execute_pipeline(input_data: Dict) -> Dict[str, Any]:
    """Execute the full agent pipeline using CrewAI and return structured outputs"""
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        import crewai  # noqa: F401
    except Exception as e:
        return {
            "status": "error",
            "error": (
                "CrewAI is not available in the current Python environment. "
                "If you are using Python 3.14, install/use Python 3.12 or 3.13 and reinstall requirements."
            ),
            "details": str(e),
        }

    from agents.loader import create_agents

    try:
        agents = create_agents()
        tasks = create_tasks_with_dependencies(agents)
        tasks_config = load_tasks_config()

        crew = Crew(
            agents=list(agents.values()),
            tasks=list(tasks.values()),
            verbose=True
        )

        if DEBUG:
            print(f"[DEBUG] Starting crew kickoff with {len(tasks)} tasks")
            print(f"[DEBUG] Task config: {[t['name'] for t in tasks_config]}")

        result = crew.kickoff(inputs=input_data)

        if DEBUG:
            print(f"[DEBUG] Crew kickoff completed, result type: {type(result)}")

        # Extract outputs from crew result
        outputs = extract_task_outputs(result, tasks, tasks_config)

        if DEBUG:
            print(f"[DEBUG] Extracted outputs: {list(outputs.keys())}")

        return {
            "status": "completed",
            "outputs": outputs,
            "raw_result": str(result)
        }
    except Exception as e:
        if DEBUG:
            print(f"[DEBUG] Exception: {str(e)}")
            traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }