import pytest
from uuid import uuid4
from pydantic import ValidationError
from inndxd_core.domain.project import ProjectCreate
from inndxd_core.domain.brief import BriefCreate
from inndxd_core.domain.data_item import DataItemCreate


def test_project_create_valid():
    p = ProjectCreate(
        name="Test",
        description=None,
        tenant_id=uuid4(),
    )
    assert p.name == "Test"


def test_project_create_name_too_short():
    with pytest.raises(ValidationError):
        ProjectCreate(name="", tenant_id=uuid4())


def test_brief_create_requires_min_length():
    tid = uuid4()
    pid = uuid4()
    with pytest.raises(ValidationError):
        BriefCreate(
            project_id=pid,
            tenant_id=tid,
            natural_language="short",
        )


def test_data_item_create_valid():
    tid = uuid4()
    pid = uuid4()
    bid = uuid4()
    item = DataItemCreate(
        project_id=pid,
        tenant_id=tid,
        brief_id=bid,
        source_url="https://example.com",
        content_type="article",
        raw_payload={"text": "hello"},
        structured_payload={"title": "hello"},
    )
    assert item.content_type == "article"
