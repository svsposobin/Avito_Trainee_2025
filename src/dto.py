from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class BaseResponse:
    result: Optional[Dict[str, bool]] = None
    errors: Optional[str] = None


@dataclass
class JWTTokenResponse:
    access_token: str
