
from contextvars import ContextVar
current_request = ContextVar("current_request", default=None)
# bot message id -> (owner_user_id, original_user_message_id, created_at)
message_owners = {}
INTERACTION_TTL = 60
