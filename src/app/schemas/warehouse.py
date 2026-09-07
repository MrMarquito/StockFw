import uuid
from pydantic import BaseModel, ConfigDict, Field


class WarehouseBase(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseRead(WarehouseBase):
    id: uuid.UUID
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class BinLocationBase(BaseModel):
    zone: str = Field(default="DEFAULT", max_length=16)
    aisle: str = Field(..., max_length=16)
    shelf: str = Field(..., max_length=16)
    bin_code: str = Field(..., max_length=32)


class BinLocationCreate(BinLocationBase):
    warehouse_id: uuid.UUID


class BinLocationRead(BinLocationBase):
    id: uuid.UUID
    warehouse_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)
