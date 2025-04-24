from account.models import UserData

def getUserById(id):
    print("userid")
    print(id)
    return UserData.objects.get(id)