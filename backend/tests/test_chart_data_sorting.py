from app.utils.chart_data_normalizer import normalize_chart_data, sort_time_series_data


def test_month_labels_sort_chronologically():
    rows = [
        {"period": "Apr 2025", "value": 4},
        {"period": "Jan 2025", "value": 1},
        {"period": "Mar 2025", "value": 3},
        {"period": "Feb 2025", "value": 2},
    ]
    sorted_rows = sort_time_series_data(rows, "period")
    assert [row["period"] for row in sorted_rows] == ["Jan 2025", "Feb 2025", "Mar 2025", "Apr 2025"]


def test_bar_ranking_sorts_by_metric_desc_when_not_temporal():
    chart = normalize_chart_data(
        {
            "chart_type": "bar",
            "x_key": "customer",
            "y_key": "grand_total",
            "data": [
                {"customer": "A", "grand_total": 10},
                {"customer": "B", "grand_total": 40},
                {"customer": "C", "grand_total": 20},
            ],
        }
    )
    assert [row["customer"] for row in chart["data"]] == ["B", "C", "A"]
