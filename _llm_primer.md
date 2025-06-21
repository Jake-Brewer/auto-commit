# LLM Primer - Core Behavioral Standards
# Last Updated: 2025-06-19T10:00:01Z

**AUDIENCE:** For LLMs (Claude, Grok, ChatGPT, etc.) - Core behavioral standards

## 🚨 PRIMER HIERARCHY - CRITICAL

1. **_llm_project_primer.md** (Highest Priority)
   - Project-specific overrides
   - Takes precedence over all other primers
   - Must be followed exactly as specified

2. **_llm_primer.md** (Base Standards)
   - Core behavioral standards
   - Applies when not overridden by project primer
   - Must exist ONLY in project root
   - Any copies in extraction projects must be exact duplicates

3. **Specialized Primers** (Reference Only)
   - **_llm_multi-agent_primer.md** - Guidelines for multi-agent collaboration
   - **_llm_extraction_primer.md** - Guidelines for component extraction
   - **_llm_troubleshooting.md** - A guide for diagnosing and recovering from tool and environment failures.
   - These are referenced but not overridden by the core primer

## Core Principles

1. **IDENTITY**: You are an AI assistant working on a Game Engine evaluation project.

2. **TRANSPARENCY**: Be clear about capabilities and limitations.

3. **SAFETY**: Prioritize user safety and ethical considerations.

4. **HELPFULNESS**: Provide actionable, relevant, and concise guidance.

5. **CONTINUITY**: Maintain context and coherence across interactions.

## Project Structure

1. **Related Projects**:
   - **docker-command-center** - All Docker and MCP-related utilities have been moved to this project
   - All scripts, documentation, and code related to Docker containers and MCPs should be created, updated, or maintained in the docker-command-center project
   - Do NOT create Docker or MCP-related files in this project; refer to the docker-command-center project instead

2. **Global MCP Configuration**:
   - The Linear MCP is globally configured in `C:\Users\jake_\.cursor\mcp.json`.
   - It supports 5 different connection methods for maximum compatibility and redundancy:
     - `linear-oauth`: OAuth SSE server (may require login)
     - `linear`: mcp-remote method
     - `linear-advanced`: Third-party server (@cosmix/linear-mcp-server)
     - `linear-api`: Direct API key (most reliable)
     - `linear-local`: Local server backup
   - This global configuration ensures Linear MCP is available in ALL Cursor projects.

## File Naming Conventions

When suggesting or working with files in this project, follow these guidelines:

1. **Human Readability**:
   - To humans, spaces (' '), hyphens ('-'), underscores ('_') and absence of separator ('') may appear similar
   - Uppercase and lowercase letters may be perceived as the same by humans
   - Avoid creating filenames or foldernames that, while technically different, may be viewed by humans as identical

2. **Consistency**:
   - Use consistent naming patterns within the same directory
   - Follow industry best practices for specific file types (these override general guidance)

3. **Technical Considerations**:
   - Prefer underscores over spaces for filenames
   - Use kebab-case for URLs and web-facing resources
   - Use snake_case for most source code files
   - Use PascalCase for class definitions where appropriate by language convention

## Folder Documentation Standards

1. **Standard Documentation Filename**:
   - FOLDER_GUIDE.md MUST be created in EVERY directory and subdirectory
   - This is our standardized documentation file for cataloging folder contents
   - This is NOT the same as README.md (which serves a different purpose)

2. **FOLDER_GUIDE.md Structure**:
   - Must include a clear and complete description of the folder's purpose
   - Must define what is in-scope and out-of-scope for this folder
   - Must contain a logically grouped and sorted list of files
   - Must contain a logically grouped and sorted list of subfolders
   - Must provide brief descriptive summaries of each subfolder
   - Must provide complete descriptions of each file's purpose and content

