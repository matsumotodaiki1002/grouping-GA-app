import io
import unittest
from html.parser import HTMLParser

from werkzeug.datastructures import MultiDict

from app import app


class ResultParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = MultiDict()
        self.group_member_counts = []
        self.in_group = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("type") == "hidden":
            self.fields.add(attrs["name"], attrs.get("value", ""))
        if tag == "article" and attrs.get("class") == "group-card":
            self.in_group = True
            self.group_member_counts.append(0)
        if tag == "li" and self.in_group:
            self.group_member_counts[-1] += 1

    def handle_endtag(self, tag):
        if tag == "article":
            self.in_group = False


class AppTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.base = {"participant_count": "11", "group_count": "3", "seed": "42", "names": ""}

    def result(self, data):
        response = self.client.post("/optimize", data=data)
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        parser = ResultParser()
        parser.feed(response.get_data(as_text=True))
        return parser

    def test_initial_screen_exposes_count_controls(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="participant-count"', response.get_data(as_text=True))
        self.assertIn('id="group-count"', response.get_data(as_text=True))

    def test_auto_allocation_and_rerun(self):
        result = self.result(self.base | {"allocation_mode": "auto"})
        self.assertEqual(result.group_member_counts, [3, 4, 4])
        self.assertEqual(result.fields["names"], "")
        rerun = self.result(result.fields)
        self.assertEqual(rerun.group_member_counts, [3, 4, 4])
        self.assertEqual(rerun.fields["names"], result.fields["names"])

    def test_custom_allocation_and_edit_keep_sizes_and_affinities(self):
        result = self.result(self.base | {"allocation_mode": "custom", "group_sizes": ["2", "4", "5"], "pair_0_1": "7"})
        self.assertEqual(result.group_member_counts, [2, 4, 5])
        self.assertEqual(result.fields.getlist("group_sizes"), ["2", "4", "5"])
        self.assertEqual(result.fields["pair_0_1"], "7.0")
        edit = self.client.post("/edit", data=result.fields)
        self.assertEqual(edit.status_code, 200)
        self.assertIn('value="11"', edit.get_data(as_text=True))
        self.assertEqual(self.result(result.fields).group_member_counts, [2, 4, 5])

    def test_invalid_sizes_and_name_count_fail_on_server(self):
        for change in (
            {"allocation_mode": "custom", "group_sizes": ["3", "3", "4"]},
            {"allocation_mode": "custom", "group_sizes": ["0", "5", "6"]},
            {"allocation_mode": "custom", "group_sizes": ["3.5", "3.5", "4"]},
            {"allocation_mode": "custom", "group_sizes": ["5", "6"]},
            {"group_count": "12"},
            {"names": "A\nB"},
        ):
            with self.subTest(change=change):
                response = self.client.post("/optimize", data=self.base | change)
                self.assertEqual(response.status_code, 400)

    def test_csv_works_with_uneven_groups(self):
        csv = "\n".join(",".join("0" for _ in range(11)) for _ in range(11))
        result = self.result(self.base | {"matrix_csv": (io.BytesIO(csv.encode()), "matrix.csv")})
        self.assertEqual(result.group_member_counts, [3, 4, 4])

    def test_large_multipart_form_accepts_all_affinity_fields(self):
        data = {"participant_count": "60", "group_count": "13", "seed": "42"}
        data.update({f"pair_{i}_{j}": "0" for i in range(60) for j in range(i + 1, 60)})
        response = self.client.post("/optimize", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        result = ResultParser()
        result.feed(response.get_data(as_text=True))
        self.assertEqual(sum(result.group_member_counts), 60)
        self.assertEqual(len(result.group_member_counts), 13)

    def test_blank_seed_is_preserved_for_edit_and_rerun(self):
        result = self.result(self.base | {"seed": ""})
        self.assertEqual(result.fields["seed"], "")


if __name__ == "__main__":
    unittest.main()
