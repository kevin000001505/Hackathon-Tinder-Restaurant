import uuid
from datetime import datetime, timedelta

class Session:
    """
    A simple dictionary-based session management class.

    Attributes:
        sessions (dict): A dictionary to store session data, where the key is the session ID.
    """

    def __init__(self):
        """Initializes the Session object."""
        self.sessions = {}

    def generate_session_id(self):
        """Generates a unique session ID using uuid4.
        :return: A string representing the unique session ID.
        """
        return str(uuid.uuid4())

    def create_session(self, user_id, timeout_minutes=30):
        """
        Creates a new session for a given user ID.

        Args:
            user_id (str): The user ID to associate with the session.
            timeout_minutes (int, optional): The session timeout in minutes. Defaults to 30.

        Returns:
            str: The newly generated session ID.
        """
        session_id = self.generate_session_id()
        self.sessions[session_id] = {
            'user_id': user_id,
            'last_active': datetime.now(),
            'timeout': timeout_minutes,
        }
        return session_id

    def get_session_data(self, session_id):
        """
        Retrieves session data for a given session ID.

        Args:
            session_id (str): The session ID to retrieve data for.

        Returns:
            dict: The session data if found and not expired, None otherwise.
        """
        if session_id in self.sessions:
            session_data = self.sessions[session_id]
            now = datetime.now()
            last_active = session_data['last_active']
            timeout = session_data['timeout']
            if (now - last_active).total_seconds() <= timeout * 60:
                # Update last_active on every fetch
                session_data['last_active'] = now
                return session_data
            else:
                self.delete_session(session_id)  #remove expired session
                return None  # Session has expired
        else:
            return None  # Session not found

    def delete_session(self, session_id):
        """
        Deletes a session with a given session ID.

        Args:
            session_id (str): The session ID to delete.
        """
        if session_id in self.sessions:
            del self.sessions[session_id]

    def clear_expired_sessions(self):
        """
        Clears all expired sessions.  This method is intended to be run
        periodically, perhaps by a background task.
        """
        now = datetime.now()
        expired_sessions = []
        for session_id, session_data in self.sessions.items():
            last_active = session_data['last_active']
            timeout = session_data['timeout']
            if (now - last_active).total_seconds() > timeout * 60:
                expired_sessions.append(session_id)
        for session_id in expired_sessions:
            self.delete_session(session_id)

    def get_user_id(self, session_id):
        """Helper function to get user ID from session.
        Args:
            session_id (str): the id of the session
        Returns:
            str: user id or None
        """
        session_data = self.get_session_data(session_id)
        if session_data:
            return session_data['user_id']
        return None
