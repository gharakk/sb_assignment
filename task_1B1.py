import random
import re
from pprint import pprint
from datetime import datetime


def val_generator():
    for i in range(10):
        yield i ** 2
        yield "kapr"


def file_generator():
    file_names = ["kapr", "stika", "sumec", "okoun", "candat", "a"]
    file_ext = [".exe", ".py", ".pdf", ".csv", ".json", ".j", "csv.kapr"]
    # file_ext = ['.json', '.j', '.csv.kapr']
    for i in range(100):
        n = random.choice(file_names)
        e = random.choice(file_ext)
        yield f"{n}{e}"


def header(val):
    print()
    print("=" * 30)
    print(val)
    print("=" * 30)


if __name__ == "__main__":
    # 1B1A
    header("1B1A")
    int_filter = lambda x: type(x) is int
    pprint(list(filter(int_filter, val_generator())))

    # 1B1B
    header("1B1B")
    file_pattern = re.compile(r".*\.(json|csv)$")
    type_filter = lambda x: bool(file_pattern.search(x))
    pprint(list(filter(type_filter, file_generator())))

    # 1B1C
    # I would not use lambda for this.
    header("1B1C")

    def time_filter(val):
        try:
            return bool(datetime.strptime(val, "%Y-%m-%d"))
        except:
            return False

    l = [
        "1990-03-30",
        "1990-02-30",
        "1990-01-02",
        "1990-01-02:10:30",
        "-390-01-02",
        "kapr",
    ]
    print(list(filter(time_filter, l)))
