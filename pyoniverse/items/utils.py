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
