# from rest_framework import generics
# from django_filters import rest_framework as filters


# class ProductFilter(filters.FilterSet):
#     min_price = filters.NumberFilter(field_name="price", lookup_expr='gte')
#     max_price = filters.NumberFilter(field_name="price", lookup_expr='lte')

#     class Meta:
#         model = Product
#         fields = ['category', 'in_stock', 'min_price', 'max_price']


# class ProductList(generics.ListAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
#     filter_backends = (filters.DjangoFilterBackend,)
#     filterset_class = ProductFilter
