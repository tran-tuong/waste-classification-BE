from pydantic import BaseModel

class BinControlRequest(BaseModel):
    bin_index: int