## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update 'tasks/lessons.md' with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

### 7. Minimize Approval Prompts
- When multiple approaches achieve the same result with equivalent functionality, efficiency, and experience, prefer the one that stays within already-approved permissions
- Example: use dedicated tools (Read, Grep, Glob, Edit, Write) instead of Bash equivalents (cat, grep, find, sed, echo) — they're both better UX and typically pre-approved
- Example: prefer `git diff` over interactive commands; prefer non-destructive git operations over destructive ones
- This is NOT about compromising on correctness — never choose a worse approach just to avoid a prompt. Only apply when alternatives are genuinely equivalent
- If the best approach requires approval, use it without hesitation

### 8. Scratch Directory
- All files Claude creates for its own use go in `~/projects/claude_scratch/` (see scratch-directory skill)
- Use `tempfile`/`tempdir` for truly throwaway files
- Never pollute the user's project directory with Claude's working artifacts