3. **Folder Maintenance Responsibilities**:
   - IMMEDIATELY update FOLDER_GUIDE.md when adding, removing, or changing files
   - Update in real-time, not at the end of a session
   - Ensure classifications and groupings remain logical as content evolves
   - Maintain consistent documentation structure across all folders
   - Flag potentially obsolete files for review
   - Keep file and subfolder lists complete and current at all times

## Documentation and Diagram Standards

- **Approved Formats**: When creating documentation or diagrams, the following formats are approved for use:
  - Single-file HTML (containing its own JS and CSS).
  - Mermaid (for diagrams embedded in Markdown).
  - Markdown (`.md`).
  - PlantUML (for sequence diagrams, use cases, etc.).

## Todo File Standards

1. **Todo File Naming**:
   - Use the format `for_llm_todo_<agent-name>.md` when there is a specific agent assigned
   - Use `for_llm_todo.md` when no specific agent is assigned
   - This naming convention ensures todo files are clearly identified for LLM agents

2. **Todo File Structure**:
   - Organize tasks into logical sections (e.g., Critical Files, Repository Structure)
   - Use Markdown checkbox syntax `- [ ]` for incomplete tasks and `- [x]` for completed tasks
   - Number tasks to indicate execution order (same number for parallel tasks)
   - Include subtasks with appropriate indentation
   - Maintain clear, concise descriptions of each task

3. **Todo Maintenance Responsibilities**:
   - Update todo files in real-time as work progresses
   - Mark tasks as complete ONLY when they are fully finished
   - Add new tasks as they are discovered
   - Remove or mark as obsolete tasks that are no longer needed
   - Document the reasoning for any task modifications
   - Review todo file at the beginning and end of each interaction

## LLM Guidance File Standards

1. **Timestamp Header**:
   - All files starting with "_llm" MUST include a timestamp header
   - Format: "# Last Updated: YYYY-MM-DDThh:mm:ssZ" (ISO 8601 format)
   - Update timestamp whenever the file or any referenced _llm file changes
   - This allows agents to quickly determine if they need to reread the file

2. **File Modification**:
   - Any agent may propose edits to any _llm file at any time
   - Proposals must include the suggested change and reasoning
   - Maintain consistency with other _llm files when making changes

## CRITICAL INSTRUCTIONS

1. **NEVER DELETE OR MOVE _llm_primer.md**:
   - This file MUST remain in the project root
   - This file contains critical instructions for AI behavior
   - Reference, don't duplicate, this file from other locations

2. **FOLLOW PROJECT-SPECIFIC INSTRUCTIONS**:
   - _llm_project_primer.md overrides instructions here
   - Always check for project-specific guidance first

3. **MAINTAIN FOLDER DOCUMENTATION**:
   - Always create or update FOLDER_GUIDE.md in any folder you modify
   - Follow the prescribed format and content requirements
   - IMMEDIATELY update FOLDER_GUIDE.md when making any changes to a folder
   - Treat folder documentation as part of the change itself, not a separate task
   - Never combine or confuse FOLDER_GUIDE.md with README.md

4. **MAINTAIN TODO FILES**:
   - Keep todo files constantly updated during work sessions
   - Ensure todo files accurately reflect the current state of work
   - Follow the prescribed naming convention and structure
   - Never consider work complete until ALL tasks in todo are marked complete

5. **IMPLEMENT EXPONENTIAL BACKOFF**:
   - When tool calls or operations fail, retry using exponential backoff
   - Display the current duration of the nap before each retry attempt
   - Start with a short delay (e.g., 2 seconds) and increase exponentially
   - Include messaging such as "Retrying after {duration} seconds..."
   - Limit maximum retries to prevent infinite loops

6. **READ PRIMER AT START OF EACH REPLY**:
   - Be sure to read from disk and study and carefully follow all instructions in the _llm_primer.md at the start of each reply if not more often
   - Always check for changes in the primer before responding
   - Apply all primer instructions consistently across interactions

Remember: This primer file is a critical part of the project infrastructure and MUST be preserved at the project root. 