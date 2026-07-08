import pytest

from app.core.exceptions import AppError
from app.schemas.report_composer import ReportComposerPlan, ReportFilter, ReportMetric, ReportSelectedField, ReportSource
from app.utils.report_composer_validator import ReportComposerValidator


def test_validator_rejects_unsupported_source():
    plan = ReportComposerPlan(source=ReportSource(source_name="GL Entry"))
    with pytest.raises(AppError):
        ReportComposerValidator().validate_plan(plan)


def test_validator_removes_sensitive_fields():
    plan = ReportComposerPlan(
        source=ReportSource(source_name="Customer"),
        fields=[ReportSelectedField(fieldname="name"), ReportSelectedField(fieldname="api_secret")],
    )
    validated = ReportComposerValidator().validate_plan(plan)
    assert [field.fieldname for field in validated.fields] == ["name"]


def test_validator_rejects_sql_like_filter_value():
    plan = ReportComposerPlan(
        source=ReportSource(source_name="Sales Invoice"),
        filters=[ReportFilter(fieldname="customer", operator="like", value="%' union select password --")],
    )
    with pytest.raises(AppError):
        ReportComposerValidator().validate_plan(plan)


def test_validator_adds_default_metric_for_grouped_plan():
    plan = ReportComposerPlan(source=ReportSource(source_name="Item"), group_by=["item_group"], metrics=[])
    validated = ReportComposerValidator().validate_plan(plan)
    assert [metric.model_dump() for metric in validated.metrics] == [ReportMetric(fieldname="name", function="count", label="Count").model_dump()]
