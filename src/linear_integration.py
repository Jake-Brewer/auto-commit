"""Linear integration module for auto-commit.

This module provides a simplified interface to Linear operations
using the MCP Linear OAuth functions.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def create_linear_issue(issue_data: Dict[str, Any]) -> str:
    """Create a Linear issue and return the issue ID.
    
    Args:
        issue_data: Dictionary containing issue creation data
        
    Returns:
        The created issue ID
        
    Raises:
        Exception: If issue creation fails
    """
    try:
        # Import the MCP function at runtime to avoid circular imports
        from mcp_linear_oauth_create_issue import mcp_linear_oauth_create_issue
        
        result = mcp_linear_oauth_create_issue(**issue_data)
        
        if result and 'id' in result:
            return result['id']
        else:
            raise Exception(f"Unexpected response format: {result}")
            
    except Exception as e:
        logger.error(f"Failed to create Linear issue: {e}")
        raise


def get_issue_comments(issue_id: str) -> List[Dict[str, Any]]:
    """Get comments for a Linear issue.
    
    Args:
        issue_id: The Linear issue ID
        
    Returns:
        List of comment dictionaries
        
    Raises:
        Exception: If fetching comments fails
    """
    try:
        # Import the MCP function at runtime
        from mcp_linear_oauth_list_comments import mcp_linear_oauth_list_comments
        
        result = mcp_linear_oauth_list_comments(issueId=issue_id)
        
        if isinstance(result, list):
            return result
        else:
            logger.warning(f"Unexpected comments format for issue {issue_id}: {result}")
            return []
            
    except Exception as e:
        logger.error(f"Failed to get comments for issue {issue_id}: {e}")
        raise


def update_linear_issue(issue_id: str, update_data: Dict[str, Any]) -> bool:
    """Update a Linear issue.
    
    Args:
        issue_id: The Linear issue ID
        update_data: Dictionary containing update data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Import the MCP function at runtime
        from mcp_linear_oauth_update_issue import mcp_linear_oauth_update_issue
        
        update_data['id'] = issue_id
        result = mcp_linear_oauth_update_issue(**update_data)
        
        return result is not None
        
    except Exception as e:
        logger.error(f"Failed to update Linear issue {issue_id}: {e}")
        return False


def close_linear_issue(issue_id: str, team_id: str) -> bool:
    """Close a Linear issue by setting it to Done status.
    
    Args:
        issue_id: The Linear issue ID
        team_id: The team ID to get the correct Done status
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # First, get the Done status ID for this team
        from mcp_linear_oauth_get_issue_status import mcp_linear_oauth_get_issue_status
        
        done_status = mcp_linear_oauth_get_issue_status(
            query="Done", 
            teamId=team_id
        )
        
        if done_status and 'id' in done_status:
            # Update the issue to Done status
            return update_linear_issue(issue_id, {
                'stateId': done_status['id']
            })
        else:
            logger.error(f"Could not find Done status for team {team_id}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to close Linear issue {issue_id}: {e}")
        return False 