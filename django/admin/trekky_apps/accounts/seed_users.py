import unicodedata

from faker import Faker


faker = Faker("vi_VN")
DEFAULT_SEED_PASSWORD = "Password@123"

EMAIL_PROVIDERS = (
    "gmail.com",
    "gmail.com",
    "gmail.com",
    "gmail.com",
    "outlook.com",
    "icloud.com",
    "yahoo.com",
)

FAMILY_NAMES = (
    "Nguyen",
    "Tran",
    "Le",
    "Pham",
    "Hoang",
    "Huynh",
    "Phan",
    "Vu",
    "Vo",
    "Dang",
    "Bui",
    "Do",
    "Ho",
    "Ngo",
    "Duong",
    "Ly",
)

MIDDLE_NAMES = (
    "Van",
    "Thi",
    "Gia",
    "Ngoc",
    "Minh",
    "Anh",
    "Thanh",
    "Quoc",
    "Duc",
    "Bao",
    "Thu",
    "Phuong",
    "Hoai",
    "Tien",
    "Khanh",
    "Hong",
    "Nhat",
    "The",
    "Trong",
    "Xuan",
)

GIVEN_NAMES = (
    "An",
    "Anh",
    "Bao",
    "Binh",
    "Chi",
    "Cuong",
    "Duy",
    "Giang",
    "Ha",
    "Hanh",
    "Hieu",
    "Hoa",
    "Hoang",
    "Huong",
    "Khanh",
    "Lan",
    "Linh",
    "Long",
    "Mai",
    "Minh",
    "Nam",
    "Ngoc",
    "Nhi",
    "Phuong",
    "Quang",
    "Quynh",
    "Son",
    "Tam",
    "Thao",
    "Thanh",
    "Thu",
    "Trang",
    "Truc",
    "Tuan",
    "Tung",
    "Vy",
)


def normalize_ascii(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    raw = raw.replace("Đ", "D").replace("đ", "d")
    normalized = unicodedata.normalize("NFD", raw)
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return without_marks.encode("ascii", "ignore").decode("ascii").lower().strip()


def tokenize_words(value: str) -> list[str]:
    normalized = normalize_ascii(value)
    cleaned = "".join(char if char.isalnum() or char in {" ", "-", "."} else " " for char in normalized)
    return [part for part in cleaned.replace("-", " ").replace(".", " ").split() if part]


def build_display_name() -> str:
    family = faker.random_element(FAMILY_NAMES)
    middle_parts = [faker.random_element(MIDDLE_NAMES)]
    if faker.boolean(chance_of_getting_true=30):
        extra_middle = faker.random_element([name for name in MIDDLE_NAMES if name not in middle_parts])
        middle_parts.append(extra_middle)
    given = faker.random_element(GIVEN_NAMES)
    middle_parts = [name for name in middle_parts if name != given]
    if not middle_parts:
        middle_parts = [faker.random_element([name for name in MIDDLE_NAMES if name != given])]
    return " ".join([family, *middle_parts, given])


def build_username(words: list[str], suffix: int) -> str:
    family = words[0] if words else "nguyen"
    middle_parts = words[1:-1] if len(words) > 2 else (words[1:2] if len(words) > 1 else [])
    middle = middle_parts[0] if middle_parts else ""
    joined_middle = "".join(middle_parts)
    given = words[-1] if words else "anh"
    middle_initial = middle[:1]
    birth_year = 1985 + (suffix % 18)
    year_suffix = f"{birth_year:04d}"[-2:]
    random_three = f"{100 + (suffix % 900):03d}"
    random_four = f"{1000 + (suffix % 9000):04d}"

    candidates = [
        f"{family}{given}",
        f"{given}{family}",
        f"{family}.{given}",
        f"{given}.{family}",
        f"{family}{middle_initial}{given}",
        f"{given}{middle_initial}{family}",
        f"{family}{joined_middle}{given}",
        f"{given}{joined_middle}{family}",
        f"{family}_{given}",
        f"{given}_{family}",
        f"{family}{given}{year_suffix}",
        f"{given}{family}{year_suffix}",
        f"{family}{given}{birth_year}",
        f"{given}{family}{birth_year}",
        f"{family}.{given}.{year_suffix}",
        f"{family}_{given}_{year_suffix}",
        f"{given}.{family}.{random_three}",
        f"{family}{given}{random_three}",
        f"{given}{family}{random_four}",
        f"{family}.{given}{year_suffix}",
    ]
    candidates = [candidate.strip("._") for candidate in candidates if len(candidate.strip("._")) >= 5]
    return faker.random_element(candidates or [f"user{suffix:04d}"])


def build_seed_user_draft(index: int) -> dict[str, str]:
    display_name = build_display_name()
    words = tokenize_words(display_name)
    username = build_username(words, index)
    email_provider = faker.random_element(EMAIL_PROVIDERS)
    email = f"{username}@{email_provider}"
    return {
        "display_name": display_name,
        "username": username,
        "email": email,
    }
