from pydantic import BaseModel


class OrderItemInputDTO(BaseModel):
    product_id: str
    quantity: int


class CreateOrderDTO(BaseModel):
    customer_id: str
    items: list[OrderItemInputDTO]
    notes: str = ""
