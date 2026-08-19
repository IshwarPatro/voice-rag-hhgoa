import re

class ModerationShield:
    def __init__(self):
        # A simple keyword matcher to filter dangerous, abusive, or malicious prompts
        self.blocked_keywords = [
            "hack", "crack", "payload", "exploit", "bypass security",
            "बम", "हैकिंग", "सुरक्षा बाईपास"
        ]
        
        # A regex pattern for general coding tasks or unrelated questions to classify as off-topic
        # Since MSMARCO-XI subset is QA about general information, we refuse general programming requests
        # or irrelevant administrative operations.
        self.offtopic_keywords = [
            "python function", "write code", "html template",
            "rust compiler", "git pull", "git merge", "decorator"
        ]

    def is_safe(self, text):
        """
        Checks if the input text contains unsafe keywords. Returns (is_safe, reason).
        """
        normalized = text.lower()
        for kw in self.blocked_keywords:
            if kw in normalized:
                return False, f"Flagged term detected: '{kw}'"
        return True, "Safe"

    def is_on_topic(self, text):
        """
        Heuristic off-topic classification to target MSMARCO topics (informational QA)
        and refuse unrelated prompts (like coding help or instructions injection).
        """
        normalized = text.lower()
        
        # Refuse system commands or coding questions
        for kw in self.offtopic_keywords:
            if kw in normalized:
                return False, "This system supports search and QA queries only. Programming or execution queries are off-topic."
                
        # Basic check to reject prompts formatting like system instructions
        if "delete all" in normalized or "ignore instruction" in normalized:
            return False, "Instruction injection detected."
            
        return True, "On-topic"
