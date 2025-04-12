class RegistrationForm:
    subdomain: str
    login: str
    password: str

    def __init__(self, state_data: dict[str, str]) -> None:
        self.subdomain = state_data['subdomain']
        self.login = state_data['login']
        self.password = state_data['password']

