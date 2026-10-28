from __future__ import annotations

import csv
import io
import math
import os

from flask import Flask, render_template, request

from ga import balanced_group_sizes, run_ga

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
# 60人の上三角（1770ペア）と人数設定をmultipartフォームで受け取れるようにする。
app.config["MAX_FORM_PARTS"] = 4096


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


@app.post("/edit")
def edit():
    return render_template("index.html", form=request.form)


@app.post("/optimize")
def optimize():
    try:
        raw_names = request.form.get("names", "")
        names = _parse_names(raw_names)
        member_count = int(request.form.get("participant_count", len(names)))
        if not 2 <= member_count <= 60:
            raise ValueError("参加者は2〜60名で入力してください。")
        if not names:
            names = [f"参加者{index + 1}" for index in range(member_count)]
        if len(names) != member_count:
            raise ValueError(f"参加者数は{member_count}名ですが、名前が{len(names)}名分あります。名前の数を合わせるか、名前欄を空にしてください。")
        group_count = int(request.form.get("group_count", "0"))
        if not 1 <= group_count <= member_count:
            raise ValueError("班数は1以上、参加者数以下にしてください。")
        mode = request.form.get("allocation_mode", "auto")
        if mode == "custom":
            try:
                sizes = [int(value) for value in request.form.getlist("group_sizes")]
            except ValueError:
                raise ValueError("各班の人数は1以上の整数にしてください。") from None
            if len(sizes) != group_count or any(size < 1 for size in sizes):
                raise ValueError("すべての班に1以上の人数を指定してください。")
            if sum(sizes) != member_count:
                raise ValueError(f"各班の合計は{sum(sizes)}名です。参加者{member_count}名と一致させてください。")
        elif mode == "auto":
            sizes = balanced_group_sizes(member_count, group_count)
        else:
            raise ValueError("人数の割り振り方法を選択してください。")

        upload = request.files.get("matrix_csv")
        matrix = _matrix_from_csv(upload, names) if upload and upload.filename else _matrix_from_form(len(names))
        seed_raw = request.form.get("seed", "").strip()
        seed = int(seed_raw) if seed_raw else None
        result = run_ga(matrix, group_count, group_sizes=sizes, seed=seed)
        groups = [[names[index] for index in group] for group in result.groups]
        return render_template("result.html", groups=groups, score=result.score, seed=seed, names=raw_names, group_count=group_count, group_sizes=sizes, allocation_mode=mode, participant_count=member_count, matrix=matrix)
    except (ValueError, TypeError) as error:
        return render_template("index.html", error=str(error), form=request.form), 400


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
