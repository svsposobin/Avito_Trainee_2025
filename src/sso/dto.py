from dataclasses import dataclass
from typing import Dict, Optional, Any, List
from src.dto import BaseResponse


@dataclass
class GetCurrentUserResponse(BaseResponse):
    message: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


@dataclass
class RegisterUserResponse(BaseResponse):
    user: Optional[Dict[str, str]] = None


@dataclass
class LoginUserResponse(BaseResponse):
    token: Optional[str] = None


@dataclass
class InitPVZResponse(BaseResponse):
    id: Optional[str] = None
    city: Optional[str] = None
    registered_at: Optional[str] = None


@dataclass
class InitActiveReceptionsResponse(BaseResponse):
    receptions_id: Optional[str] = None
    pvz_id: Optional[str] = None
    status: Optional[str] = None


@dataclass
class AddProductResponse(BaseResponse):
    product_id: Optional[int] = None
    accepting_id: Optional[int] = None
    type: Optional[str] = None
    datetime: Optional[str] = None


@dataclass
class DeleteProductResponse(BaseResponse):
    product_id: Optional[int] = None
    accepting_id: Optional[int] = None
    type: Optional[str] = None
    datetime: Optional[str] = None


@dataclass
class CloseReceptionResponse(BaseResponse):
    reception_id: Optional[int] = None
    pvz_id: Optional[int] = None
    status: Optional[str] = None


@dataclass
class PVZInfoResponse(BaseResponse):
    pvz_list: Optional[List[Dict[str, str] | List[Dict[str, str | Any]]]] = None
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
