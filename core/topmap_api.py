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
        if not self.token:
            raise ValueError("Not authenticated. Please login first.")
        try:
            resp = self.session.get(
                f"{self.BASE_URL}/projects/{project_id}/", timeout=self.timeout
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch project {project_id}: {e}")

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

    def download_project(self, project_id: int, destination_folder: str):
        """Download all files from a specific project by ID."""
        if not self.token:
            raise ValueError("Not authenticated. Please login first.")

        try:
            # Get project details including files
            response = self.session.get(
                f"{self.BASE_URL}/projects/{project_id}/",
                timeout=self.timeout,
            )
            response.raise_for_status()
            project = response.json()

            # Create project folder
            project_name = project.get("name", f"project_{project_id}")
            safe_folder_name = "".join(
                c for c in project_name if c.isalnum() or c in " _-"
            ).rstrip()
            project_path = os.path.join(destination_folder, safe_folder_name)
            os.makedirs(project_path, exist_ok=True)

            # Download all files
            files = project.get("files", [])
            downloaded_count = 0
            failed_files = []

            for file in files:
                file_url = file["file"]
                file_name = file["name"]

                name_part, extension = os.path.splitext(file_name)
                clean_name = "".join(c for c in name_part if c.isalnum() or c in " _-")
                safe_file_name = f"{clean_name}{extension}"
                file_path = os.path.join(project_path, safe_file_name)

                try:
                    r = self.session.get(
                        file_url,
                        stream=True,
                        timeout=20,
                    )
                    r.raise_for_status()
                    with open(file_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    downloaded_count += 1
                    print(f"Downloaded {file_name} to {project_path}")
                except Exception as e:
                    failed_files.append(file_name)
                    print(f"Failed to download {file_name}: {e}")

            return {
                "project_name": project_name,
                "project_path": project_path,
                "downloaded_count": downloaded_count,
                "failed_files": failed_files,
                "total_files": len(files),
            }

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download project {project_id}: {e}")

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
