from django.urls import path

from . import views

urlpatterns = [
    path("api/health/", views.health, name="health"),
    path("api/products/search/", views.search, name="product-search"),
    path("api/products/add/", views.add_product, name="product-add"),
    path("api/analyze/", views.analyze, name="analyze"),
    path("api/literature/", views.literature_only, name="literature"),
    path("api/chat/", views.chat_endpoint, name="chat"),
]
