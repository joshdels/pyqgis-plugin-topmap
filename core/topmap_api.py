import requests


class TopMapApiClient:
    """Simple client for TopMap API."""

    BASE_URL = "https://topmapsolutions.com/api/v1"

    def __init__(self, timeout=20):
        """Initialize the API client with default headers and timeout."""
        self.session = requests.Session()
        self.timeout = timeout
        self.token = None

        self.session.headers.update(
            {
                "User-Agent": "TopMap QGIS Plugin",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    # -------------------- Authentication --------------------

    def login(self, username, password):
        """Login and store token."""
        payload = {"username": username, "password": password}

        response = self.session.post(
            f"{self.BASE_URL}/login/", json=payload, timeout=self.timeout
        )
        response.raise_for_status()

        token = response.json().get("token")
        if not token:
            raise ValueError("No token returned from server")

        self.token = token
        self.session.headers.update({"Authorization": f"Token {token}"})
        return token

    def logout(self):
        """Logout and clear token."""
        if not self.token:
            return

        response = self.session.post(f"{self.BASE_URL}/logout/", timeout=self.timeout)
        response.raise_for_status()

        self.session.headers.pop("Authorization", None)
        self.token = None

    # -------------------- Data Retrieval --------------------

    def get_projects(self):
        """Fetch projects for the authenticated user."""
        if not self.token:
            raise ValueError("Not authenticated. Please login first.")

        try:
            response = self.session.get(
                f"{self.BASE_URL}/projects/", timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch projects: {e}")
