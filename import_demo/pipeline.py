from conversions import to_seconds


def report_duration(milliseconds):
    return to_seconds(milliseconds)


if __name__ == '__main__':
    print(report_duration(2500))
