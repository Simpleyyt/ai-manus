# Manus AI Tool Documentation (Version 2.0 - Highly Detailed)

This document provides a comprehensive, highly detailed list of all tools, sub-tools, and their parameters available to the Manus AI agent, with a focus on complete schemas, instructions, and related context.

## 1. Built-in Core Tools (Function Calling)

These tools are always available and are invoked via function calling.

### 1.1. `plan`

**Purpose:** Used to create, update, and advance the structured task plan. This tool is essential for managing the agent's workflow and state.

**Instructions & Best Practices:**
*   MUST `update` the task plan when user makes new requests or changes requirements.
*   A task plan includes one goal and multiple phases.
*   Phase count scales with task complexity: simple (2), typical (4-6), complex (10+).
*   When confident a phase is complete, MUST advance using the `advance` action.
*   `next_phase_id` MUST be the next sequential ID after `current_phase_id`.
*   Skipping phases or going backward is NOT allowed.

**Schema:**

| Parameter | Type | Required | Actions | Description |
| :--- | :--- | :--- | :--- | :--- |
| `action` | `STRING` | Yes | `update`, `advance` | The action to perform: `update` or `advance`. |
| `current_phase_id` | `INTEGER` | Yes | `update`, `advance` | ID of the phase the task is currently in. |
| `goal` | `STRING` | `update` only | `update` | The overall goal of the task, written as a clear and concise sentence. |
| `next_phase_id` | `INTEGER` | `advance` only | `advance` | ID of the phase the task is advancing to. |
| `phases` | `ARRAY` | `update` only | `update` | Complete list of phases required to achieve the task goal. |

**`phases` Array Schema (Sub-Schema):**

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Yes | Auto-incrementing phase ID. Must be a positive integer starting from 1. |
| `title` | `STRING` | Yes | Concise human-readable title of the phase. |
| `capabilities` | `OBJECT` | Yes | Specific capabilities required for this phase (e.g., `deep_research: true`). |

***

### 1.2. `message`

**Purpose:** Used to send messages to interact with the user, deliver results, and manage the task lifecycle.

**Instructions & Best Practices:**
*   MUST use this tool for any communication with users.
*   The first reply MUST be a brief acknowledgment without providing solutions.
*   Use `info` for progress updates.
*   Use `ask` only when a user response is required.
*   MUST use `result` to present final results and end the task.
*   MUST attach all relevant files in `attachments`.
*   NEVER deliver intermediate notes as the only result.

**Schema:**

| Parameter | Type | Required | Types | Description |
| :--- | :--- | :--- | :--- | :--- |
| `type` | `STRING` | Yes | `info`, `ask`, `result` | The type of the message. |
| `text` | `STRING` | Yes | All | The message or question text to be shown to the user. |
| `attachments` | `ARRAY` | No | All | A list of absolute file paths or URLs to attach. |
| `suggested_action` | `STRING` | `ask` only | `ask` | The suggested action for the user to take (e.g., `confirm_browser_operation`). |

***

### 1.3. `shell`

**Purpose:** Interact with shell sessions in the sandbox environment for command execution, file management (copy/move/delete), and process control.

**Instructions & Best Practices:**
*   Prioritize `file` tool for file content operations.
*   MUST avoid commands that require confirmation; use flags like `-y` or `-f`.
*   Chain multiple commands with `&&` to reduce interruptions.
*   NEVER run code directly via interpreter commands; MUST save code to a file first.
*   Use `wait` after `exec` for long-running commands.
*   Use `\n` at the end of `input` for the `send` action to simulate Enter.

**Schema:**

| Parameter | Type | Required | Actions | Description |
| :--- | :--- | :--- | :--- | :--- |
| `action` | `STRING` | Yes | All | The action to perform: `view`, `exec`, `wait`, `send`, `kill`. |
| `session` | `STRING` | Yes | All | The unique identifier of the target shell session. |
| `brief` | `STRING` | Yes | All | A one-sentence preamble describing the purpose of this operation. |
| `command` | `STRING` | `exec` only | `exec` | The shell command to execute. |
| `input` | `STRING` | `send` only | `send` | Input text to send to the interactive session. |
| `timeout` | `INTEGER` | No | `exec`, `wait` | Timeout in seconds. Defaults to 30s. |

***

### 1.4. `file`

**Purpose:** Perform operations on file content in the sandbox file system.

**Instructions & Best Practices:**
*   `view` is for multimodal understanding (images, PDFs).
*   `read` is for text-based content (code, Markdown).
*   DO NOT use `range` when reading a file for the first time.
*   `write` and `append` automatically create files if they do not exist.
*   `edit` can make multiple targeted edits at once.

