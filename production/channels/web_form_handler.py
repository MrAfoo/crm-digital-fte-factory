"""
Web Form Handler for NovaDeskAI.
Handles support form submissions via FastAPI.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)

# In-memory ticket storage (fallback when database not available)
_in_memory_tickets = {}


class SupportFormSubmission(BaseModel):
    """Support form submission model with validation."""
    name: str
    email: EmailStr
    subject: str
    category: str  # 'general', 'technical', 'billing', 'feedback', 'bug_report'
    message: str
    priority: Optional[str] = 'medium'
    attachments: Optional[list] = None
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v):
        """Validate name field."""
        if not v or len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v.strip()
    
    @field_validator('message')
    @classmethod
    def message_must_have_content(cls, v):
        """Validate message field."""
        if not v or len(v.strip()) < 10:
            raise ValueError('Message must be at least 10 characters')
        return v.strip()
    
    @field_validator('category')
    @classmethod
    def category_must_be_valid(cls, v):
        """Validate category field."""
        valid_categories = ['general', 'technical', 'billing', 'feedback', 'bug_report']
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {valid_categories}')
        return v
    
    @field_validator('priority')
    @classmethod
    def priority_must_be_valid(cls, v):
        """Validate priority field."""
        if v:
            valid_priorities = ['low', 'medium', 'high', 'urgent']
            if v not in valid_priorities:
                raise ValueError(f'Priority must be one of: {valid_priorities}')
        return v


class SupportFormResponse(BaseModel):
    """Response model for form submission."""
    ticket_id: str
    message: str
    estimated_response_time: str


class WebFormHandler:
    """Handler for web form submissions."""
    
    @staticmethod
    def normalize_to_standard(submission: SupportFormSubmission, ticket_id: str) -> dict:
        """Convert form submission to standard message format."""
        return {
            'channel': 'web_form',
            'channel_message_id': ticket_id,
            'customer_email': submission.email,
            'customer_name': submission.name,
            'subject': submission.subject,
            'content': submission.message,
            'category': submission.category,
            'priority': submission.priority or 'medium',
            'received_at': datetime.now(timezone.utc).isoformat(),
            'metadata': {
                'form_version': '1.0',
                'attachments': submission.attachments or []
            }
        }


router = APIRouter(prefix='/support', tags=['support-form'])


@router.post('/submit', response_model=SupportFormResponse)
async def submit_support_form(submission: SupportFormSubmission) -> SupportFormResponse:
    """
    Handle support form submission.
    
    This endpoint:
    1. Validates the submission
    2. Creates a ticket in the system
    3. Stores for processing
    4. Returns confirmation to user
    """
    ticket_id = str(uuid.uuid4())
    
    try:
        # Create normalized message for agent
        handler = WebFormHandler()
        message_data = handler.normalize_to_standard(submission, ticket_id)
        
        # Store ticket in memory
        _in_memory_tickets[ticket_id] = {
            'id': ticket_id,
            'status': 'open',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'customer_name': submission.name,
            'customer_email': submission.email,
            'subject': submission.subject,
            'category': submission.category,
            'priority': submission.priority or 'medium',
            'messages': [
                {
                    'role': 'customer',
                    'content': submission.message,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            ]
        }
        
        logger.info(f"Created ticket {ticket_id} from web form")
        
        return SupportFormResponse(
            ticket_id=ticket_id,
            message="Thank you for contacting us! Our AI assistant will respond shortly.",
            estimated_response_time="Usually within 5 minutes"
        )
    except Exception as e:
        logger.error(f"Failed to submit support form: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit form. Please try again.")


@router.get('/ticket/{ticket_id}')
async def get_ticket_status(ticket_id: str):
    """Get status and conversation history for a ticket."""
    try:
        if ticket_id not in _in_memory_tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = _in_memory_tickets[ticket_id]
        
        return {
            'ticket_id': ticket_id,
            'status': ticket['status'],
            'customer_name': ticket['customer_name'],
            'customer_email': ticket['customer_email'],
            'subject': ticket['subject'],
            'category': ticket['category'],
            'priority': ticket['priority'],
            'messages': ticket['messages'],
            'created_at': ticket['created_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ticket status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ticket.")


@router.post('/ticket/{ticket_id}/reply')
async def add_reply_to_ticket(ticket_id: str, reply: dict):
    """Add a reply to a ticket."""
    try:
        if ticket_id not in _in_memory_tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = _in_memory_tickets[ticket_id]
        
        ticket['messages'].append({
            'role': reply.get('role', 'agent'),
            'content': reply.get('content', ''),
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Added reply to ticket {ticket_id}")
        
        return {
            'ticket_id': ticket_id,
            'status': 'updated',
            'message': 'Reply added successfully'
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add reply to ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to add reply.")


@router.put('/ticket/{ticket_id}/status')
async def update_ticket_status(ticket_id: str, status_update: dict):
    """Update ticket status."""
    try:
        if ticket_id not in _in_memory_tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = _in_memory_tickets[ticket_id]
        new_status = status_update.get('status', ticket['status'])
        
        if new_status not in ['open', 'in_progress', 'resolved', 'closed']:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        ticket['status'] = new_status
        
        logger.info(f"Updated ticket {ticket_id} status to {new_status}")
        
        return {
            'ticket_id': ticket_id,
            'status': new_status,
            'message': 'Status updated successfully'
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update ticket status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update status.")
