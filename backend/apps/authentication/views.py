from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that returns user information along with tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer
