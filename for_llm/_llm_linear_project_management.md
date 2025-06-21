# LLM Linear Project Management Guide
# Last Updated: 2025-06-19T10:30:00Z

**AUDIENCE:** For LLMs (Claude, Grok, ChatGPT, etc.) - Linear MCP integration and project management standards

## Overview

This guide provides comprehensive instructions for using Linear MCP (Model Context Protocol) server to manage projects, issues, and tasks through natural language interactions. Linear MCP enables AI agents to interact with Linear's project management platform securely and efficiently.

## Linear MCP Configuration

### Current Setup
Linear MCP is globally configured in the user's `C:\Users\jake_\.cursor\mcp.json` with **5 different connection methods** for maximum compatibility and redundancy:

1. **`linear-oauth`**: OAuth SSE server (may require login)
2. **`linear`**: mcp-remote method
3. **`linear-advanced`**: Third-party server (`@cosmix/linear-mcp-server`)
4. **`linear-api`**: Direct API key (most reliable)
5. **`linear-local`**: Local server backup

### Authentication
- **API Key**: Primary authentication for `linear-api` and `linear-local` methods.
- **OAuth Flow**: Used by `linear-oauth` and `linear` methods; may prompt for login on first use.
- **Token Management**: Automatically handled by MCP servers.
- **Workspace Access**: Requires proper Linear workspace permissions.

## Core Linear MCP Capabilities

### 1. Project Management
- **Create Projects**: `Create a new project called "Project Name" with description "Project Description"`
- **List Projects**: `Show me all projects` or `List projects in workspace`
- **Project Details**: `Get details for project "Project Name"`
- **Project Updates**: `Update project "Project Name" with new description`

### 2. Issue Management
- **Create Issues**: `Create a high-priority issue titled "Issue Title" with description "Issue Description"`
- **Search Issues**: `List all open issues assigned to me`
- **Update Issues**: `Update issue LIN-123 to mark it as complete`
- **Issue Details**: `Get details for issue LIN-123`

### 3. Comment System
- **Add Comments**: `Add comment to issue LIN-123: "Comment text"`
- **Read Comments**: `Show comments for issue LIN-123`
- **Comment Threads**: `Get comment thread for issue LIN-123`

### 4. Team Collaboration
- **List Members**: `Show team members`
- **Assign Issues**: `Assign issue LIN-123 to John Smith`
- **User Information**: `Get user details for john@example.com`

## Best Practices

### DO:
- Use descriptive, actionable issue titles
- Include comprehensive descriptions with technical details
- Set appropriate priority levels (High, Medium, Low)
- Leverage Linear's project structure (teams, projects, cycles)
- Use natural language commands - MCP translates to API calls
- Add relevant labels and tags for organization
- Include acceptance criteria in issue descriptions
- Use comments for progress updates and collaboration

### DON'T:
- Try to access data without proper permissions
- Create duplicate issues without checking existing ones
- Override Linear's built-in workflows unnecessarily
- Use vague or unclear issue descriptions
- Ignore priority levels and project organization
- Expect file operations (Linear MCP is data-focused)

## Common Workflows

### Project Setup Workflow
1. `Create a new project called "Project Name" with description "Project Description"`
2. `Create multiple issues for the project with priorities and descriptions`
3. `Assign issues to team members`
4. `Set up project milestones and cycles`

### Issue Management Workflow
1. `List all open issues in project "Project Name"`
2. `Update issue status to In Progress`
3. `Add progress comments to issues`
4. `Mark issues as complete when finished`

### Bulk Operations
- `Create 5 issues for project "Project Name" with different priorities`
- `List all overdue issues and their assignees`
- `Update all issues with label "bug" to high priority`

## Troubleshooting

### Authentication Issues
- If authentication fails, retry the command
- Ensure proper workspace permissions
- Check Linear workspace access

### Permission Errors
- Verify user has access to the workspace
- Check team membership and permissions
- Ensure proper project access rights

### Data Access Issues
- Confirm issue/project exists
- Check if user has read permissions
- Verify workspace selection

## Example Task Creation

### For Docker MCP Configuration Project:
```
Create a new project called "Docker Desktop MCP Configuration" with description "Fix MCP server port configurations and setup for memory, sequential-thinking, and puppeteer servers. Ensure all MCP services are properly accessible through correct port mappings and configuration."

Create 5 issues for this project:
1. "Fix Memory MCP Server Port Exposure" (High priority) - Container memory-mcp-server needs port mapping -p 23847:3000
2. "Fix Sequential-Thinking MCP Server Port Exposure" (High priority) - Container llm_only-sequential-thinking-mcp-1 needs port mapping -p 41293:3000  
3. "Deploy Puppeteer MCP Server" (Medium priority) - Create and start container with port mapping -p 58129:3000
4. "Update MCP.json Configuration" (High priority) - Update Cursor MCP config with new port mappings
5. "Verify All MCP Services Functional" (Medium priority) - End-to-end testing of all 7 MCP services
```

## Integration with Other Tools

### Docker Project Management
- Use Linear for tracking Docker container fixes
- Create issues for port mapping problems
- Track MCP server deployment status
- Document configuration changes

### Development Workflow
- Link issues to code changes
- Track technical debt and improvements
- Manage feature development cycles
- Coordinate team assignments

## Monitoring and Reporting

### Progress Tracking
- `Show status of all issues in project "Project Name"`
- `List completed issues this week`
- `Get project completion percentage`

### Team Coordination
- `Show all issues assigned to team member`
- `List overdue issues and assignees`
- `Get team workload distribution`

## Security Considerations

- Linear MCP uses OAuth for secure authentication
- All data access respects Linear's permission model
- No sensitive data is stored in MCP server
- Workspace access is controlled by Linear admin settings

## Limitations

- Cannot perform file operations (Linear is data-focused)
- Limited to user's workspace permissions
- Real-time notifications not available through MCP
- Some advanced Linear features may not be exposed

## Project Catalog Workflow

This section outlines the specific procedure for managing the "Project Catalog" project (`ID: 745a1f44-73f9-4030-8159-c0dd83154f91`).

1.  **Task Ingestion**: At the beginning of a work session, or when prompted, query Linear for all open issues within the "Project Catalog" project.
2.  **Local Sync**: Synchronize the open Linear issues with the `for_llm_todo.md` file. New tasks from Linear should be added to the todo list.
3.  **Execution**: Begin work on the tasks from the `for_llm_todo.md` list, prioritizing as indicated.
4.  **Completion**: Upon completing a task, mark the item as done (`- [x]`) in `for_llm_todo.md` and update the corresponding issue in Linear to a "Done" status.

This process ensures that the work done by the AI agent is always aligned with the project plan outlined in Linear.

## Updates and Maintenance

- Monitor Linear MCP server status and updates
- Keep mcp-remote package updated
- Test authentication periodically
- Verify workspace access after team changes

Remember: Linear MCP provides a powerful interface for project management automation. Use it to streamline workflows, improve task tracking, and enhance team collaboration through natural language interactions. 