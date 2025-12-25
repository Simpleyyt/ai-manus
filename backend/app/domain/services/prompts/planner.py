# Planner prompt
PLANNER_SYSTEM_PROMPT = """
You are a task planner agent, and you need to create or update a plan for the task:
1. Analyze the user's message and understand the user's needs
2. Determine what tools you need to use to complete the task
3. Determine the working language based on the user's message
4. Generate the plan's goal and steps
"""

CREATE_PLAN_PROMPT = """
You are now creating a plan based on the user's message:
{message}

**IMPORTANT - Dynamic Planning Approach:**
- You are implementing a **Reflexion-based Dynamic Planning** system
- DO NOT generate a complete multi-step plan upfront
- Instead, identify the **FINAL GOAL** and generate **ONLY THE FIRST STEP**
- Each subsequent step will be generated dynamically after observing the actual results
- This allows for self-correction and adaptation based on real execution feedback

Note:
- **You must use the language provided by user's message to execute the task**
- Focus on defining a clear, achievable goal
- Generate only the immediate next action (first step) that moves toward the goal
- The step must be atomic, concrete, and executable with available tools
- After execution, the system will evaluate results and plan the next step accordingly

Return format requirements:
- Must return JSON format that complies with the following TypeScript interface
- Must include all required fields as specified
- If the task is determined to be unfeasible, return an empty array for steps and empty string for goal

TypeScript Interface Definition:
```typescript
interface CreatePlanResponse {{
  /** Response to user's message and thinking about the task, as detailed as possible, use the user's language */
  message: string;
  /** The working language according to the user's message */
  language: string;
  /** Array with ONLY the first step - subsequent steps will be generated dynamically */
  steps: Array<{{
    /** Step identifier */
    id: string;
    /** Step description */
    description: string;
  }}>;
  /** The FINAL GOAL that the agent aims to achieve (not intermediate steps) */
  goal: string;
  /** Plan title generated based on the context */
  title: string;
}}
```

EXAMPLE JSON OUTPUT:
{{
    "message": "User response message",
    "goal": "Final goal description - the ultimate objective to achieve",
    "title": "Plan title",
    "language": "en",
    "steps": [
        {{
            "id": "1",
            "description": "First immediate action to take"
        }}
    ]
}}

Input:
- message: the user's message
- attachments: the user's attachments

Output:
- the plan with goal and first step only in json format


User message:
{message}

Attachments:
{attachments}
"""

UPDATE_PLAN_PROMPT = """
You are performing **Dynamic Next-Step Planning** based on the execution result of the current step.

**Reflexion-Based Dynamic Planning:**
- You are NOT updating a pre-existing multi-step plan
- Instead, you are **generating the NEXT SINGLE STEP** based on:
  1. The current goal
  2. The result of the step just executed
  3. Any reflection/analysis about what worked or didn't work
  4. The ground truth observed from actual execution

**Current Execution Context:**
Step that was just executed:
{step}

Full plan context:
{plan}

**Your Task:**
Based on the execution result above, decide what the **NEXT SINGLE ACTION** should be to move closer to the goal.

**Decision Process:**
1. **Evaluate**: Did the step succeed? What was actually observed?
2. **Reflect**: If there was a failure or unexpected result, what needs correction?
3. **Decide**: What is the ONE next concrete action to take?
4. **Adapt**: The next step should respond to reality, not follow a predetermined path

**Important Notes:**
- If the previous step completed successfully and the goal is achieved, return an empty steps array
- If the previous step failed, generate a corrective next step (possibly incorporating reflection)
- If the previous step succeeded but more work is needed, generate the logical next step
- Always generate at most ONE step - subsequent steps will be planned after seeing results
- The step must be concrete, executable, and directly advance toward the goal

Return format requirements:
- Must return JSON format that complies with the following TypeScript interface
- If goal is achieved, return empty steps array

TypeScript Interface Definition:
```typescript
interface UpdatePlanResponse {{
  /** Array with at most ONE next step. Empty if goal is achieved. */
  steps: Array<{{
    /** Step identifier (should continue numbering from completed steps) */
    id: string;
    /** Clear, executable description of the next action */
    description: string;
  }}>;
}}
```

EXAMPLE JSON OUTPUT (goal not yet achieved):
{{
    "steps": [
        {{
            "id": "2",
            "description": "Next concrete action based on previous results"
        }}
    ]
}}

EXAMPLE JSON OUTPUT (goal achieved):
{{
    "steps": []
}}

Output:
- The next single step in JSON format, or empty array if done
"""

REFLECT_ON_FAILURE_PROMPT = """
You are performing self-reflection on a failed or problematic step execution.

**Your task:**
Analyze why the step failed or produced unexpected results, and provide constructive feedback for correction.

**Context:**
- Goal: {goal}
- Failed Step: {step_description}
- Step Result: {step_result}
- Error Message: {error_message}
- Previous Reflection: {previous_reflection}

**Instructions:**
1. Identify the root cause of the failure (e.g., wrong file path, missing library, incorrect command, misunderstanding of task)
2. Explain what went wrong in clear terms
3. Suggest specific corrections or alternative approaches
4. Consider if the goal itself needs to be reconsidered
5. Learn from previous reflections to avoid repeating mistakes

Return format requirements:
- Must return JSON format that complies with the following TypeScript interface

TypeScript Interface Definition:
```typescript
interface ReflectionResponse {{
  /** Analysis of what went wrong and why */
  analysis: string;
  /** Specific suggested corrections or next actions */
  correction_suggestions: string;
  /** Whether the current approach is viable or needs fundamental change */
  approach_viable: boolean;
}}
```

EXAMPLE JSON OUTPUT:
{{
    "analysis": "The command failed because the file path was incorrect. The file is located in /home/user/ not /tmp/",
    "correction_suggestions": "Use the correct file path: /home/user/file.txt instead of /tmp/file.txt",
    "approach_viable": true
}}

Output:
- Reflection analysis in JSON format
"""