"""电商同步URL配置"""

from django.urls import path

from . import api_views
from .views.listing_views import listing_list

urlpatterns = [
    # 前台视图路由
    path("", listing_list, name="listing_list"),
    # API路由
    path(
        "api/products/<int:product_id>/listings/fragment/",
        api_views.product_listings_fragment,
        name="product_listings_fragment",
    ),
    path("api/platforms/", api_views.platforms_list, name="platforms_list"),
    path("api/listings/", api_views.listings_list, name="listings_list_api"),
    path("api/listings/publish/", api_views.publish_listing, name="publish_listing"),
    path(
        "api/listings/<int:listing_id>/sync/",
        api_views.sync_listing,
        name="sync_listing",
    ),
    path(
        "api/listings/batch-sync/",
        api_views.batch_sync_listings,
        name="batch_sync_listings",
    ),
]
