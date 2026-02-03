import requests
import traceback
import os


class TopMapApiClient:
    """Simple client for TopMap API."""

    # BASE_URL = "https://topmapsolutions.com/api/v1"
    BASE_URL = "http://127.0.0.1:8000/api/v1"

    def __init__(self, timeout=20):
        """Initialize the API client with default headers and timeout."""
        self.session = requests.Session()
        self.timeout = timeout
        self.token = None

        self.session.headers.update(
            {
                "User-Agent": "TopMap QGIS Plugin",
                "Accept": "application/json",
                # "Content-Type": "application/json",
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

    def get_user_profile(self):
        """Fetches user that already authenticates"""
        if not self.token:
            raise ValueError("Not authenticated. Please login first.")

        try:
            response = self.session.get(
                f"{self.BASE_URL}/user-profile/", timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch user information: {e}")

    def get_project(self, project_id: int) -> dict:
        """Fetch a single project by ID"""
        pass

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

    def create_project(self, payload):
        """Create a new project from authenticated users."""
        if not self.token:
            raise ValueError("Not Authenticated. Please login first.")

        try:
            response = self.session.post(
                f"{self.BASE_URL}/projects/", json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to create project: {e}")

    def upload_project(self, id, input_payload):
        """Upload a new project from authenticated users."""
        if not self.token:
            raise ValueError("Not Authenticated. Please login first.")

        payload = input_payload

        try:
            response = self.session.put(
                f"{self.BASE_URL}/projects/{id}/", json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch projects: {e}")

    def delete_project(self, id: int) -> bool:
        """Delete a project by ID."""
        if not self.token:
            raise ValueError("Not Authenticated. Please login first.")

        try:
            response = self.session.delete(
                f"{self.BASE_URL}/projects/{id}/", timeout=self.timeout
            )
            response.raise_for_status()
            return True

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to delete the project: {e}")

    def upload_file(self, project_id: int, file_path: str, relative_path: str = None):
        if not self.token:
            raise ValueError("Not authenticated. Please login first.")

        url = f"{self.BASE_URL}/projects/{project_id}/files/upload/"

        data = {}
        if relative_path:
            data["path"] = relative_path

        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            try:
                response = self.session.post(
                    url, files=files, data=data, timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()

            except requests.RequestException as e:
                raise RuntimeError(f"Failed to upload file '{file_path}': {e} ")
