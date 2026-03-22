import sys
from anthropic.types import TextBlock
from clients import claude_client, gemini_client

GEMINI_MODEL = "gemini-2.5-pro"
CLAUDE_MODEL = "claude-sonnet-4-6"

# ==========================================
# Specialized Workers
# ==========================================

def architect_design(task: str) -> str:
    """Gemini writes the initial architecture and design document."""
    print("\n[⏳] Gemini Architect is drafting the design...")
    prompt = f"""
    You are a Lead Software Architect. Create a detailed design document and step-by-step
    implementation plan for the following task. Do not write the final code, just the design.

    Task: {task}
    """
    response = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text or ""  # type: ignore[return-value]

def coder_implement(task: str, design_doc: str) -> str:
    """Claude writes the code strictly based on Gemini's design."""
    print("[⏳] Claude Coder is implementing the code...")
    prompt = f"""
    You are a Senior Software Engineer. Implement the code for the task below.
    You MUST strictly follow the provided Architecture Design Document.
    Only output the code and necessary instructions, no conversational filler.

    Original Task: {task}

    Architecture Design Document:
    {design_doc}
    """
    response = claude_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    block = response.content[0]
    assert isinstance(block, TextBlock)
    return block.text

def architect_review(task: str, design_doc: str, implementation: str) -> str:
    """Gemini reviews Claude's code against the original design."""
    print("[⏳] Gemini Architect is reviewing the code...")
    prompt = f"""
    You are a strict Lead Software Architect. Review the following code implementation.
    Does it accurately fulfill the Original Task? Does it follow your Design Document?
    Point out any bugs, security flaws, or deviations from the plan.

    Original Task: {task}

    Your Design Document:
    {design_doc}

    Engineer's Implementation:
    {implementation}
    """
    response = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text or ""  # type: ignore[return-value]


# ==========================================
# Manager Workflow
# ==========================================

def execute_full_workflow(user_prompt: str):
    print(f"=== Starting Workflow for Task: '{user_prompt}' ===\n")

    design_document = architect_design(user_prompt)
    code_implementation = coder_implement(user_prompt, design_document)
    review_feedback = architect_review(user_prompt, design_document, code_implementation)

    print("\n=== WORKFLOW COMPLETE ===")
    print("\n--- 1. DESIGN DOCUMENT ---")
    print(design_document[:500] + "\n...[truncated]...")
    print("\n--- 2. CODE IMPLEMENTATION ---")
    print(code_implementation)
    print("\n--- 3. ARCHITECT'S REVIEW ---")
    print(review_feedback)

    return {
        "design": design_document,
        "code": code_implementation,
        "review": review_feedback
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <task>", file=sys.stderr)
        sys.exit(1)
    task = sys.argv[1]
    _ = execute_full_workflow(task)


if __name__ == "__main__":
    main()
