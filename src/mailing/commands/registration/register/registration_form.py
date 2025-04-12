class RegistrationForm:
    login: str
    password: str

    def __init__(self, state_data: dict[str, str]) -> None:
        self.login = state_data['login']
        self.password = state_data['password']