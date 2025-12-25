# Reflexion and Dynamic Planning Implementation

## Overview
This update transforms the AI Manus agent system from traditional ReAct (Reason + Act) to **Reflexion-based Dynamic Planning** architecture.

## Key Changes

### 1. Architecture Shift
- **From**: Traditional ReAct with complete multi-step planning upfront
- **To**: Reflexion + Dynamic Planning (one step at a time, with self-correction)

### 2. Modified Files

#### `/backend/app/domain/models/plan.py`
- **Added**: `reflection: Optional[str]` field to `Step` model
- **Purpose**: Store self-reflection analysis when steps fail or produce unexpected results

#### `/backend/app/domain/services/flows/plan_act.py`
- **Added**: New state `AgentStatus.REFLECTING` for self-reflection phase
- **Modified**: Main execution loop to support new flow:
  - `PLANNING` → Generate goal + first step only
  - `EXECUTING` → Execute current step
  - `REFLECTING` → Analyze failures/problems (new)
  - `UPDATING` → Dynamically generate next step based on results
  - `SUMMARIZING` → Final summary
  - `COMPLETED` → Done
- **Added**: `reflection_history` list to track reflections and avoid repeating mistakes

#### `/backend/app/domain/services/agents/planner.py`
- **Added**: `reflect_on_failure()` method
  - Analyzes why a step failed
  - Provides correction suggestions
  - Stores reflection in step for future reference
- **Modified**: `update_plan()` method
  - Now generates only ONE next step dynamically
  - Removes all pending steps and adds new step based on current context
  - Implements true dynamic planning

#### `/backend/app/domain/services/prompts/planner.py`
- **Modified**: `CREATE_PLAN_PROMPT`
  - Now instructs LLM to generate ONLY first step + final goal
  - Emphasizes dynamic planning approach
- **Modified**: `UPDATE_PLAN_PROMPT`
  - Completely redesigned for dynamic next-step generation
  - Focuses on generating ONE next action based on execution results
- **Added**: `REFLECT_ON_FAILURE_PROMPT`
  - New prompt for self-reflection on failures
  - Generates analysis, corrections, and viability assessment

## New Execution Flow

```
1. PLANNING: Define goal + generate first step only
   ↓
2. EXECUTING: Execute the current step
   ↓
3. EVALUATING: Check execution result
   ↓
   → If failed/problematic → REFLECTING
   → If successful → UPDATING
   ↓
4. REFLECTING (if needed): Analyze failure, generate insights
   ↓
5. UPDATING: Generate next single step dynamically
   ↓
   → Loop back to EXECUTING
   ↓
6. SUMMARIZING: When all steps complete
   ↓
7. COMPLETED: Done
```

## Benefits

1. **Adaptive Planning**: Plans adapt based on actual execution results
2. **Self-Correction**: System learns from failures and adjusts approach
3. **No Wasted Planning**: Doesn't generate future steps that may become invalid
4. **Ground Truth**: Each step is planned with knowledge of what actually happened
5. **Memory of Mistakes**: Reflection history prevents repeating errors

## Example Scenario

**Traditional ReAct (Old)**:
```
Plan: 
  Step 1: Check file at /tmp/data.txt
  Step 2: Process the file
  Step 3: Save results

→ Step 1 fails (file not found)
→ Steps 2-3 become invalid
→ Agent might struggle to adapt
```

**Reflexion + Dynamic Planning (New)**:
```
Plan Goal: Process data file
Step 1: Check file at /tmp/data.txt

→ Execute Step 1 → Fails (file not found)
→ REFLECTING: "File doesn't exist at /tmp/data.txt, likely in /home/user/"
→ UPDATING: Generate Step 2: "Search for data.txt in /home/user/"
→ Execute Step 2 → Success (found at /home/user/data.txt)
→ UPDATING: Generate Step 3: "Process /home/user/data.txt"
→ And so on...
```

## Integration Notes

- All changes are backward compatible with existing session/repository system
- Reflection data is stored in Step model and persists in session
- Compact memory still works to keep context manageable
- No changes required to tools or external integrations

## Testing Recommendations

1. Test with tasks that typically fail on first attempt
2. Verify reflection messages are shown to users
3. Check that agent doesn't repeat the same mistake twice
4. Ensure dynamic planning generates appropriate next steps
5. Test that goal achievement is properly detected

