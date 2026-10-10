from config import DISCOUNT_PERCENT


def discounted_price(price):
    return price * (1 - DISCOUNT_PERCENT / 100)


if __name__ == "__main__":
    print(discounted_price(100))