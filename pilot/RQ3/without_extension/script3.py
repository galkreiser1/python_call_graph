class User:
    def __init__(self, username):
        self.username = username
        self.permissions = []

    def add_permission(self, permission):
        self.permissions.append(permission)

class Admin(User):
    def __init__(self, username):
        super().__init__(username)
        self.add_permission('admin')

class Guest(User):
    def __init__(self, username):
        super().__init__(username)
        self.add_permission('read')

class Contributor(User):
    def __init__(self, username):
        super().__init__(username)
        self.add_permission('write')

class SuperUser(Admin, Contributor):
    def __init__(self, username):
        Admin.__init__(self, username)
        Contributor.__init__(self, username)
        self.add_permission('delete')

def manage_users(users):
    for user in users:
        print(f"{user.username}: {', '.join(user.permissions)}")

def main():
    users = [SuperUser("alice"), Admin("bob"), Guest("carol"), Contributor("dave")]
    manage_users(users)

main()
