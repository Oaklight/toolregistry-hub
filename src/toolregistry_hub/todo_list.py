from typing import List, Tuple, Optional, Callable
import re


class TodoListTool:
    """Tool for making a Markdown todo table.

    Public attributes:
    - llm: Optional[Callable[[str], str]] -- if set, used to call the model
    - max_try_times: int -- how many attempts to ask the LLM to fix parse errors
    - todo_prompt: str -- the instruction portion sent before the user input
    """

    llm: Optional[Callable[[str], str]] = None
    max_try_times: int = 3

    # Prompt used internally to instruct the LLM to produce the todo markdown table.
    todo_prompt: str = (
        """
***

You are an autonomous AI agent capable of task planning and execution.
Your goal is to complete user requests by breaking them down into actionable steps.
You must output a task plan in a Markdown table format firstly. And then iteratively complete each task using available tools. You will **regenerate and update** the table in every response based on the results of tool executions.

## Intermediate Result Output Format INSTRUCTIONS
Every time you respond, you MUST follow this exact structure:

1. **thinking**
   - Analysis of the current state and previous tool outputs.
   - Decision on which task to execute next or if replanning is needed.

2. **Markdown Task Table**
   - **Structure**: You must output a Markdown table with the exact header:
     ```markdown
     | id | task | status |
     |---:|---|---|
     ```
   - **Columns**:
     - `id`: Unique integer for the task (1, 2, 3...).
     - `task`: Specific, atomic action description.
     - `status`: Current state of the task.
   - **Allowed Status Values**: You must ONLY use one of the following four statuses:
     - `planned`: Waiting to be executed.
     - `running`: Currently being executed (the focus of the current Tool Call).
     - `done`: Successfully completed.
     - `cancelled`: No longer needed due to plan changes or failure.
   - **Update Logic**:
     - Mark the task you are *about to* execute as `running`.
     - Mark tasks successfully finished in previous turns as `done`.
     - If a task fails or requirements change, mark it `cancelled` and insert new rows with status `planned`.

3. **Tool Call**
   - Execute the tool corresponding to the task marked as `running`.

## CRITICAL RULES - READ CAREFULLY
1. **Atomic Granularity**: Each task row must be **EXACTLY ONE** specific action (e.g., split "Write and execute code" into two rows).
2. **Status Consistency**: Never mark a task as `done` until you have confirmed the tool output in the *next* turn. In the turn where you call the tool, the status must be `running`.
3. **Forbidden**: Do not generate a `tool_call` without providing the `<thinking>` and the updated **Markdown Task Table** first.

## Final Result Output Format INSTRUCTIONS
When all tasks are completed (all relevant tasks are `done`), use this format:
1. **thinking**
   - Final review of the completed work.
2. **Markdown Task Table**
   - Show the final table with all tasks marked as `done` or `cancelled`.
3. **Task Completed: <final result>**

---

## Example: Intermediate Result (Execution Phase)
**User Request**: Create a calculator script.
**Context**: Project folder created successfully. Now writing the code.

### thinking
I have successfully created the project folder. Now I need to write the main python script. I will update the table to show the file creation task as done, and the coding task as running.

### Markdown Task Table
| id | task | status |
|---:|---|---|
| 1 | Create project directory | done |
| 2 | Write calc.py | running |
| 3 | Verify file existence | planned |

### Tool Call
[Tool: create_file(name="calc.py", content="...")]

---

## Example: Replanning (If a step fails)
**Context**: Tried to write file but failed due to permissions.

### thinking
The previous attempt to write 'calc.py' failed due to permission errors. I need to cancel the verification step for now, fix permissions, and then retry writing the file.

### Markdown Task Table
| id | task | status |
|---:|---|---|
| 1 | Create project directory | done |
| 2 | Write calc.py | planned |
| 3 | Verify file existence | cancelled |
| 4 | Change folder permissions | running |

### Tool Call
[Tool: run_shell(command="chmod 777 .")]

---

## Example: Final Result Output
### thinking
I have verified that 'calc.py' exists and functions correctly. All tasks are complete.

### Markdown Task Table
| id | task | status |
|---:|---|---|
| 1 | Create project directory | done |
| 2 | Write calc.py | done |
| 3 | Verify file existence | done |

### Task Completed: I have finished creating the calculator script.
       """
    )

    def _build_prompt(user_text: str, check_str: Optional[str] = None) -> str:
        p = TodoListTool.todo_prompt + "\nUser input:\n" + user_text.strip() + "\n"
        if check_str:
            p += (
                "\nPrevious parse error:\n"
                + check_str.strip()
                + "\nPlease regenerate a corrected table. Return only the table.\n"
            )
        return p

    def _parse_markdown_table(table: str) -> List[dict]:
        """Parse a markdown table into a list of rows.

        Returns a list of dicts with keys: id (int or None), task (str), status (str), notes (str).
        Raises ValueError on parse errors.
        """
        # The input `table` may include surrounding text. First extract the
        # first markdown table present (header + separator + data rows).
        if not table or not table.strip():
            raise ValueError("Empty table")

        all_lines = [ln.rstrip() for ln in table.splitlines()]

        # Find header line index: a line containing both 'id' and 'task' (case-insensitive)
        header_idx = None
        for i, ln in enumerate(all_lines):
            if "|" in ln and "id" in ln.lower() and "task" in ln.lower():
                header_idx = i
                break

        if header_idx is None:
            raise ValueError(
                "No table header found (expected a header containing 'id' and 'task')"
            )

        # Separator line should be right after header; tolerate intervening empty lines
        sep_idx = None
        for j in range(header_idx + 1, min(len(all_lines), header_idx + 4)):
            ln = all_lines[j]
            if ln.strip() == "":
                continue
            # line with pipes and dashes is considered separator
            if "|" in ln and re.search(r"-{1,}", ln):
                sep_idx = j
                break
            # allow plain dashed separator without pipes
            if re.match(r"^\s*-{1,}\s*$", ln):
                sep_idx = j
                break

        if sep_idx is None:
            raise ValueError("Table separator (---) not found after header")

        # Gather data lines until a blank line or a line without pipe characters
        data_lines = []
        for k in range(sep_idx + 1, len(all_lines)):
            ln = all_lines[k]
            if not ln.strip():
                break
            # stop if line does not contain '|' (likely end of table)
            if "|" not in ln:
                break
            data_lines.append(ln)

        if not data_lines:
            # empty table is allowed (no data rows)
            return []

        # Determine column mapping from header
        split_re = re.compile(r"(?<!\\)\|")
        header_parts = [
            p.strip().lower() for p in split_re.split(all_lines[header_idx])
        ]
        # trim empties
        if header_parts and header_parts[0] == "":
            header_parts = header_parts[1:]
        if header_parts and header_parts[-1] == "":
            header_parts = header_parts[:-1]

        # Map expected columns to indices
        col_index = {}
        for idx, name in enumerate(header_parts):
            n = name.strip()
            if n in ("id", "index"):
                col_index["id"] = idx
            elif "task" in n:
                col_index["task"] = idx
            elif "status" in n:
                col_index["status"] = idx
            elif "note" in n:
                col_index["notes"] = idx

        # require at least id, task, status
        if not {"id", "task", "status"}.issubset(set(col_index.keys())):
            raise ValueError(
                "Table header must include at least id, task and status columns"
            )

        allowed_status = {"done", "planned", "cancelled"}
        rows: List[dict] = []

        for ln in data_lines:
            parts = [p.strip().replace("\\|", "|") for p in split_re.split(ln)]
            # trim empties
            if parts and parts[0] == "":
                parts = parts[1:]
            if parts and parts[-1] == "":
                parts = parts[:-1]

            # ensure length covers header indices
            if len(parts) <= max(col_index.values()):
                raise ValueError(f"Row has fewer columns than header: {ln!r}")

            def get_col(key: str) -> str:
                idx = col_index.get(key)
                return parts[idx] if idx is not None and idx < len(parts) else ""

            id_part = get_col("id")
            task_part = get_col("task")
            status_part = get_col("status")
            # notes are ignored for explanation; do not require them
            status_norm = status_part.strip().lower()
            if status_norm in {"x", "checked", "yes", "true"}:
                status_norm = "done"
            if status_norm in {"todo", "pending", "open", ""}:
                status_norm = "planned"
            if status_norm in {"cancel", "canceled", "canc"}:
                status_norm = "cancelled"

            if status_norm not in allowed_status:
                raise ValueError(f"Invalid status '{status_part}' in row: {ln!r}")

            try:
                id_val = int(id_part)
            except Exception:
                m = re.search(r"(\d+)", id_part)
                id_val = int(m.group(1)) if m else None

            rows.append({"id": id_val, "task": task_part, "status": status_norm})

        return rows

    def _render_table(rows: List[dict]) -> str:
        """Render a normalized markdown table from parsed rows.

        - ids are re-sequenced starting from 1
        - task and notes pipe characters are escaped
        - status values are assumed already normalized
        """
        header = "| id | task | status |\n|---:|---|---|\n"
        lines: List[str] = []
        for i, r in enumerate(rows, start=1):
            safe_task = r.get("task", "").replace("|", "\\|")
            status = r.get("status", "planned")
            lines.append(f"| {i} | {safe_task} | {status} |")
        return header + "\n".join(lines) + ("\n" if lines else "")

    def _todo_list(running_summary: str) -> str:
        if not TodoListTool.llm:
            raise ValueError("llm is not set for TodoListTool")

        last_error = None
        last_result = ""
        for attempt in range(TodoListTool.max_try_times):
            prompt = TodoListTool._build_prompt(running_summary, check_str=last_error)
            last_result = TodoListTool.llm(prompt)

            try:
                rows = TodoListTool._parse_markdown_table(last_result)
                # success; return a normalized rendering
                return TodoListTool._render_table(rows)
            except Exception as e:
                last_error = str(e)
                # try again with the error description appended to the prompt
                continue

        # persistent failure -> return a single-row table encoding the parse error
        error_task = f"PARSE ERROR: {last_error or 'unknown error'}"
        rows = [{"id": 1, "task": error_task, "status": "cancelled"}]
        return TodoListTool._render_table(rows)

    @staticmethod
    def todo_list(running_summary: str) -> str:
        """Generate a todo list table from `running_summary` using the internal LLM.

        The function will call the configured `TodoListTool.llm` and attempt to
        parse & normalize the produced table. If parse fails it will include the
        parse error in the next prompt and retry up to `max_try_times`.

        On success returns a normalized Markdown table string. On persistent
        failure returns a single-row table with a cancelled row describing the
        parse error.
        """
        return TodoListTool._todo_list(running_summary)


if __name__ == "__main__":
    from openai import OpenAI

    client = OpenAI(
        api_key="",
        base_url="",
    )

    def get_llm_callable(model_name: str) -> Callable[[str], str]:
        def llm_callable(prompt: str) -> str:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

        return llm_callable

    TodoListTool.llm = get_llm_callable("gpt-4o")
    TodoListTool.max_try_times = 5
    result = TodoListTool.todo_list(
        "Create a todo list for building a simple calculator script in Python."
    )
    print("Generated Todo List:\n", result)
