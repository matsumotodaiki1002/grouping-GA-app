from __future__ import annotations

import csv
import io
import math
import os

from flask import Flask, render_template, request

from ga import run_ga

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


def _number(value: str, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label}には数値を入力してください。") from None
    if not math.isfinite(number):
        raise ValueError(f"{label}には有限の数値を入力してください。")
    return number


def _parse_names(raw: str) -> list[str]:
    names = [name.strip() for name in raw.replace("\r", "").split("\n") if name.strip()]
    if len(names) != len(set(names)):
        raise ValueError("参加者名は重複しないように入力してください。")
    return names


def _matrix_from_form(member_count: int) -> list[list[float]]:
    matrix = [[0.0] * member_count for _ in range(member_count)]
    for row in range(member_count):
        for col in range(row + 1, member_count):
            value = _number(request.form.get(f"pair_{row}_{col}", "0") or "0", f"相性（{row + 1}, {col + 1}）")
            matrix[row][col] = matrix[col][row] = value
    return matrix


def _matrix_from_csv(file, names: list[str]) -> list[list[float]]:
    try:
        text = file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("CSVはUTF-8形式で保存してください。") from None
    rows = [row for row in csv.reader(io.StringIO(text)) if any(cell.strip() for cell in row)]
    size = len(names)
    if len(rows) == size + 1 and len(rows[0]) == size + 1:
        rows = [row[1:] for row in rows[1:]]
    if len(rows) != size or any(len(row) != size for row in rows):
        raise ValueError(f"CSVの相性行列は {size} × {size} にしてください。")
    matrix = [[_number(cell.strip(), "CSVの相性") for cell in row] for row in rows]
    for index in range(size):
        if matrix[index][index] != 0:
            raise ValueError("CSVの対角成分は0にしてください。")
        for col in range(index + 1, size):
            if matrix[index][col] != matrix[col][index]:
                raise ValueError("CSVの相性行列は対称行列にしてください。")
    return matrix


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/optimize")
def optimize():
    try:
        names = _parse_names(request.form.get("names", ""))
        if not 2 <= len(names) <= 60:
            raise ValueError("参加者は2〜60名で入力してください。")
        group_count = int(request.form.get("group_count", "0"))
        group_size = int(request.form.get("group_size", "0"))
        if group_count < 1 or group_size < 1:
            raise ValueError("班数と1班あたりの人数は1以上にしてください。")
        if len(names) != group_count * group_size:
            raise ValueError("参加者数は、班数 × 1班あたりの人数と一致させてください。")

        upload = request.files.get("matrix_csv")
        matrix = _matrix_from_csv(upload, names) if upload and upload.filename else _matrix_from_form(len(names))
        seed_raw = request.form.get("seed", "").strip()
        seed = int(seed_raw) if seed_raw else None
        result = run_ga(matrix, group_count, group_size, seed=seed)
        groups = [[names[index] for index in group] for group in result.groups]
        return render_template("result.html", groups=groups, score=result.score, seed=seed, names="\n".join(names), group_count=group_count, group_size=group_size, matrix=matrix)
    except (ValueError, TypeError) as error:
        return render_template("index.html", error=str(error), form=request.form), 400


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
