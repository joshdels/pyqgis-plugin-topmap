import requests


class TopMapApiClient:
    BASE_URL = "https://topmapsolutions.com/api/v1"

    def __init__(self, timeout=20):
        self.session = requests.Session()
        self.timeout = timeout
        self.token = None

        # Set headers before any requests
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QGIS Plugin",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    # AUTH
    def login(self, username: str, password: str) -> str:
        """Login and store token"""
        payload = {"username": username, "password": password}

        r = self.session.post(
            f"{self.BASE_URL}/login/", json=payload, timeout=self.timeout
        )

        print("Status code:", r.status_code)
        print("Response text:", r.text) 

        r.raise_for_status()

        self.token = r.json().get("token")
        if not self.token:
            raise ValueError("No token returned from server")

        self.session.headers.update({"Authorization": f"Token {self.token}"})
        return self.token

    def logout(self):
        if not self.token:
            return

        r = self.session.post(f"{self.BASE_URL}/logout/", timeout=self.timeout)
        r.raise_for_status()

        self.session.headers.pop("Authorization", None)
        self.token = None

    # DATA
    def get_projects(self):
        """Fetch user projects"""
        if not self.token:
            raise ValueError("Not authenticated. Please login first.")

        try:
            r = self.session.get(f"{self.BASE_URL}/projects/", timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch projects: {e}")
