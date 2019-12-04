from datetime import datetime
from pprint import pprint
import json

# mock
def get_all_keys(bucket, full_path):
    d = {
        "xxx/yyy/zzz/abc/def": [
            "id=123/month=2018-01-01/2018-01-19T10:31:18.818Z.gz",
            "id=123/month=2019-01-01/2019-01-19T10:31:18.818Z.gz",
            "id=123/month=2019-02-01/2019-02-19T10:32:18.818Z.gz",
            "id=333/month=2019-03-01/2019-06-19T10:33:18.818Z.gz",
            "id=123/month=2019-10-01/2019-10-19T10:34:18.818Z.gz",
            "id=333/month=2019-11-01/2019-12-19T10:35:18.818Z.gz",
        ],
        "xxx/yyy/zzz/abc/del": [
            "id=123/month=1018-01-01/1018-01-19T10:31:18.818Z.gz",
            "id=123/month=1019-01-01/1019-01-19T10:31:18.818Z.gz",
            "id=123/month=1019-02-01/1019-02-19T10:32:18.818Z.gz",
            "id=333/month=1019-03-01/1019-06-19T10:33:18.818Z.gz",
            "id=123/month=1019-10-01/1019-10-19T10:34:18.818Z.gz",
            "id=333/month=1019-11-01/1019-12-19T10:35:18.818Z.gz",
            "id=333/month=1017-11-01/1019-12-19T10:35:18.818Z.gz",
            "id=334/month=1017-11-01/1019-12-19T10:35:18.818Z.gz",
        ],
    }
    return iter(d.get(full_path, []))


def calculate_months_by_id(specific_paths, bucket, base_path):
    time_format = "%Y-%m-%d"
    path_dict = {}

    for specific_path in specific_paths:
        key_dict = {}
        full_path = "/".join([base_path.strip("/"), specific_path.strip("/")])

        for key in get_all_keys(bucket, full_path):
            key_dict = update_key_dict2(key_dict, key, time_format)
        output_dict = calculate_missing_months(key_dict)
        path_dict[full_path] = output_dict
    return path_dict


def update_key_dict2(key_dict, key, time_format):
    parsed_key = key.split("/")
    id = parsed_key[0].split("=")[1]
    key_date = parsed_key[1].split("=")[1]
    dt_key_date = datetime.strptime(key_date, time_format)

    if id not in key_dict:
        key_dict[id] = {"min": key_date, "max": key_date, "present": {key_date}}
    else:
        if datetime.strptime(key_dict[id]["min"], time_format) > dt_key_date:
            key_dict[id]["min"] = key_date
        if datetime.strptime(key_dict[id]["max"], time_format) < dt_key_date:
            key_dict[id]["max"] = key_date

        key_dict[id]["present"].add(key_date)
    return key_dict


def generate_expected_months(min_month, max_month):
    expected_months = []
    y_iter, m_iter, _ = [int(x) for x in min_month.split("-")]
    y_max, m_max, _ = [int(x) for x in max_month.split("-")]
    while y_iter != y_max or m_iter != m_max:
        expected_months.append("-".join([str(y_iter), str(m_iter).zfill(2), "01"]))
        if m_iter == 12:
            m_iter = 1
            y_iter += 1
        else:
            m_iter += 1
    return expected_months


def calculate_missing_months(key_dict):
    output_dict = {}
    for id, val in key_dict.items():
        expected_months = generate_expected_months(val["min"], val["max"])
        missing_months = [x for x in expected_months if x not in val["present"]]
        output_dict[id] = {
            "max": val["max"],
            "min": val["min"],
            "missing": missing_months,
        }
    return output_dict


def write_output(filename, path_dict):
    with open(filename, "w") as f:
        f.write(json.dumps(path_dict, indent=4))


if __name__ == "__main__":
    bucket = "s3://my-bucket"
    base_path = "/xxx/yyy/zzz/abc/"
    specific_paths = ["/def/", "/del/"]
    path_dict = calculate_months_by_id(specific_paths, bucket, base_path)
    pprint(path_dict)
    write_output("output.json", path_dict)