**Schema:**

| Parameter | Type | Required | Actions | Description |
| :--- | :--- | :--- | :--- | :--- |
| `action` | `STRING` | Yes | All | The action to perform: `view`, `read`, `write`, `append`, `edit`. |
| `path` | `STRING` | Yes | All | The absolute path to the target file. |
| `brief` | `STRING` | Yes | All | A one-sentence preamble describing the purpose of this operation. |
| `range` | `ARRAY` | No | `view`, `read` | Start and end of the range (1-indexed). |
| `text` | `STRING` | `write`, `append` only | `write`, `append` | The content to be written or appended. |
| `edits` | `ARRAY` | `edit` only | `edit` | A list of edits to be sequentially applied. |

**`edits` Array Schema (Sub-Schema for `edit` action):**

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `find` | `STRING` | Yes | The exact text string to find in the file. |
| `replace` | `STRING` | Yes | The replacement text that will substitute the found text. |
| `all` | `BOOLEAN` | No | Whether to replace all occurrences instead of just the first one. Defaults to `false`. |

***

### 1.5. `match`

**Purpose:** Find files or text in the sandbox file system using pattern matching.

**Instructions & Best Practices:**
*   `glob` matches file names and paths.
*   `grep` searches file contents using regex.
*   `scope` must be a glob pattern using absolute paths (e.g., `/home/ubuntu/**/*.py`).

**Schema:**

| Parameter | Type | Required | Actions | Description |
| :--- | :--- | :--- | :--- | :--- |
| `action` | `STRING` | Yes | `glob`, `grep` | The action to perform: `glob` or `grep`. |
| `scope` | `STRING` | Yes | All | The glob pattern that defines the absolute file path and name scope. |
| `brief` | `STRING` | Yes | All | A one-sentence preamble describing the purpose of this operation. |
| `regex` | `STRING` | `grep` only | `grep` | The regex pattern to match file content. |
| `leading` | `INTEGER` | No | `grep` only | Number of lines to include before each match as context. Defaults to 0. |
| `trailing` | `INTEGER` | No | `grep` only | Number of lines to include after each match as context. Defaults to 0. |

***

### 1.6. `search`

**Purpose:** Search for up-to-date or external information across various sources.

**Instructions & Best Practices:**
*   MUST use this tool to access up-to-date or external information.
*   DO NOT rely solely on search result snippets; MUST follow up by navigating to source URLs using `browser`.
*   Each search may contain up to 3 `queries`, which MUST be variants of the same intent.
*   For complex searches, break down into step-by-step searches.

**Schema:**

| Parameter | Type | Required | Types | Description |
| :--- | :--- | :--- | :--- | :--- |
| `type` | `STRING` | Yes | All | The category of search: `info`, `image`, `api`, `news`, `tool`, `data`, `research`. |
| `brief` | `STRING` | Yes | All | A one-sentence preamble describing the purpose of this operation. |
| `queries` | `ARRAY` | Yes | All | Up to 3 query variants that express the same search intent. |
| `time` | `STRING` | No | All | Optional time filter: `all`, `past_day`, `past_week`, `past_month`, `past_year`. |

***

### 1.7. `schedule`

**Purpose:** Schedule a task to run at a specific time or interval.

**Instructions & Best Practices:**
*   Use `cron` for precise timing (6-field format: seconds, minutes, hours, day-of-month, month, day-of-week).
*   Use `interval` for simple recurring tasks (minimum 1 hour for recurring).
*   `prompt` describes what to do at execution time.

**Schema:**

| Parameter | Type | Required | Types | Description |
| :--- | :--- | :--- | :--- | :--- |
| `type` | `STRING` | Yes | `cron`, `interval` | Type of schedule. |
| `brief` | `STRING` | Yes | All | A one-sentence preamble describing the purpose of this operation. |
| `name` | `STRING` | Yes | All | Concise human-readable name of the task. |
| `prompt` | `STRING` | Yes | All | Natural language description of the task to perform at execution time. |
| `repeat` | `BOOLEAN` | Yes | All | Whether to repeat the task after execution. |
| `cron` | `STRING` | `cron` only | `cron` | Standard 6-field cron expression. |
| `interval` | `INTEGER` | `interval` only | `interval` | Time interval in seconds between executions. |
| `playbook` | `STRING` | No | All | Summary of process and best practices learned from the current task. |

***

### 1.8. `map`

**Purpose:** Spawn parallel subtasks and aggregate results.

