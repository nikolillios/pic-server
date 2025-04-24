from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        print(user)
        print(user.__dict__)
        print(user.id)
        token['uid'] = user.id
        print(token)
        print("serializing jwt token")
        print(token)
        return token