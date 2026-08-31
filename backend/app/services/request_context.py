from contextvars import ContextVar

request_ip: ContextVar[str | None] = ContextVar("request_ip", default=None)
request_agent: ContextVar[str | None] = ContextVar("request_agent", default=None)