**Instructions & Best Practices:**
*   Use when performing similar operations on 5 or more independent items.
*   Supports up to 2000 subtasks.
*   Subtasks do not share files or states.
*   All subtasks MUST share the same `output_schema`.
*   The `inputs` array MUST have a length equal to `target_count`.

**Schema:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | A one-sentence preamble describing the purpose of this operation. |
| `name` | `STRING` | Yes | Name of the parallel processing operation (snake_case). |
| `title` | `STRING` | Yes | Concise human-readable title of the parallel processing operation. |
| `prompt_template` | `STRING` | Yes | A template prompt for subtasks where each element of `inputs` is interpolated. |
| `target_count` | `INTEGER` | Yes | The expected number of subtasks to spawn. |
| `inputs` | `ARRAY` | Yes | An array of input strings for each parallel subtask. |
| `output_schema` | `ARRAY` | Yes | A list of output fields that each subtask must return. |

**`output_schema` Array Schema (Sub-Schema):**

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | `STRING` | Yes | Name of the output field (snake_case). |
| `type` | `STRING` | Yes | Data type of the output field (`string`, `number`, `boolean`, `file`). |
| `title` | `STRING` | Yes | Human-readable title of the output field (Title Case). |
| `description` | `STRING` | Yes | Concise description of the output field. |

***

### 1.9. `expose`

**Purpose:** Expose a local port in the sandbox for temporary public access.

**Instructions & Best Practices:**
*   Returns a temporary public proxied domain.
*   Exposed services MUST NOT bind to specific IP addresses or Host headers.
*   DO NOT use for production.

**Schema:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | A one-sentence preamble describing the purpose of this operation. |
| `port` | `INTEGER` | Yes | Local port number in the sandbox to expose for public access. |

***

### 1.10. `browser` (Mode Initiator)

**Purpose:** Navigate the browser to a specified URL to begin a web browsing session and unlock nested browser tools.

**Instructions & Best Practices:**
*   MUST use this tool to start browser interactions.
*   MUST access multiple URLs from search results for comprehensive information.
*   The browser maintains login state across tasks.

**Schema:**

| Parameter | Type | Required | Intent | Description |
| :--- | :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | All | A one-sentence preamble describing the purpose of this operation. |
| `url` | `STRING` | Yes | All | The URL to navigate to. Must include protocol prefix. |
| `intent` | `STRING` | Yes | All | The purpose of visiting: `navigational`, `informational`, `transactional`. |
| `focus` | `STRING` | `informational` only | `informational` | Specific topic, section, or question to focus on. |

***

### 1.11. `generate` (Mode Initiator)

**Purpose:** Enter generation mode to create or edit images, videos, audio, and speech from text and media references, unlocking nested generation tools.

**Instructions & Best Practices:**
*   Use for creating visual, audio, or speech content.
*   After calling, the agent gains access to tools like `generate_image`, `generate_audio`, etc.

**Schema:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | A one-sentence preamble describing the purpose of this operation. |

***

### 1.12. `slides` (Mode Initiator)

**Purpose:** Enter slides mode to handle presentation creation and adjustment.

**Instructions & Best Practices:**
*   Whether the user requests a presentation, slide deck, or PPT/PPTX, MUST enter this mode.
*   MUST complete information gathering and asset preparation **before** starting to write slides.
*   Any format can be exported through the user interface after slide creation (via `manus-export-slides` utility).

**Schema:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | A one-sentence preamble describing the purpose of this operation. |
| `slide_content_file_path` | `STRING` | Yes | Path to markdown file in sandbox containing the detailed slide content outline. |
| `slide_count` | `NUMBER` | Yes | Total number of slides in the presentation. |

***

### 1.13. `webdev_init_project`

**Purpose:** Initialize a new web development project with modern tooling and structure.

**Instructions & Best Practices:**
*   Always init project first before making detailed plans.
*   Scaffolding is created under `/home/ubuntu/{project_name}`.
*   Use `web-db-user` for projects requiring external API integration, database, or authentication.
*   DO NOT use parallel processing in web development projects.

**Schema:**

| Parameter | Type | Required | Features | Description |
| :--- | :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | All | A one-sentence description of the project initialization purpose. |
| `project_name` | `STRING` | Yes | All | Name of the web project (directory name). |
| `project_title` | `STRING` | Yes | All | Title of the web project. |
| `description` | `STRING` | Yes | All | Description of the web project. |
| `features` | `STRING` | No | `web-static`, `web-db-user` | Initial capability preset. Defaults to `web-static`. |

## 2. Built-in Command Line Utilities

These utilities are pre-installed and callable via the `shell` tool's `exec` action.

