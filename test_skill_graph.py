from core.skill_graph import SkillGraph
from core.workflow_synth import WorkflowSynthesizer

print("Initializing Skill Graph...")
sg = SkillGraph()

print("Initializing Workflow Synthesizer...")
ws = WorkflowSynthesizer(sg)

print("Synthesizing workflow for 'Audit API security'")
workflow = ws.synthesize("Audit API security")

print("\nWorkflow Steps:")
for step in workflow.steps:
    print(f"  Step {step.step_id}: {step.skill_name} (parallel group {step.parallel_group})")

print(f"\nWorkflow Valid: {workflow.composition_valid}")
