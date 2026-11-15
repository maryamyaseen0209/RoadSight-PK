import os
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_WORKSPACE_DIR = Path(__file__).resolve().parent.parent
os.environ["YOLO_CONFIG_DIR"] = str(_WORKSPACE_DIR / "artifacts")
os.environ["YOLO_OFFLINE"] = "True"
os.environ["YOLO_VERBOSE"] = "False"
os.environ["ULTRALYTICS_AUTOINSTALL"] = "0"
os.environ["SETTINGS_CHECK"] = "0"

from backend.app.main import app
from backend.app.db.session import get_db
from backend.app.models.detection import Base


@pytest.fixture(scope="session", autouse=True)
def override_test_db(tmp_path_factory):
    """
    Isolates pytest database operations into a session-scoped temporary SQLite database.
    Prevents test runs from polluting or altering the production 'roadsight.db'.
    """
    db_file = tmp_path_factory.mktemp("data") / "test_roadsight.db"
    test_engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def _get_test_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()