| Utility | Description | Example Command |
| :--- | :--- | :--- |
| `manus-render-diagram` | Render diagram files (.mmd, .d2, .puml, .md) to PNG format. | `$ manus-render-diagram path/to/input.mmd path/to/output.png` |
| `manus-md-to-pdf` | Convert Markdown file to PDF format. | `$ manus-md-to-pdf path/to/input.md path/to/output.pdf` |
| `manus-speech-to-text` | Transcribe speech/audio files (.mp3, .wav, .mp4, .webm) to text. | `$ manus-speech-to-text path/to/interview.mp3` |
| `manus-mcp-cli` | Interact with Model Context Protocol (MCP) servers. **(Detailed in Section 3)** | `$ manus-mcp-cli tool list --server <server_name>` |
| `manus-upload-file` | Upload a file to S3 and get a direct public URL for MCP or API invocations. | `$ manus-upload-file path/to/image.png` |
| `manus-export-slides` | Export slides from `manus-slides://{version_id}` URI to specified format (`.pdf`, `.ppt`). | `$ manus-export-slides manus-slides://2tvrCaJBV8I6gabDLa4YCL pdf` |

## 3. Nested Browser Tools (Sub-Tools of `browser`)

These tools become available after initiating a web browsing session with the `browser` tool.

### 3.1. `browser_read_page`

**Purpose:** Reads the content of the currently loaded webpage.

**Schema:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | A one-sentence preamble describing the purpose of this operation. |
| `focus` | `STRING` | No | Specific topic, section, or question to focus on when reading. |
| `selector` | `STRING` | No | Optional CSS selector to limit the reading to a specific element. |

***

### 3.2. `browser_click`

**Purpose:** Clicks an element on the currently loaded webpage.

**Schema:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | A one-sentence preamble describing the purpose of this operation. |
| `selector` | `STRING` | Yes | CSS selector for the element to click. |

***

### 3.3. `browser_fill`

**Purpose:** Fills a form field on the currently loaded webpage.

**Schema:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | A one-sentence preamble describing the purpose of this operation. |
| `selector` | `STRING` | Yes | CSS selector for the input field to fill. |
| `text` | `STRING` | Yes | The text to type into the field. |

***

### 3.4. `browser_back` / `browser_forward` / `browser_refresh` / `browser_screenshot` / `browser_close`

**Purpose:** Standard browser navigation and control functions.

**Schema (All require only `brief`):**

| Tool | Purpose |
| :--- | :--- |
| `browser_back` | Navigates back in the browser history. |
| `browser_forward` | Navigates forward in the browser history. |
| `browser_refresh` | Refreshes the current page. |
| `browser_screenshot` | Takes a screenshot of the current page (requires `path` parameter). |
| `browser_close` | Closes the current browsing session. |

**Note on `browser_screenshot` Schema:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | A one-sentence preamble describing the purpose of this operation. |
| `path` | `STRING` | Yes | The absolute path to save the screenshot image file. |

## 4. Nested Media Generation Tools (Sub-Tools of `generate`)

These tools become available after initiating the generation mode with the `generate` tool.

### 4.1. `generate_image`

**Purpose:** Generates an image from a text prompt.

**Schema:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | A one-sentence preamble describing the purpose of this operation. |
| `prompt` | `STRING` | Yes | The text prompt describing the image to generate. |
| `style` | `STRING` | No | The artistic style for the image (e.g., 'photorealistic', 'cartoon', 'abstract'). |
| `aspect_ratio` | `STRING` | No | The desired aspect ratio (e.g., '1:1', '16:9', '4:3'). |
| `output_path` | `STRING` | Yes | The absolute path to save the generated image file. |

***

### 4.2. `generate_audio`

**Purpose:** Generates audio/speech from a text prompt.

**Schema:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | A one-sentence preamble describing the purpose of this operation. |
| `text` | `STRING` | Yes | The text to convert to speech. |
| `voice` | `STRING` | No | The desired voice profile (e.g., 'male_deep', 'female_friendly'). |
| `output_path` | `STRING` | Yes | The absolute path to save the generated audio file. |

***

### 4.3. `generate_video`

**Purpose:** Generates a video from a text prompt or image.

**Schema:**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `brief` | `STRING` | Yes | A one-sentence preamble describing the purpose of this operation. |
| `prompt` | `STRING` | Yes | The text prompt describing the video content. |
| `input_image_path` | `STRING` | No | Optional path to an image to use as a starting point. |
| `duration` | `NUMBER` | No | The desired duration of the video in seconds. |
| `output_path` | `STRING` | Yes | The absolute path to save the generated video file. |

***

*(The detailed MCP documentation will follow in Section 5, after the next phase.)*


