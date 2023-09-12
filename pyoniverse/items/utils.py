from datetime import datetime


def convert_currency(currency: str) -> int:
    """
    :param currency: KRW 등의 통화
    :return: 통화 ID
    """
    match currency:
        case "KRW":
            return 1
        case _:
            raise ValueError(f"Unknown currency: {currency!r}")


def get_timestamp() -> int:
    """
    :return: 현재 시간의 타임스탬프
    """
    return int(datetime.utcnow().timestamp())


def convert_event(event: str) -> int:
    """
    :param event: 1+1 등의 이벤트 이름
    :return: 이벤트 ID
    """
    event = event.upper().strip()
    match event:
        case "1+1":
            return 1
        case "2+1":
            return 2
        case "GIFT":
            return 3
        case "NEW":
            return 4
        case "MONOPOLY":
            return 5
        case "RESERVATION":
            # 예약이 필요한 상품
            return 6
        case "DISCOUNT":
            # 할인 이벤트
            return 7
        case _:
            raise ValueError(f"Unknown event: {event!r}")


def convert_brand(brand: str) -> int:
    brand = brand.upper().strip()
    match brand:
        case "GS25":
            return 1
        case "CU":
            return 2
        case "SEVEN ELEVEN":
            return 3
        case _:
            raise ValueError(f"Unknown brand: {brand!r}")


def convert_category(category: str) -> int:
    category = category.upper().strip()
    match category:
        case "DRINK":
            return 1
        case "ALCOHOL":
            return 2
        case "SNACK":
            return 3
        case "ICE CREAM":
            return 4
        case "CUP NOODLE":
            return 5
        case "LUNCH BOX":
            return 6
        case "SALAD":
            return 7
        case "KIMBAP":
            return 8
        case "SANDWICH":
            return 9
        case "BREAD":
            return 10
        case "FOOD":
            return 11
        case "HOUSEHOLD GOODS":
            return 12
        case _:
            raise ValueError(f"Unknown category: {category!r}")
