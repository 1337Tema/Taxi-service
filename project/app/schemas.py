# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class UserType(str, Enum):
    DRIVER = "driver"
    PASSENGER = "passenger"

class DriverStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"

class RideStatus(str, Enum):
    PENDING = "pending"
    DRIVER_ASSIGNED = "driver_assigned"
    DRIVER_ARRIVED = "driver_arrived"
    PASSENGER_ONBOARD = "passenger_onboard"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Базовые схемы
class UserBase(BaseModel):
    email: EmailStr
    phone: str
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str
    user_type: UserType

class UserResponse(UserBase):
    id: int
    user_type: UserType
    created_at: datetime
    
    class Config:
        from_attributes = True

# Схемы для водителей
class DriverBase(BaseModel):
    car_model: str
    car_license: str

class DriverCreate(DriverBase):
    user_id: int

class DriverResponse(DriverBase):
    id: int
    user_id: int
    status: DriverStatus
    rating: Optional[float]
    total_rides: int
    created_at: datetime

    class Config:
        from_attributes = True

class DriverStatusUpdate(BaseModel):
    status: DriverStatus
    current_x: Optional[int] = None
    current_y: Optional[int] = None

class LocationUpdate(BaseModel):
    x: int
    y: int

# Схемы для поездок
class RideCreate(BaseModel):
    passenger_id: int
    start_x: int
    start_y: int
    end_x: int
    end_y: int

class RideResponse(BaseModel):
    id: int
    passenger_id: int
    driver_id: Optional[int]
    status: RideStatus
    start_x: int
    start_y: int
    end_x: int
    end_y: int
    distance: int
    estimated_duration: int
    estimated_price: float
    final_price: Optional[float]
    created_at: datetime
    accepted_at: Optional[datetime]
    arrived_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]

    class Config:
        from_attributes = True

class RideStatusUpdate(BaseModel):
    status: RideStatus

class PriceCalculation(BaseModel):
    distance: int
    estimated_duration: int
    estimated_price: float

# Схемы для аутентификации
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    user_type: UserType

class LoginRequest(BaseModel):
    email: EmailStr
    password: str