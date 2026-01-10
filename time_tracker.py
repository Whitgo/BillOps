"""Time tracking module for passive time capture"""
from datetime import datetime
from dateutil import parser
import re


class TimeTracker:
    """Handles passive time tracking from various sources"""
    
    def __init__(self):
        self.client_patterns = {}
        self.matter_patterns = {}
    
    def capture_from_email(self, email_subject, email_body='', email_from=None, 
                          email_to=None, timestamp=None, duration_minutes=None):
        """
        Capture time from email activity
        
        Args:
            email_subject: Subject line of the email
            email_body: Body content of the email
            email_from: Sender email address
            email_to: Recipient email address
            timestamp: When the email was sent/received
            duration_minutes: Estimated time spent on email (optional)
        
        Returns:
            Dictionary with captured time information
        """
        # Parse timestamp
        if timestamp:
            if isinstance(timestamp, str):
                dt = parser.parse(timestamp)
            else:
                dt = timestamp
        else:
            dt = datetime.utcnow()
        
        # Estimate duration if not provided
        if not duration_minutes:
            # Simple heuristic: estimate based on email length
            word_count = len(email_body.split()) if email_body else 0
            # Average reading speed: ~200 words/min, writing: ~40 words/min
            # Assume 50% reading, 50% writing for estimation
            duration_minutes = max(6, word_count / 60)  # Minimum 6 minutes (0.1 hours)
        
        hours = duration_minutes / 60.0
        
        # Try to extract client/matter information from subject or body
        client_info = self._extract_client_matter_info(email_subject + ' ' + email_body)
        
        return {
            'source': 'email',
            'description': f"Email: {email_subject}",
            'hours': round(hours, 2),
            'date': dt.date().isoformat(),
            'source_reference': f"From: {email_from}, To: {email_to}",
            'suggested_matter_id': client_info.get('matter_id'),
            'suggested_client': client_info.get('client_name'),
            'timestamp': dt.isoformat()
        }
    
    def capture_from_calendar(self, event_title, event_description='', 
                             start_time=None, end_time=None, attendees=None):
        """
        Capture time from calendar events
        
        Args:
            event_title: Title of the calendar event
            event_description: Description/notes for the event
            start_time: Start time of the event (ISO format string or datetime)
            end_time: End time of the event (ISO format string or datetime)
            attendees: List of attendee email addresses
        
        Returns:
            Dictionary with captured time information
        """
        # Parse start and end times
        if isinstance(start_time, str):
            start_dt = parser.parse(start_time)
        else:
            start_dt = start_time or datetime.utcnow()
        
        if isinstance(end_time, str):
            end_dt = parser.parse(end_time)
        else:
            end_dt = end_time or start_dt
        
        # Calculate duration
        duration = (end_dt - start_dt).total_seconds() / 3600.0  # Convert to hours
        
        # Try to extract client/matter information
        search_text = f"{event_title} {event_description}"
        client_info = self._extract_client_matter_info(search_text)
        
        # Build description with attendees
        description = f"Meeting: {event_title}"
        if attendees:
            description += f" (Attendees: {', '.join(attendees[:3])})"
        
        return {
            'source': 'calendar',
            'description': description,
            'hours': round(duration, 2),
            'date': start_dt.date().isoformat(),
            'source_reference': f"Calendar event: {start_dt.isoformat()} - {end_dt.isoformat()}",
            'suggested_matter_id': client_info.get('matter_id'),
            'suggested_client': client_info.get('client_name'),
            'timestamp': start_dt.isoformat()
        }
    
    def capture_from_document(self, document_name, document_type=None, 
                             activity_type='edit', duration_minutes=None, timestamp=None):
        """
        Capture time from document activity
        
        Args:
            document_name: Name of the document
            document_type: Type of document (e.g., 'brief', 'contract', 'memo')
            activity_type: Type of activity (e.g., 'edit', 'review', 'create')
            duration_minutes: Time spent on document
            timestamp: When the activity occurred
        
        Returns:
            Dictionary with captured time information
        """
        # Parse timestamp
        if timestamp:
            if isinstance(timestamp, str):
                dt = parser.parse(timestamp)
            else:
                dt = timestamp
        else:
            dt = datetime.utcnow()
        
        # Estimate duration if not provided
        if not duration_minutes:
            # Default estimates based on activity type
            duration_estimates = {
                'create': 60,    # 1 hour
                'edit': 30,      # 30 minutes
                'review': 20,    # 20 minutes
                'comment': 10    # 10 minutes
            }
            duration_minutes = duration_estimates.get(activity_type, 30)
        
        hours = duration_minutes / 60.0
        
        # Try to extract client/matter information from document name
        client_info = self._extract_client_matter_info(document_name)
        
        # Build description
        activity_desc = activity_type.capitalize()
        doc_type_desc = f" {document_type}" if document_type else ""
        description = f"{activity_desc}{doc_type_desc}: {document_name}"
        
        return {
            'source': 'document',
            'description': description,
            'hours': round(hours, 2),
            'date': dt.date().isoformat(),
            'source_reference': f"Document: {document_name}",
            'suggested_matter_id': client_info.get('matter_id'),
            'suggested_client': client_info.get('client_name'),
            'timestamp': dt.isoformat()
        }
    
    def _extract_client_matter_info(self, text):
        """
        Extract client and matter information from text
        Uses pattern matching to identify clients and matters
        
        Args:
            text: Text to search for client/matter references
        
        Returns:
            Dictionary with client_name and matter_id if found
        """
        result = {}
        
        # Look for matter number patterns (e.g., M00001, #M00001)
        matter_pattern = r'#?M\d{5}'
        matter_match = re.search(matter_pattern, text, re.IGNORECASE)
        if matter_match:
            result['matter_number'] = matter_match.group().replace('#', '')
        
        # Check registered client patterns
        for client_name, pattern in self.client_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                result['client_name'] = client_name
                break
        
        return result
    
    def register_client_pattern(self, client_name, pattern):
        """
        Register a pattern to automatically identify a client in text
        
        Args:
            client_name: Name of the client
            pattern: Regex pattern to match for this client
        """
        self.client_patterns[client_name] = pattern
    
    def register_matter_pattern(self, matter_id, pattern):
        """
        Register a pattern to automatically identify a matter in text
        
        Args:
            matter_id: ID of the matter
            pattern: Regex pattern to match for this matter
        """
        self.matter_patterns[matter_id] = pattern
