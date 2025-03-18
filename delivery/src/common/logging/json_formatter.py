import datetime as dt
import json
import logging


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """

    def __init__(self, fmt_keys: dict[str, str] | None = None):
        super().__init__()
        self.fmt_keys = fmt_keys or {}

    def format(self, record: logging.LogRecord) -> str:
        base_fields = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(record.created, tz=dt.timezone.utc).isoformat(),
        }

        if record.exc_info is not None:
            base_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            base_fields["stack_info"] = self.formatStack(record.stack_info)

        message_dict = {
            key: base_fields[record_attr] if record_attr in base_fields else getattr(record, record_attr)
            for key, record_attr in self.fmt_keys.items()
        }

        message_dict.update(base_fields)
        return json.dumps(message_dict, default=str)
