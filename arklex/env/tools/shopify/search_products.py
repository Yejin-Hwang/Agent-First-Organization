"""
This module provides functionality to search for products in the Shopify store based on a query string.
It returns product information in a card format suitable for display.

Module Name: search_products

This file contains the code for searching products in Shopify.
"""

import inspect
import json
from typing import TypedDict

import shopify

from arklex.env.tools.shopify._exception_prompt import ShopifyExceptionPrompt
from arklex.env.tools.shopify.utils import authorify_admin
from arklex.env.tools.shopify.utils_nav import PAGEINFO_OUTPUTS, cursorify

# general GraphQL navigation utilities
from arklex.env.tools.shopify.utils_slots import (
    ShopifyOutputs,
    ShopifySearchProductsSlots,
)

# Admin API
from arklex.env.tools.tools import register_tool
from arklex.utils.exceptions import ToolExecutionError
from arklex.utils.logging_utils import LogContext

log_context = LogContext(__name__)


class SearchProductsKwargs(TypedDict, total=False):
    """Type definition for kwargs used in search_products function."""

    limit: str
    navigate: str
    pageInfo: dict
    shop_url: str
    api_version: str
    admin_token: str
    llm_provider: str
    model_type_or_path: str


description = "Search products by string query. If no products are found, the function will return an error message."
slots = ShopifySearchProductsSlots.get_all_slots()
outputs = [ShopifyOutputs.PRODUCT_ID, *PAGEINFO_OUTPUTS]


@register_tool(description, slots, outputs, isResponse=True)
def search_products(product_query: str, **kwargs: SearchProductsKwargs) -> str:
    """
    Search for products in the Shopify store based on a query string.

    Args:
        product_query (str): The search query string to find products.
        **kwargs: Additional keyword arguments for pagination, authentication, and LLM configuration.

    Returns:
        str: A JSON string containing:
            - card_list: List of product information in card format, including:
                - id: Product ID
                - title: Product title
                - description: Truncated product description
                - link_url: URL to the product page
                - image_url: URL of the product's main image
                - variants: List of product variants with their details

    Raises:
        ToolExecutionError: If no products are found or if there's an error during the search.
    """
    func_name = inspect.currentframe().f_code.co_name
    nav = cursorify(kwargs)
    if not nav[1]:
        return nav[0]
    auth = authorify_admin(kwargs)

    try:
        with shopify.Session.temp(**auth):
            response = shopify.GraphQL().execute(f"""
                {{
                    products ({nav[0]}, query: "{product_query}") {{
                        nodes {{
                            id
                            title
                            description
                            handle
                            onlineStoreUrl
                            images(first: 1) {{
                                edges {{
                                    node {{
                                        src
                                        altText
                                    }}
                                }}
                            }}
                            variants (first: 3) {{
                                nodes {{
                                    displayName
                                    id
                                    price
                                    inventoryQuantity
                                }}
                            }}
                        }}
                        pageInfo {{
                            endCursor
                            hasNextPage
                            hasPreviousPage
                            startCursor
                        }}
                    }}
                }}
            """)
            products = json.loads(response)["data"]["products"]["nodes"]
            card_list = []
            for product in products:
                product_dict = {
                    "id": product.get("id"),
                    "title": product.get("title"),
                    "description": product.get("description", "None")[:180] + "...",
                    "link_url": product.get("onlineStoreUrl")
                    if product.get("onlineStoreUrl")
                    else f"{auth['domain']}/products/{product.get('handle')}",
                    "image_url": product.get("images", {})
                    .get("edges", [{}])[0]
                    .get("node", {})
                    .get("src", ""),
                    "variants": product.get("variants", {}).get("nodes", []),
                }
                card_list.append(product_dict)
            if card_list:
                return json.dumps({"card_list": card_list})
            else:
                raise ToolExecutionError(
                    func_name,
                    extra_message=ShopifyExceptionPrompt.PRODUCT_SEARCH_ERROR_PROMPT,
                )

    except Exception as e:
        raise ToolExecutionError(
            func_name,
            extra_message=ShopifyExceptionPrompt.PRODUCT_SEARCH_ERROR_PROMPT,
        ) from e
