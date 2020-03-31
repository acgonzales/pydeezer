class User:
    def __init__(self, id, name, arl, picture="https://e-cdns-images.dzcdn.net/images/user/250x250-000000-80-0-0.jpg"):
        self.id = id
        self.name = name
        self.picture = picture
        self.arl = arl        

    def __str__(self):
        return f"Id: {self.id}; Name: {self.name}"

    def __repr__(self):
        return f"Id: {self.id}; Name: {self.name}"