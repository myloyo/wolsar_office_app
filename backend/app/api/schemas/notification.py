from urllib.parse import urlparse

from pydantic import BaseModel, Field, model_validator


class PushInput(BaseModel):
    endpoint: str = Field(max_length=3000)
    keys: dict[str, str]

    @model_validator(mode="after")
    def safe_endpoint(self) -> "PushInput":
        url = urlparse(self.endpoint)
        hosts = {"fcm.googleapis.com", "updates.push.services.mozilla.com", "web.push.apple.com"}
        if (
            url.scheme != "https"
            or url.hostname not in hosts
            or url.username
            or url.port not in {None, 443}
        ):
            raise ValueError("Адрес push-службы не разрешён")
        if set(self.keys) != {"auth", "p256dh"} or any(
            not 16 <= len(value) <= 200 for value in self.keys.values()
        ):
            raise ValueError("Неверные ключи подписки")
        return self
