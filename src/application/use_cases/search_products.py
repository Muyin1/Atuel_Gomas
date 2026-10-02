from src.application.ports.product_repository import IProductRepository
from src.application.dtos.product_dto import ProductSearchDTO, ProductSummaryDTO
from src.domain.entities.product import Product
from src.domain.entities.user_role import UserRole


class SearchProductsUseCase:
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo

    async def execute(self, dto: ProductSearchDTO) -> list[ProductSummaryDTO]:
        products: list[Product] = await self.product_repo.search(
            query=dto.query,
            category=dto.category,
            family=dto.family,
            vehicle_brand=dto.vehicle_brand,
            vehicle_model=dto.vehicle_model,
            page=dto.page,
            page_size=dto.page_size
        )

        results = []
        for p in products:
            price = p.calculate_price_for_role(dto.role, custom_markup=dto.custom_markup)
            is_wholesale = dto.role in (UserRole.B2B_CLIENT, UserRole.SALES_AGENT, UserRole.ADMIN)
            compat_list = [f"{c.brand} {c.model} ({c.engine} {c.years})" for c in p.compatibilities]
            compat_summary = ", ".join(compat_list) if compat_list else "Uso universal / medidas varias"

            results.append(
                ProductSummaryDTO(
                    id=p.id,
                    sku=p.sku,
                    oem_code=p.oem_code,
                    name=p.name,
                    category=p.category.value if hasattr(p.category, "value") else str(p.category),
                    family=p.family_name or "",
                    dimensions=p.dimensions.summary(),
                    price_formatted=price.format_ars(),
                    is_wholesale=is_wholesale,
                    stock=p.stock,
                    image_url=p.image_url,
                    compatibilities_summary=compat_summary
                )
            )
        return results
