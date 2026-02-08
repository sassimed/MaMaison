from pydantic import BaseModel, ConfigDict

class BaseDBModel(BaseModel):
    """Base model for database documents"""
    model_config = ConfigDict(
        extra="ignore",
        from_attributes=True,
        populate_by_name=True
    )
